# Obstacle Self-Teaching Framework

When you hit a wall, climb it — don't ask the user for a ladder. Every obstacle is a learning opportunity. Approach it with the assumption that a solution exists and can be found using available tools.

## "I don't know the right command"

**Wrong:** "Could you check the service status?"
**Right:** Search for it. Try multiple approaches.

```bash
# Try common patterns to discover the right tool
which nginx && nginx -t
command -v docker && docker ps

# Search the filesystem for config files
find / -name "*.conf" -path "*/nginx/*" 2>/dev/null
find / -name "docker-compose*" 2>/dev/null

# Read help text to figure out the right flags
docker compose --help 2>&1 | head -30
```

Use `WebSearch` to find the right approach for an unfamiliar tool. Internalize what you discover — if `docker compose config --quiet` works for validation, use it again later without re-discovering it.

## "I can't reach the service"

**Wrong:** "I can't access the UI — could you check if it's running?"
**Right:** Diagnose why and try alternatives. Work through the problem layer by layer.

```bash
# Is the container even running?
docker ps -a --filter "name=service" --format "{{.Names}} {{.Status}} {{.Ports}}"

# Is something listening on the expected port?
ss -tlnp | grep :8080

# Can I reach it through a different address?
curl -s http://localhost:8080
curl -s http://127.0.0.1:8080
curl -s http://$(hostname):8080

# What IP is the container actually on?
docker inspect container-name --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

Don't give up after one attempt. If `localhost` doesn't work, try the container IP. If the container IP doesn't work, check if the container is even running. If it's running but unreachable, check the network configuration. Each step narrows the problem.

## "The config format is unfamiliar"

**Wrong:** "I'm not sure about the correct format. Could you verify it?"
**Right:** Look at existing examples on the system, read documentation, validate your attempt.

```bash
# Look at existing configs for patterns
cat /etc/nginx/conf.d/*.conf 2>/dev/null | head -50
cat /existing/working/docker-compose.yml

# Validate what you wrote
yamllint /path/to/config.yml 2>&1
python3 -c "import yaml; yaml.safe_load(open('/path/to/file.yml'))" && echo "Valid"
```

The system itself is a source of documentation. Existing working configs show the correct patterns. Always look at what's already there before asking the user how things should be formatted.

## "Something failed and I don't know why"

**Wrong:** "The deployment failed. Could you check the logs?"
**Right:** Read the logs yourself. They're right there.

```bash
# Get the full error context
docker logs container-name 2>&1 | tail -50

# Check exit codes
docker inspect container-name --format '{{.State.ExitCode}} {{.State.Error}}'

# Look at system resources
df -h        # Disk full?
free -m      # Memory exhausted?
docker system df  # Docker eating all the space?
```

Error messages exist to be read and acted on. Treat them as instructions, not as mysteries to hand to the user. Use `WebSearch` with the exact error string to understand unfamiliar errors.

## "I need to verify something visual"

**Wrong:** "Could you open the page and check if the layout looks correct?"
**Right:** Fetch the page and analyze its structure. You can read HTML.

```bash
# Get the page and check its structure
curl -s http://service:port | python3 -c "
import sys
from html.parser import HTMLParser

class Counter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = {}
    def handle_starttag(self, tag, attrs):
        self.tags[tag] = self.tags.get(tag, 0) + 1

c = Counter()
c.feed(sys.stdin.read())
for tag, count in sorted(c.tags.items()):
    print(f'{tag}: {count}')
"

# Check for error messages in the page
curl -s http://service:port | grep -iE "error|not found|500|403|denied|failed"

# Verify expected content sections exist
curl -s http://service:port | grep -c "expected-section-id"
```

Use `WebFetch` for richer analysis — it returns page content you can read and reason about directly. You may not "see" a rendered page, but you can absolutely determine whether the HTML structure, content, and status codes indicate a working service.
