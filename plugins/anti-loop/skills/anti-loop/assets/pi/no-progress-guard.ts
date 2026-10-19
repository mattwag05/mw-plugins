import { createHash } from "node:crypto";

// No-progress guard for small local models. Keeps only in-memory hashes and short
// output excerpts for the current session; nothing is written to disk.
//
// Repeat counts reset only on a successful edit/write; the no-progress budget
// also resets on a tool result never seen before.
// shortcut: file changes made through bash (sed -i, scripts) do not count as
// progress; add a mutation heuristic if that causes false stops in practice.
export const LIMITS = {
  rerunBlockAfter: 2,   // identical call + identical result twice -> block a third run
  resultWarnAt: 3,      // same output from any spelling of a call -> annotate it
  resultStopAt: 4,      // same output again -> stop tools and force a written explanation
  budgetCalls: 10,      // calls with no progress -> steer toward acting or reporting
  toolOnlyTurns: 6,     // assistant turns with tool calls and no prose -> ask for a status line
  minResultChars: 20,   // shorter outputs ("", "OK") are too generic to compare across calls
};

const MUTATING = new Set(["edit", "write"]);
const QUESTION = /\?\s*$|^(what|why|how|are you|is it|did you)\b|what happened/i;
const sha = (value) => createHash("sha256").update(value).digest("hex");
const normalize = (input) => JSON.stringify(input ?? {}).replace(/\\n|\\t|\s+/g, " ").replace(/ +/g, " ");
const textOf = (content) => (content ?? []).filter((p) => p.type === "text").map((p) => p.text).join("\n");
const excerpt = (text) => (text.length > 300 ? `${text.slice(0, 300)}…` : text).trim();
const EXPLAIN = "Answer the user in plain text: (1) what you were trying to learn, (2) what the repeated output already tells you, " +
  "(3) the concrete change or different check you would make next, or what blocks you. Do not ask to rerun the command.";
const note = (content, customType = "no-progress-guard") => ({ type: "custom_message", customType, content, display: true });

