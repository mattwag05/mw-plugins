---
name: ops-change
description: Change a live system or service safely: owning record, backup you have proven, approval, reversible experiments, and acceptance by real behavior. Use for any config, restart, upgrade, or state change on a running service or host.
---

# Ops change

A live system is one other people or services depend on right now. The host overlay names your registry, backup locations and alert channel.

## Steps

1. Find the owner. Read the record that owns this service (registry, runbook, or the repo's ops doc). It beats any copied list, old report, or memory. If two sources disagree, check the live system and say which you trusted.
2. Baseline. Run the service's real acceptance check first (below) and keep its output. Capture the current value of what you will change, verbatim.
3. Approval. Each live write needs the human's own words naming it. If the task already names this change, that is approval for that change only. Anything extra you discover (another setting, a restart, a cleanup) needs a new ask.
4. Backup before changing, in the way that fits the data:
   - Config file: `cp -p service.conf service.conf.bak.$(date +%Y%m%d%H%M%S)` next to the original, then `cmp service.conf service.conf.bak.*` to confirm it is byte-identical.
   - Database or running state: use its own dump or snapshot tool. A raw copy of a running database is not a backup.
   - Prove you can restore: restore the backup to a scratch path and read it back. An unproven backup is not a backup.
5. Change the smallest thing that does the job. If several changes need restarts, batch them into one restart.
6. Reversible experiment (try something, then undo). Capture, then change and test inside a subshell that restores on exit, then re-read:
   ```
   orig=$(mktemp); cp -p service.conf "$orig"
   ( trap 'cp -p "$orig" service.conf' EXIT
     # make the temporary change, run the acceptance check
   )
   cmp -s "$orig" service.conf && echo "RESTORED: identical"
   ```
   Quote the `RESTORED` line in your reply. If the check cannot run, the experiment is not finished.
7. Accept by behavior. "Running", "healthy", HTTP 200, or a fresh timestamp is not acceptance. Run the check that makes the service do its job (a real request, a real restore, a real login) and paste its output in your final reply. A failing or unavailable check is incomplete, not an all-clear.
8. State that holds identity (node keys, certificates, databases, enrollment tokens): never clear or recreate it to fix a fault. Restore it from its backup into its original place.
9. Alerts: test an alert path by sending a real message to a test channel and confirming delivery. Never test on the channel that pages people, and never trust an exit code alone.
10. Report: what changed, backup path, the acceptance output, the rollback command, and anything unverified.

## Done when

- A backup of the original exists next to it and is byte-identical to what was there before.
- The requested change is applied and nothing else changed.
- The acceptance check's real output is quoted in your reply.
- For an experiment, the original is restored and the `RESTORED: identical` re-read is quoted.
- No secret was printed, and nothing was pushed or deployed beyond what was approved.
