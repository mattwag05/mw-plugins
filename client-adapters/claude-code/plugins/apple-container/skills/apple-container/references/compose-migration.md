# Docker Compose → Apple container migration playbook

Apple Container has **no `docker compose`**. A Compose project becomes a **bring-up script** that
issues `container` commands. Most of the work is mechanical; the two real puzzles are **service
discovery** (Compose's automatic name DNS) and **lifecycle** (no `--restart`, no healthcheck-gated
`depends_on`). This playbook solves both, grounded in the upstream docs.

## Step 0: one-time: enable service discovery by name

Compose lets `web` reach `db` at the bare hostname `db`. Apple Container has an **embedded DNS
service**, but you must configure a domain. Pick a domain (e.g. `test`) once:

```bash
# Option A (host + container resolution, persists): config file
#   ~/.config/container/config.toml
[dns]
domain = "test"

# Option B (also lets the *host* resolve names; writes /etc/resolver, needs sudo):
sudo container system dns create test
```

With a domain set, a container started with `--name db` is resolvable at **`db.test`**, from the host
*and from other containers*. To let apps keep using the **bare** Compose hostname (`db`, not
`db.test`), add **`--dns-search test`** to each `container run` so the app's lookup of `db` resolves
to `db.test`. (Networks + name DNS require **macOS 26**; see the gaps section.)

## Field-by-field mapping (compose key → container)

| Compose | Apple Container |
|---------|-----------------|
| `services.<name>.image: X` | `container run -d --name <name> … X` |
| `build: .` / `build.context` | `container build -t <name> .` then `container run … <name>` |
| `command: …` | trailing args after the image |
| `entrypoint: …` | `--entrypoint …` |
| `ports: ["8080:80"]` | `-p 8080:80` (`[host-ip:]host:container[/proto]`) |
| `environment:` / `env_file:` | `-e KEY=val` (repeatable) / `--env-file <file>` |
| `volumes: [pgdata:/data]` (named) | `container volume create pgdata` once, then `-v pgdata:/data` |
| `volumes: [./src:/app]` (bind) | `-v "$PWD/src:/app"` |
| `networks:` | `container network create <net>` (macOS 26), then `--network <net>` |
| service-name DNS (`db`) | `--name db` + a `[dns] domain` + `--dns-search <domain>` (Step 0) |
| `depends_on:` | **manual**: order the commands + poll readiness (see worked example) |
| `healthcheck:` | **no built-in**: poll with `container exec … <check>` in the script |
| `restart: unless-stopped` | **no equivalent**: wrap the script in a launchd agent (see gaps) |
| `deploy.resources.limits` | `--cpus N` / `--memory 1G` |
| `cap_add` / `cap_drop` | `--cap-add` / `--cap-drop` |
| `read_only: true` | `--read-only` |
| `tmpfs:` | `--tmpfs <path>` |
| `platform: linux/amd64` | `--arch amd64` (runs under Rosetta) |

## Worked example

This Compose file:

```yaml
services:
  db:
    image: postgres:16
    environment: { POSTGRES_PASSWORD: secret }
    volumes: [pgdata:/var/lib/postgresql/data]
  redis:
    image: redis:7
  web:
    build: .
    ports: ["8080:8000"]
    environment:
      DATABASE_URL: postgres://postgres:secret@db:5432/app
      REDIS_URL: redis://redis:6379
    depends_on: [db, redis]
volumes:
  pgdata:
```

becomes `up.sh` (note `--dns-search app-net` so the app's unchanged `db`/`redis` hostnames resolve):

```bash
#!/usr/bin/env bash
set -euo pipefail
NET=app DOMAIN=test          # domain must be configured per Step 0

container network create "$NET" 2>/dev/null || true     # macOS 26+; idempotent
container volume create pgdata 2>/dev/null || true

# stateless deps first
container run -d --name db    --network "$NET" --dns-search "$DOMAIN" \
  -e POSTGRES_PASSWORD=secret -v pgdata:/var/lib/postgresql/data postgres:16
container run -d --name redis --network "$NET" --dns-search "$DOMAIN" redis:7

# depends_on → poll readiness (Compose's `condition: service_healthy`)
echo "waiting for db…"
until container exec db pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done

# build + run the app (db/redis reachable by bare name via --dns-search)
container build -t web:latest .
container run -d --name web --network "$NET" --dns-search "$DOMAIN" -p 8080:8000 \
  -e DATABASE_URL='postgres://postgres:secret@db:5432/app' \
  -e REDIS_URL='redis://redis:6379' web:latest

echo "up → http://localhost:8080"
```

and `down.sh`:

```bash
#!/usr/bin/env bash
container stop web db redis 2>/dev/null || true
container rm   web db redis 2>/dev/null || true
# container network delete "$NET"   # optional (only when nothing is attached)
# container volume rm pgdata        # ⚠ DESTROYS the database — omit to persist
```

`# ponytail:` a hand-rolled `up.sh`/`down.sh` pair is the right altitude for a handful of services.
Don't reach for a YAML-parsing "compose clone" unless you're migrating many projects.

## Gaps & caveats (plan for these)

1. **No restart policy.** `container run` has no `--restart`. A crashed container stays down. For
   "always up" semantics, register the bring-up script as a **launchd** agent (`~/Library/LaunchAgents`,
   `RunAtLoad` + `KeepAlive`), or run a tiny supervisor loop: the container itself won't self-restart.
2. **`depends_on` is ordering only.** Even in Compose, `depends_on` doesn't wait for *readiness* unless
   you add `condition: service_healthy`. Here you replace that with an explicit poll
   (`until container exec … ; do sleep 1; done`). Don't assume a started container is ready.
3. **macOS 26 required for networks + name DNS.** On macOS 15 there's only the single isolated
   `default` network, `container network create`/`--network` error out, and containers can't reach each
   other: a multi-service Compose app effectively can't be reproduced. Treat macOS 26 as a hard
   prerequisite for any Compose migration.
4. **Host-service access** (Compose's `host.docker.internal`): use
   `sudo container system dns create host.container.internal --localhost <ipv4>`, but note it
   **disables iCloud Private Relay** and the packet-filter rule is **removed on restart** (re-create
   after reboot).
5. **Anonymous volumes aren't auto-removed** by `--rm`: name every volume you care about and clean up
   explicitly (`container volume prune` for the rest).
6. **No `.env` interpolation in a compose file**: there's no compose file. Put variables in your shell
   script or an `--env-file` per service.

## Quick migration checklist

- [ ] On macOS 26 + Apple silicon, `container system start` is running.
- [ ] DNS domain configured (Step 0) and `--dns-search <domain>` on each `run` if apps use bare names.
- [ ] Each `services:` entry → one `container run -d --name <svc> --network <net>`.
- [ ] Named volumes pre-created; bind mounts use absolute host paths.
- [ ] `depends_on` replaced with readiness polls; `restart:` replaced with a launchd agent if needed.
- [ ] `build:` services → `container build -t <svc> .` before their `run`.
- [ ] Tear-down script stops+removes in reverse, preserving data volumes.
