# Docker → Apple Container: full mapping & command catalog

Grounded in `apple/container` docs (`command-reference.md`, `how-to.md`, `technical-overview.md`).
For deep prose, the full source docs are in the CCL at `contexts/technical/apple-container/`.

## Command mapping (Docker ⇒ container)

| Docker | Apple Container | Notes |
|--------|-----------------|-------|
| `dockerd` / Docker Desktop | `container system start` / `stop` | launchd-managed `container-apiserver`, not a daemon you babysit |
| `docker info` / `docker version` | `container system status` / `container system version` | |
| `docker run` | `container run` | flags largely identical (see below) |
| `docker create` | `container create` | same flags as run, leaves it stopped |
| `docker start/stop/kill` | `container start` / `stop` / `kill` | `stop --all`, `--signal`, `--time` |
| `docker rm` | `container delete` (alias `rm`) | `--force` for running, `--all` |
| `docker ps` / `docker ps -a` | `container ls` / `container ls --all` | `--format json\|table\|yaml\|toml` |
| `docker exec` | `container exec` | same process flags |
| `docker logs` | `container logs` | plus `--boot` for the VM boot log |
| `docker inspect` | `container inspect` | JSON |
| `docker stats` | `container stats` | `--no-stream` for one snapshot |
| `docker cp` | `container cp` (alias `copy`) | container ref form `id:/path` |
| `docker export` | `container export` | container must be stopped |
| `docker build` | `container build` | reads `Dockerfile` **or** `Containerfile`; BuildKit |
| `docker images` | `container image ls` | `-v/--verbose` |
| `docker pull` / `push` | `container image pull` / `push` | default registry `docker.io` |
| `docker tag` | `container image tag` | |
| `docker save` / `load` | `container image save` / `load` | tar archive ↔ images |
| `docker rmi` | `container image delete` (alias `rm`) | `--all`, `--force` |
| `docker image prune` | `container image prune` | `--all` for unreferenced, not just dangling |
| `docker volume create/ls/rm/prune/inspect` | `container volume create/ls/rm/prune/inspect` | ⚠ anon volumes not auto-removed by `--rm` |
| `docker network create/ls/rm/prune/inspect` | `container network create/ls/rm/prune/inspect` | **macOS 26 only** |
| `docker login` / `logout` | `container registry login` / `logout` | creds in macOS **Keychain**; `--password-stdin` |
| `docker system df` | `container system df` | |
| `docker system prune` | **no single command** | run `container prune` + `image prune` + `volume prune` |
| `docker compose` | **none** | wire by hand / `container network` / external orchestrator |
| `docker buildx` (multi-arch) | `container build --arch arm64 --arch amd64` | x86 runs under **Rosetta** |
| `docker context` / VM mgmt | `container machine` (alias `m`) | explicit guest VM; not used for normal runs |

## `container run` / `create` flag groups (from command-reference)

- **Process:** `-e/--env`, `--env-file`, `--gid`, `-i/--interactive`, `-t/--tty`, `-u/--user`,
  `--uid`, `--ulimit`, `-w/--workdir/--cwd`
- **Resource:** `-c/--cpus`, `-m/--memory` (K/M/G/T/P suffix)
- **Management:** `-a/--arch` (default arm64), `--cap-add/--cap-drop`, `--cidfile`, `-d/--detach`,
  `--dns*`, `--entrypoint`, `--init`, `--init-image`, `-k/--kernel`, `-l/--label`, `--mount`
  (`type=,source=,target=,readonly`), `--name`, `--network` (`name[,mac=…][,mtu=…]`), `--no-dns`,
  `--os` (default linux), `-p/--publish` (`[host-ip:]host:container[/proto]`), `--platform`,
  `--publish-socket`, `--read-only`, `--rm`, `--rosetta`, `--runtime`, `--ssh`, `--shm-size`,
  `--tmpfs`, `-v/--volume`, `--virtualization`
- **Registry:** `--scheme http|https|auto` (auto ⇒ HTTP for loopback/RFC1918/local domain, else HTTPS)

## `container build` options

`-a/--arch` (repeatable), `--build-arg`, `-c/--cpus` (default 2), `--dns*`, `-f/--file`,
`-l/--label`, `-m/--memory` (default 2048MB), `--no-cache`, `-o/--output type=oci|tar|local[,dest=]`,
`--os`, `--platform`, `--progress`, `--pull`, `-q/--quiet`, `--secret id=…`, `-t/--tag` (repeatable),
`--target <stage>`, `--vsock-port`. The builder is a BuildKit container managed via
`container builder start|status|stop|delete`.

## Full command surface (groups)

- **Core:** `run`, `build`
- **Container mgmt:** `create`, `start`, `stop`, `kill`, `delete(rm)`, `ls`, `exec`, `export`,
  `logs`, `inspect`, `stats`, `cp`, `prune`
- **Image mgmt:** `image ls`, `pull`, `push`, `save`, `load`, `tag`, `delete(rm)`, `prune`, `inspect`
- **Builder:** `builder start`, `status`, `stop`, `delete(rm)`
- **Network (macOS 26+):** `network create`, `delete(rm)`, `prune`, `ls`, `inspect`
- **Volume:** `volume create` (`--opt journal=ordered|writeback|journal[:size]`, `-s/--size`),
  `delete(rm)`, `prune`, `ls`, `inspect`
- **Registry:** `registry login`, `logout`, `list`
- **Machine (guest VM, alias `m`):** `machine create`, `run`, `ls`, `inspect`, `set`, `set-default`,
  `logs`, `stop`, `delete(rm)`
- **System (macOS host only):** `system start`, `stop`, `status`, `version`, `logs`, `df`,
  `dns create|delete|ls` (needs sudo), `kernel set` (`--recommended` to fetch the default),
  `property ls`

## Behavioral differences that bite (complete list)

1. **No daemon to manage; no `docker compose`.** (Biggest migration gaps.)
2. **Anonymous volumes** (`-v /path` or `--mount type=volume,dst=/path` with no source) get UUID names
   (`anon-…`) and are **not** removed by `--rm` — clean up manually.
3. **Rosetta** translates x86_64 (`--arch amd64` / `--rosetta`); the builder VM uses Rosetta by default
   (toggle via the `rosetta` system property).
4. **Partial memory ballooning:** freed guest memory isn't returned to macOS; restart long-running
   memory-heavy containers periodically.
5. **macOS 15 limits:** no `container network`, single isolated default net, containers can't talk to
   each other, possible network-init race (see troubleshooting in the CCL).
6. **Default registry `docker.io`;** image refs without a host resolve to `docker.io/library/<name>`.
   Registry credentials are stored in the **Keychain**.
7. **`--scheme auto`** uses HTTP for loopback/RFC1918/the local container DNS domain, HTTPS otherwise.
8. **`container machine`** is an explicit guest VM (alias `m`) — separate concept from running a
   container; most workflows never touch it.

## Setup, upgrade, uninstall

```bash
container system start                       # bring services up (installs default kernel first run)
/usr/local/bin/update-container.sh           # upgrade to latest
/usr/local/bin/update-container.sh -v 0.3.0  # install a specific version (downgrade)
/usr/local/bin/uninstall-container.sh -k     # uninstall, KEEP user data
/usr/local/bin/uninstall-container.sh -d     # uninstall, DELETE user data
container system stop                        # always stop before upgrade/downgrade
```

Requirements: **Apple silicon + macOS 26** (runs on 15 with the limits above). Pre-1.0: pin to a
release tag; minor versions may break.
