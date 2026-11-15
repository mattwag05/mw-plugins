- mattpocock/skills @ 5863806, skills/engineering/research/SKILL.md, MIT: the primary-sources-first rule and the write-findings-to-a-Markdown-file-with-cited-claims job.
- Hermes `research` umbrella and `grounded-citations` skills (~/.hermes/skills/research, MIT, read 2026-11-15): save fetched text and quote only from those bytes, follow a summary page to the full text it summarizes, and record the exact searches run so a later session can retry them. The tool workflows (YouTube transcripts, video frames, Whisper, CME quizzes, shopping, the citation ledger script) stay in Hermes.

Adapted for small models: dropped the background-agent step (no subagents on the floor model); added a fixed file path and template (question, answer, evidence, inference, conflicts, open questions); added rules to separate source text from inference, to record gaps, and to work from local files when no web tool exists; defined "primary source" inline; added a Done when list.

Eval `not-found` now also checks that Open questions lists the commands or searches that were run.
