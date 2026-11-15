---
name: research
description: "Answer a question from primary sources and write the findings to a file with citations. Use when asked to look something up, check what docs or a spec say, or gather facts before deciding."
---

# Research

Primary source means the thing's owner: official docs, a spec, the source code, release notes, a first-party API response. A blog or forum post is secondary.

## Steps

1. Restate the question in one sentence. Pick a short kebab-case slug for it (for example `cache-ttl-default`).
2. List where sources live. Check local first: `ls -R sources docs` and `grep -ril "<keyword>" .` for files in the project. Use the web only if you have a web tool and the local files do not answer the question. With no web tool, work from local files and say so.
3. Rank what you found. Read primary sources first. Read secondary sources only to find leads, and follow each lead back to the primary source that owns the claim. If a page reads like a summary, find the full text it summarizes.
4. Read the passages that bear on the question. Save each fetched web page as text under `research/sources/` and copy quotes from those saved bytes. Copy exact values (numbers, names, versions) as written. Note the file path or URL and the section heading or line number for each.
5. If a secondary source contradicts a primary one, trust the primary and record the conflict.
6. Write `research/<slug>.md` (create `research/` if missing) using the template below.
7. Run `cat research/<slug>.md` and check that each Evidence line has a source and a location.

## Template

```
# <question>

## Answer
<One to three sentences. State the value. If it is not found, write "Not found in the sources checked.">

## Evidence
1. <claim> | source: <URL or file path>, <section or line> | type: primary or secondary | says: "<short quote or value>"

## Inference
<What you concluded beyond what a source says. Mark each item "inference". Write "none" if none.>

## Conflicts
<Sources that disagree, and which you trusted and why. "none" if none.>

## Open questions
<What you looked for and could not find, where you looked, and the exact searches or commands you ran (so they can be rerun).>
```

## Rules

- Every claim in Answer has a line in Evidence. No source, no claim.
- Keep "the source says" separate from "I infer". Never put an inference in Evidence.
- Never invent a value to fill a gap. If no source states it, say not found and list where you looked.
- A value from a secondary source alone is marked secondary and unconfirmed.

## Done when

- `research/<slug>.md` exists with the five headings: Answer, Evidence, Inference, Conflicts, Open questions.
- Every Evidence line names a file path or URL plus a location.
- The Answer matches the primary source, or says not found.
- Every gap appears under Open questions, with the exact searches or commands you ran.
- You told the user the file path.
