# Verification Patterns

Concrete commands and patterns for autonomously verifying work across common task categories. Use these instead of asking the user to check results.

## Web UI and Service Health

```bash
# Fetch a page and inspect its HTML — this IS "looking at the UI"
curl -s http://service:port | head -100

# Check for specific UI elements that indicate the service is working
curl -s http://service:port | grep -i "dashboard\|login\|welcome\|ready"

# Verify a specific page or route exists
curl -s -o /dev/null -w "%{http_code}" http://service:port/admin

# Check what the page title says
curl -s http://service:port | grep -oP '<title>\K[^<]+'

# Check HTTP response code AND body
curl -sS http://service:port -w "\nHTTP_CODE: %{http_code}\n"

# Hit health/status endpoints
curl -s http://service:port/health
curl -s http://service:port/api/status
curl -s http://service:port/api/v1/system/info

# Check if the service returns valid JSON
curl -s http://service:port/api/endpoint | python3 -m json.tool

# Follow redirects to see where the service actually sends you
curl -sL -o /dev/null -w "%{url_effective} (HTTP %{http_code})" http://service:port
```

Or use `WebFetch` to retrieve full page content and read it directly.

## Log Reading

```bash
# Docker container logs
docker logs container-name --tail 100 2>&1

# Filter for errors and warnings
docker logs container-name 2>&1 | grep -iE "error|warn|fatal|fail|exception" | tail -20

# System service logs
journalctl -u service-name --no-pager -n 50

# Application log files
tail -50 /path/to/app/logs/error.log
```

## Docker and Containers

```bash
# Validate compose config BEFORE applying
docker compose -f /path/to/docker-compose.yml config --quiet && echo "Config valid" || echo "Config invalid"

# Verify containers are actually running
docker compose -f /path/to/docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Wait for service readiness instead of asking the user to check
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code}" http://localhost:port | grep -q "200" && echo "Service ready" && break
  echo "Waiting... ($i/15)"
  sleep 2
done

# Verify volume/mount data is accessible
docker exec container-name ls -la /expected/mount/path

# Verify container connectivity
docker exec container-name ping -c 1 other-container 2>&1
docker exec container-name wget -q -O- http://other-container:port 2>&1 | head -5
```

## Network and DNS

```bash
# After DNS changes
dig +short hostname.example.com
nslookup hostname.example.com

# After reverse proxy changes
curl -s -H "Host: subdomain.domain.com" http://proxy-ip:port -w "\nHTTP: %{http_code}\n"

# After TLS/certificate changes
curl -vI https://service-url 2>&1 | grep -E "subject|expire|issuer|SSL"

# After Tailscale changes
tailscale status 2>/dev/null
tailscale ping hostname 2>/dev/null
```

## Code and Scripts

```bash
# Validate syntax before presenting
python3 -c "import py_compile; py_compile.compile('/path/to/script.py', doraise=True)" 2>&1
bash -n /path/to/script.sh 2>&1
node --check /path/to/script.js 2>&1

# Run it and check the output
python3 /path/to/script.py 2>&1 | tail -30

# For scripts that modify files, verify the files changed correctly
md5sum /path/to/file  # before
# ... run script ...
md5sum /path/to/file  # after — did it change?
```

## Configuration Files

```bash
# YAML
python3 -c "import yaml; yaml.safe_load(open('/path/to/file.yml'))" && echo "Valid YAML"

# JSON
python3 -c "import json; json.load(open('/path/to/file.json'))" && echo "Valid JSON"

# TOML
python3 -c "import tomllib; tomllib.load(open('/path/to/file.toml', 'rb'))" && echo "Valid TOML"

# Nginx
nginx -t 2>&1

# Docker Compose
docker compose config --quiet 2>&1

# Show what changed
diff /path/to/original /path/to/modified
```
