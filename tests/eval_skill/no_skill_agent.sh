#!/bin/sh
# Control agent: real pi with NO skill loaded. Args: <skill-dir> <task-file> (skill ignored).
exec pi -p --no-session --no-skills --no-context-files --no-extensions --no-mcp --no-prompt-templates --offline -- "$(cat "$2")"
