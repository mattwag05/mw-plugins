---
name: ambition
description: >-
  Rework a task or prompt into a more ambitious version along three axes. Altitude owns the
  outcome instead of the task, depth does the work the way the field's best practitioner would,
  and range borrows methods from other fields. Use when the user says "be more ambitious,"
  "aim higher," "what's the ambitious version," "go deeper," "how would an expert do this,"
  "make this prompt better," or asks what a task could become beyond the literal request.
  Invoke with /ambition, optionally followed by the task or prompt to upgrade.
metadata:
  version: "0.1.0"
---

# Ambition

Most requests reach the model as the user's best guess at a means to some end. This skill finds the end and asks for more of it. It works in three directions. Pick the ones that fit, since you rarely need all three.

This skill skips speed, meaning the same work done faster. That needs no change in approach.

## Before you start

Find out what the task is for. Restate it in one line, then answer one question. What does the user want to happen after this is done? If context doesn't tell you, ask the user that question and stop.

Every axis assumes you have a computer where you can install software, plus access to the relevant data through connectors or files. If you lack either, say what is missing up front. It bounds how far the upgrade can go.

Ambition changes scope. Present the upgraded plan and get a yes before you act on it, especially when it reaches outside the current workspace. A bigger goal never widens your authorization. Access, deploys, messages, and spending still need their own approval.

## Altitude

Move up from the task to the result it serves. "Fix this crash" becomes "keep the app crash-free." "Update the quarterly deck" becomes "help leadership catch problems early and move money and people to the right places."

Climb in steps. Each step should leave the user with something usable.

1. Explain. Read all the raw material you can get, beyond the fields the template asks for, and say what changed, why, and what to do about it.
2. Decide. Name the few decisions that matter most right now and draft options, each with its case for and against.
3. Redesign. Question whether the current format is the best way to reach the outcome. Propose a better one, test it against the user's own history to show it would have caught things sooner, and run it beside the old process before replacing it.

Altitude fits when there is a real end outcome. A good sign is work that would otherwise need recurring meetings. It fits poorly for creative work where the artifact is the point. It also has a ceiling. "Go make the business money" is still too high for a model to run alone, so pick the highest outcome you can actually measure and verify.

A high-altitude goal only holds up if you can work without a human feeding you tasks. List what you would need to do it alone: data feeds you can fetch, a map from release to commit, machines to reproduce and verify on, connectors to the right systems. Tell the user which of these exist and which they would have to set up. That setup is often the most valuable part of the answer.

## Depth

Do the task the way a top practitioner would, and keep going until that practitioner might learn something from the result.

- Use their instruments. Sounding like a statistician is different from fitting a model. If you catch yourself building a markdown table where an expert would load a database or run a regression, switch tools. Install what you need. The user doesn't have to know which instruments experts use, but you should name them.
- Start from raw material. Go to logs, source data, and primary records. Skip the summaries someone already digested.
- Set an unreasonable target and treat it as reachable. If the user would settle for 5 seconds, aim for 200 ms. Make the target a number. Goal-setting research finds that specific hard goals beat "do your best." When a goal looks impossible, assume it is solvable and keep working before you report a wall.
- Test what everyone believes. Take the user's stated assumption, such as "churn is an onboarding problem," and try to reproduce it from the raw data. Report where it fails.
- Find something new. Once you are deep in the data, look for what nobody knows yet. Build a model that reproduces past behavior, find a signal that is on nobody's dashboard, and show it predicts on data it has not seen.
- Get an outside judge. Never grade your own work. Find a check that depends on neither you nor the user, like a test suite, a benchmark, a held-out dataset, a profiler, a compiler, or another system's output. Prefer one you can run yourself, because fast feedback lets you iterate.

To deepen a prompt instead of executing it, answer four questions first:

1. What would a top professional do here that the prompt does not ask for?
2. What is the rawest material they would start from?
3. Which specific methods and tools would they use?
4. What, other than the model or the user, would show the result is right?

Then rewrite the prompt to ask for exactly that. Keep the rewrite close to the original's size. Depth comes from better methods and sources, and a longer prompt adds none of either.

## Range

Look at the work through fields it does not obviously need.

- Swap nouns for verbs. Instead of "a deck," call a quarterly review "getting busy people to believe a cause-and-effect story and decide under uncertainty in 30 minutes." The verb version shows which fields have something to offer, like persuasion, journalism, decision science, and information design.
- Build a crew. Ask who you would hire if the result had to be extraordinary. For a deck, that could be an analyst, a journalist, and an editor, plus a motion or audio designer if someone will present it. Add a red team to attack it, such as a short seller or a forensic accountant.
- Do each field's actual work. Each crew member stands for a set of methods. Writing "as a short seller" changes nothing. Doing what a short seller does changes the result: hunt for the weakest number, check it against outside sources, and build the case against it. Role play makes the transcript odder and the result no better.
- Use parallel agents where the platform allows. Give each field its own subagent or thread with a concrete method to apply, then merge what they find.

## What to return

When the user asks for the ambitious version of a task or prompt, return:

1. The real outcome, in one line.
2. The upgrade for each axis that fits, as concrete next steps or a rewritten prompt. Name any axis you skipped and give the reason in a few words.
3. What you need to do it, such as tools, data access, machines, and connectors. Mark what you already have.
4. The outside check that will show it worked.

Then ask which version to run. Once the user picks one, do it, and run the outside check before you report success.

## Notes for the human

Users often hold back because they don't believe a task is possible, or because they trust themselves only inside their own field. Michelangelo resisted the Sistine Chapel because he was a sculptor. Three things help, and you can offer them when someone hesitates.

- Treat the hard goal as ordinary homework. People who don't know a problem is famous sometimes just solve it.
- Point to someone who already did it. Once one person breaks a barrier, others follow fast.
- Make failure cheap. A prototype run beside the old process costs little if it doesn't work. Linux started as "just a hobby."

## Source

Adapted from Felix Rieseberg's post ["How to be more ambitious: A tutorial for humans with models"](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/), published 13 October 2026. The axes, techniques, and examples are his. The wording here is a paraphrase.
