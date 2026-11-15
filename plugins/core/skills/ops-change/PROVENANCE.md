# Provenance

- Private homelab operations policy (author's own document, not published): only generic rules were taken: the owning record beats copied lists, evidence over "it's running", source-specific backup and proven restore before change, capture then `trap restore EXIT` and re-read for reversible experiments, acceptance by real behavior, batch restarts, never clear identity-bearing state (restore it), test alerts on a test channel, named approval for each live write. All hostnames and infrastructure specifics were left out.
- Authority and reversible-experiment rules also appear in core/AGENTS.md.

Adapted for small models: the restore pattern is a runnable subshell snippet that prints a fixed `RESTORED: identical` line; backup is a named command with a `cmp` check; acceptance output must be quoted in the final reply.