export default function noProgressGuard(pi) {
  let calls;            // call hash -> { result, count }
  let results;          // result hash -> { count, excerpt }
  let sinceProgress, budgetWarned, toolOnlyStreak;
  let pendingExplain;   // reason string once a hard stop fires
  let lastStop;         // evidence carried into the next user prompt
  let savedTools = null;
  let pausedBlocks = 0;
  const blockedIds = new Set(); // blocked calls never ran, so their results are not evidence

  const resetProgress = () => {
    calls = new Map();
    results = new Map();
    sinceProgress = 0;
    budgetWarned = false;
  };
  const resetSession = () => {
    resetProgress();
    toolOnlyStreak = 0;
    pendingExplain = null;
    lastStop = null;
    restoreTools();
  };
  const disableTools = () => {
    if (savedTools === null) savedTools = pi.getActiveTools();
    pi.setActiveTools([]);
  };
  function restoreTools() {
    if (savedTools !== null) pi.setActiveTools(savedTools);
    savedTools = null;
    pausedBlocks = 0;
  }
  const evidence = () => [...results.values()]
    .filter((r) => r.count >= 2)
    .map((r) => `- seen ${r.count}x: ${r.excerpt}`)
    .join("\n");
  const stop = (why) => {
    pendingExplain = why;
    lastStop = `${why}\nOutputs you already have:\n${evidence() || "(none recorded)"}`;
  };

  resetSession();
  // Deliberately no agent_start reset: a follow-up like "What happened?" must not re-arm reruns.
  pi.on("session_start", resetSession);

  pi.on("tool_call", (event, ctx) => {
    // Paused: a stop is pending, or tools were switched off (older Pi may still offer them).
    if (pendingExplain || savedTools !== null) {
      blockedIds.add(event.toolCallId);
      // Pi releases without `terminate` cannot end the batch; abort rather than loop on blocked calls.
      if (++pausedBlocks > 2) ctx?.abort?.();
      return { block: true, terminate: true, reason: `Tools are paused by the no-progress guard. ${EXPLAIN}` };
    }
    const prior = calls.get(sha(`${event.toolName}:${normalize(event.input)}`));
    if (prior && prior.count >= LIMITS.rerunBlockAfter) {
      const shown = results.get(prior.result)?.excerpt ?? "";
      if (prior.blocked) {
        stop(`You retried a blocked ${event.toolName} call.`);
        blockedIds.add(event.toolCallId);
        return { block: true, terminate: true, reason: `Blocked again. Tools are paused. ${EXPLAIN}` };
      }
      prior.blocked = true;
      blockedIds.add(event.toolCallId);
      return {
        block: true,
        reason: `Blocked without running: this exact ${event.toolName} call already returned the same output ${prior.count} times:\n${shown}\n` +
          "Rerunning it cannot tell you anything new. In one sentence, say what that output means, then make a code change, run a different check, or tell the user what blocks you.",
      };
    }
  });

  pi.on("tool_result", (event) => {
    if (blockedIds.delete(event.toolCallId)) return;
    const text = textOf(event.content);
    if (MUTATING.has(event.toolName) && !event.isError) {
      resetProgress();
      return;
    }
    const callKey = sha(`${event.toolName}:${normalize(event.input)}`);
    const resultKey = sha(JSON.stringify([event.toolName, Boolean(event.isError), text]));
    const call = calls.get(callKey);
    calls.set(callKey, { result: resultKey, count: call?.result === resultKey ? call.count + 1 : 1 });

    const seen = results.get(resultKey);
    if (seen) sinceProgress += 1;
    else {
      sinceProgress = 0;
      budgetWarned = false;
    }
    if (text.length < LIMITS.minResultChars) {
      if (!seen) results.set(resultKey, { count: 1, excerpt: excerpt(text) });
      return;
    }
    const count = (seen?.count ?? 0) + 1;
    results.set(resultKey, { count, excerpt: excerpt(text) });
    if (count >= LIMITS.resultStopAt) {
      stop(`The same ${event.toolName} output came back ${count} times, from differently worded calls.`);
      return { content: [...event.content, { type: "text", text: `\n[no-progress guard] This output has now appeared ${count} times. Tools are paused. ${EXPLAIN}` }] };
    }
    if (count === LIMITS.resultWarnAt) {
      return { content: [...event.content, { type: "text", text: `\n[no-progress guard] You have now seen this exact output ${count} times, from differently worded calls. Rewording the call will not change it. Do not run it again: state what it means and act on it.` }] };
    }
  });

  pi.on("turn_end", (event) => {
    const entries = [];
    const parts = event.message?.role === "assistant" && Array.isArray(event.message.content) ? event.message.content : [];
    const usedTools = parts.some((p) => p.type === "toolCall");
    const prose = parts.filter((p) => p.type === "text").map((p) => p.text).join("").trim();
    toolOnlyStreak = usedTools && prose.length < 15 ? toolOnlyStreak + 1 : 0;

    if (pendingExplain) {
      const why = pendingExplain;
      pendingExplain = null;
      disableTools();
      return {
        entries: [note(`No-progress guard: ${why} Tools are off for this reply.\n${EXPLAIN}`)],
        continue: true,
      };
    }
    if (sinceProgress >= LIMITS.budgetCalls && !budgetWarned) {
      budgetWarned = true;
      entries.push(note(`No-progress guard: ${sinceProgress} tool calls without a file change or a new result. ` +
        "Stop gathering evidence. Write your current hypothesis in one sentence, then make the change it implies or tell the user what blocks you."));
    }
    if (toolOnlyStreak >= LIMITS.toolOnlyTurns) {
      toolOnlyStreak = 0;
      entries.push(note("Status check: before your next tool call, write one line saying what the last results showed and what you will do next."));
    }
    if (entries.length) return { entries };
  });

  pi.on("before_agent_start", (event) => {
    // Older Pi has no messageType; any event with a prompt string is a user run.
    if (typeof event.prompt !== "string" || !lastStop) return;
    const evidenceText = lastStop;
    lastStop = null;
    // A question about the stop gets a text answer first; tools come back when the run settles.
    if (QUESTION.test(event.prompt.trim())) disableTools();
    return {
      systemPrompt: `${event.systemPrompt}\n\nNo-progress guard: your previous run was stopped. ${evidenceText}\n` +
        (savedTools !== null
          ? "Tools are off for this reply. Answer the user's question in plain text."
          : "Do not rerun calls that produced these outputs. Use them, or try a genuinely different approach."),
    };
  });

  // agent_end exists on every Pi release; agent_settled only on newer ones.
  const settle = () => {
    restoreTools();
    pendingExplain = null;
  };
  pi.on("agent_end", settle);
  pi.on("agent_settled", settle);
}
