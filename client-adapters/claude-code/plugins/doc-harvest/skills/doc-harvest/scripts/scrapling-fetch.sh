#!/usr/bin/env bash
# doc-harvest: fetch a URL as clean Markdown via Scrapling in Apple Container.
#
# Prints clean Markdown to STDOUT. Progress + Scrapling logs go to STDERR, so
# this pipes straight into the clean step:
#   scrapling-fetch.sh <url> | python3 harvest.py clean --base-url <domain>
#
# Usage: scrapling-fetch.sh <url> [auto|get|fetch|stealthy]
#   auto (default) : static GET first; if the result looks SPA-thin, escalate
#                    to a JS-rendering browser fetch. Handles 95% of sites.
#   get            : static httpx fetch (fast), impersonating Chrome
#   fetch          : DynamicFetcher — renders JavaScript (SPA sites: Apple, Google AI)
#   stealthy       : StealthyFetcher — Cloudflare / anti-bot sites
#
# Every mode passes --ai-targeted (Scrapling's DOM-level main-content extraction +
# hidden-element sanitization), so the output is already nav/footer/boilerplate-free.
#
# Env:
#   CONTAINER_RUNTIME    compatible container runtime CLI (default: container).
#                        Run `container system start` before using the default.
#   SCRAPLING_IMAGE      container image (default: digest-pinned pyd4vinci/scrapling).
#                        Re-pin after `container image pull pyd4vinci/scrapling:latest`
#                        and inspect it with `container image inspect`.
#   SCRAPLING_MIN_BYTES  auto-escalation threshold (default: 200)
#   SCRAPLING_HTML       if set to a path, also save the raw rendered HTML there
#                        (for link discovery on SPA sites — see harvest.py discover --html)
set -euo pipefail

URL="${1:?usage: scrapling-fetch.sh <url> [auto|get|fetch|stealthy]}"
MODE="${2:-auto}"
RUNTIME="${CONTAINER_RUNTIME:-container}"
IMAGE="${SCRAPLING_IMAGE:-pyd4vinci/scrapling@sha256:2a0c05bdd78211a76cb7ab9565a91250787a326f9ca73c97cf764ccb536631a2}"
MIN_BYTES="${SCRAPLING_MIN_BYTES:-200}"

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/scrapling-fetch.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT

# _run <subcommand> [extra args...] — fetch into STAGE/page.md; logs to stderr.
_run() {
  local sub="$1"; shift
  "$RUNTIME" run --rm -v "$STAGE:/out" "$IMAGE" \
    extract "$sub" "$URL" /out/page.md --ai-targeted "$@" >&2 || return 1
}
_bytes() { [ -s "$STAGE/page.md" ] && wc -c < "$STAGE/page.md" | tr -d ' ' || echo 0; }

case "$MODE" in
  get)      _run get --impersonate chrome || true ;;
  fetch)    _run fetch --network-idle || true ;;
  stealthy) _run stealthy-fetch || true ;;
  auto)
    _run get --impersonate chrome || true
    # ponytail: byte-count heuristic for "this was a JS shell" — cheap and good
    # enough; a site that renders <200B of real static content is vanishingly
    # rare. Tune via SCRAPLING_MIN_BYTES if a real page trips it.
    if [ "$(_bytes)" -lt "$MIN_BYTES" ]; then
      printf 'scrapling-fetch: static result thin (%sB) — escalating to JS browser fetch\n' "$(_bytes)" >&2
      _run fetch --network-idle || true
    fi
    ;;
  *) printf 'scrapling-fetch: unknown mode %q (use auto|get|fetch|stealthy)\n' "$MODE" >&2; exit 2 ;;
esac

if [ "$(_bytes)" -lt 1 ]; then
  printf 'scrapling-fetch: FAILED — 0 bytes for %s\n' "$URL" >&2
  exit 1
fi

# Optionally also render raw HTML for link discovery (SPA discover fallback).
if [ -n "${SCRAPLING_HTML:-}" ]; then
  HTML_DIR="$(cd "$(dirname "$SCRAPLING_HTML")" && pwd)"
  "$RUNTIME" run --rm -v "$HTML_DIR:/htmlout" "$IMAGE" \
    extract fetch "$URL" "/htmlout/$(basename "$SCRAPLING_HTML")" --network-idle >&2 || true
fi

cat "$STAGE/page.md"
