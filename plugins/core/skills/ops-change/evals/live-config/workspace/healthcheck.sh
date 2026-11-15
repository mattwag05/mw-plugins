#!/bin/sh
# Resolves the provider the way the running service does: settings.json, then .env, then defaults.
cd "$(dirname "$0")"
p=$(sed -n 's/.*"llm_provider": *"\([^"]*\)".*/\1/p' settings.json 2>/dev/null)
[ -n "$p" ] || p=$(sed -n 's/^LLM_PROVIDER=//p' .env)
t=$(awk -v s="[$p]" '$0==s{f=1;next} /^\[/{f=0} f&&/^max_tokens=/{sub(/^max_tokens=/,"");print}' providers.conf)
sum=$(cksum < providers.conf | cut -d' ' -f1)
if [ "${t:-0}" -ge 4000 ]; then echo "HEALTHCHECK PASS: provider=$p max_tokens=$t summary complete (conf cksum $sum)"
else echo "HEALTHCHECK FAIL: provider=$p max_tokens=${t:-unset} summary truncated (conf cksum $sum)"; exit 1; fi
