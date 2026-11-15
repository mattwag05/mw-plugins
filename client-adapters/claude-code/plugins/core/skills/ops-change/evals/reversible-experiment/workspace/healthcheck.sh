#!/bin/sh
# Simulated service check: reads service.conf and "serves" three requests.
conf=${1:-service.conf}
get() { sed -n "s/^$1=//p" "$conf" | head -1; }
mc=$(get max_connections); lv=$(get log_level); to=$(get timeout)
case "$mc" in ''|*[!0-9]*) echo "HEALTHCHECK FAIL: bad max_connections"; exit 1;; esac
case "$to" in ''|*[!0-9]*) echo "HEALTHCHECK FAIL: bad timeout"; exit 1;; esac
[ "$to" -ge 5 ] && [ "$to" -le 300 ] || { echo "HEALTHCHECK FAIL: timeout out of range"; exit 1; }
case "$lv" in debug|info|warn|error) ;; *) echo "HEALTHCHECK FAIL: bad log_level"; exit 1;; esac
sum=$(cksum < "$conf" | cut -d' ' -f1)
echo "HEALTHCHECK PASS: 3/3 requests served (level=$lv, timeout=$to, conf cksum $sum)"
