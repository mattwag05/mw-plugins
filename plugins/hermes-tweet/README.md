# Hermes Tweet

Hermes Tweet is a native Hermes Agent plugin for X/Twitter research, public reads, and explicitly approved account actions through Xquik.

## Install in Hermes Agent

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
```

Hermes prompts for `XQUIK_API_KEY` during interactive install. In non-interactive setups, set it in the Hermes runtime environment or `~/.hermes/.env`.

Keep account-changing actions disabled unless the session intentionally needs them:

```bash
HERMES_TWEET_ENABLE_ACTIONS=false
```

## What This Marketplace Entry Provides

This entry gives agents a portable skill card for when to use Hermes Tweet and how to keep usage safe:

- Start with `tweet_explore` for endpoint or capability discovery.
- Use `tweet_read` for public read-only routes after an endpoint is known.
- Use `tweet_action` only for writes or private-account operations after the user approves the exact action.
- Never ask for, print, or pass API keys in chat or tool arguments.

See the upstream plugin for runtime code, commands, and full validation:

https://github.com/Xquik-dev/hermes-tweet
