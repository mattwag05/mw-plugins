# Pippin Claude Code Plugin

This plugin teaches Claude Code how to use the `pippin` CLI for Apple app automation.

## What it provides

- `pippin-cli` skill: triggered when the user asks about mail, calendar, reminders, notes, contacts, voice memos, audio, or browser automation
- Complete command reference across all 8 command groups
- Output format guide (text / json / agent)
- Multi-step workflow patterns for common automation tasks

## Requirements

- `pippin` v0.11.0 installed at `/opt/homebrew/bin/pippin`
- macOS 15+ with appropriate TCC permissions (run `pippin doctor`)
- Mail.app open for mail commands
- mlx-audio installed for audio commands (`pip install mlx-audio`)

## Source

Plugin source: `~/Projects/pippin` (v0.11.0)
