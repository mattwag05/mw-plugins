import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { resolve } from "node:path";

// No-progress guard for small local models. Keeps only in-memory hashes and short
// output excerpts for the current session; nothing is written to disk.
//
// An edit/write that changes a file resets the repeat counts; the no-progress budget
// also resets on a result never seen before from a command not yet run.
// shortcut: file changes made through bash (sed -i, scripts) do not count as
// progress; add a mutation heuristic if that causes false stops in practice.
export const LIMITS = {
  rerunBlockAfter: 2,   // identical call + identical result twice -> block a third run
  resultWarnAt: 3,      // same output from any spelling of a call -> annotate it
  resultStopAt: 4,      // same output again -> stop tools and force a written explanation
  producerWarnAt: 3,    // same command rerun only to view other parts of its output -> annotate
  producerBlockAt: 6,   // ...and again -> block; a retry after that stops
  editWarnAt: 3,        // edits in a row that left a check's output unchanged -> annotate
  editStopAt: 5,        // ...and more -> stop
  sideEffectBlockAt: 2, // runs that delete/overwrite paths outside the project -> block the next
  budgetCalls: [10, 20, 30], // calls with no progress -> steer, steer again, stop
  toolOnlyTurns: 6,     // assistant turns with tool calls and no prose -> ask for a status line
  proseBlocksStop: 3,   // calls blocked for a missing status line -> stop
  minResultChars: 20,   // shorter outputs ("", "OK") are too generic to compare across calls
  minProseChars: 8,     // "Tests pass." counts as a status line
};

const MUTATING = new Set(["edit", "write"]);
const QUESTION = /\?\s*$|^(what|why|how|are you|is it|did you)\b|what happened/i;
// Pipeline stages that only select or reshape output already produced upstream.
const VIEW = /^(sed|head|tail|grep|egrep|fgrep|rg|wc|less|more|cat|cut|sort|uniq|nl|awk|tr|column)\b/;
const SCRATCH = /^(\/tmp|\/private\/tmp|\/private\/var\/folders|\/var\/folders|\/dev)(\/|$)/;
const sha = (value) => createHash("sha256").update(value).digest("hex");
const normalize = (input) => JSON.stringify(input ?? {}).replace(/\\n|\\t|\s+/g, " ").replace(/ +/g, " ");
const squash = (text) => text.replace(/\s+/g, " ").trim();
const textOf = (content) => (content ?? []).filter((p) => p.type === "text").map((p) => p.text).join("\n");
const excerpt = (text) => (text.length > 300 ? `${text.slice(0, 300)}…` : text).trim();
const proseOf = (message) => (message?.role === "assistant" && Array.isArray(message.content) ? message.content : [])
  .filter((p) => p.type === "text").map((p) => p.text).join("").trim();
const EXPLAIN = "Answer the user in plain text: (1) what you were trying to learn, (2) what the repeated output already tells you, " +
  "(3) the concrete change or different check you would make next, or what blocks you. Do not ask to rerun the command.";
const STATUS = "Status check: before your next tool call, write one line saying what the last results showed and what you will do next.";
const note = (content, customType = "no-progress-guard") => ({ type: "custom_message", customType, content, display: true });

// Splits a shell command on top-level pipes, ignoring quoted text and `||`.
export function pipeline(command) {
  const parts = [];
  let quote = null, start = 0;
  for (let i = 0; i < command.length; i++) {
    const ch = command[i];
    if (ch === "\\" && quote !== "'") i++;
    else if (quote) { if (ch === quote) quote = null; }
    else if (ch === "'" || ch === '"') quote = ch;
    else if (ch === "|" && command[i + 1] !== "|" && command[i - 1] !== "|") {
      parts.push(command.slice(start, i));
      start = i + 1;
    }
  }
  parts.push(command.slice(start));
  return parts;
}

// The command that produces output, without trailing stages that only view it.
export function producerOf(command) {
  const parts = pipeline(command);
  let viewed = false;
  while (parts.length > 1 && VIEW.test(parts.at(-1).trim())) {
    parts.pop();
    viewed = true;
  }
  return { producer: squash(parts.join("|").replace(/\s*2>&1\s*$/, "")), viewed };
}

// Paths outside the working directory that a command deletes, moves or overwrites.
export function outsideTargets(command, cwd) {
  const home = homedir();
  const targets = [];
  for (const m of command.matchAll(/(?:^|[;&|(\s])(?:rm|mv)\s+([^;&|<>()\n]+)/g)) {
    targets.push(...m[1].trim().split(/\s+/).filter((t) => !t.startsWith("-")));
  }
  for (const m of command.matchAll(/(?:^|[^0-9&>])>>?\s*([^\s;&|<>()]+)/g)) targets.push(m[1]);
  return [...new Set(targets.map((t) => t.replace(/^["']|["']$/g, ""))
    .filter((t) => /^(~|\$HOME|\/)/.test(t))
    .map((t) => resolve(t.replace(/^(~|\$HOME)(?=\/|$)/, home)))
    .filter((t) => !SCRATCH.test(t) && !(cwd && (t === cwd || t.startsWith(`${cwd}/`)))))].sort();
}

function isNoopMutation(toolName, input, cwd) {
  if (toolName === "edit") {
    const edits = Array.isArray(input?.edits) ? input.edits : [input ?? {}];
    return edits.length > 0 && edits.every((e) => typeof e.oldText === "string" && e.oldText === e.newText);
  }
  if (toolName === "write" && typeof input?.path === "string" && typeof input?.content === "string") {
    try {
      const path = resolve(cwd ?? process.cwd(), input.path.replace(/^~(?=\/|$)/, homedir()));
      return readFileSync(path, "utf8") === input.content;
    } catch {
      return false; // new or unreadable file: the write is real
    }
  }
  return false;
}

export default function noProgressGuard(pi) {
  let calls;            // exact call hash -> { result, count }
  let results;          // result hash -> { count, excerpt }
  let producers;        // producing command hash -> { runs, views: Set, blocked }
  let sinceProgress, budgetLevel;
  const checks = new Map();      // exact bash call hash -> { result, epoch, ineffective }; survives edits
  const sideEffects = new Map(); // outside-target list -> runs
  let epoch = 0;                 // count of edits/writes that changed a file
  let toolOnlyStreak, statusAsked, statusIgnored, requireProse, lastProse, proseBlocks;
  let pendingExplain;   // reason string once a hard stop fires
  let lastStop;         // evidence carried into the next user prompt
  let savedTools = null;
  let pausedBlocks = 0;
  const blockedIds = new Set(); // blocked calls never ran, so their results are not evidence
  const noopIds = new Set();
  const sideEffectIds = new Map();

  const resetProgress = () => {
    calls = new Map();
    results = new Map();
    producers = new Map();
    sinceProgress = 0;
    budgetLevel = 0;
  };
  const resetSession = () => {
    resetProgress();
    checks.clear();
    sideEffects.clear();
    toolOnlyStreak = 0;
    statusAsked = false;
    statusIgnored = 0;
    requireProse = false;
    lastProse = true;
    proseBlocks = 0;
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
  const block = (event, reason, hard = false) => {
    blockedIds.add(event.toolCallId);
    return hard ? { block: true, terminate: true, reason } : { block: true, reason };
  };
  const sawProse = () => {
    statusAsked = false;
    statusIgnored = 0;
    requireProse = false;
    proseBlocks = 0;
  };

  resetSession();
  // Deliberately no agent_start reset: a follow-up like "What happened?" must not re-arm reruns.
  pi.on("session_start", resetSession);

  // Fires once the assistant message is complete, before its tool calls run.
  pi.on("message_end", (event) => {
    if (event.message?.role !== "assistant") return;
    lastProse = proseOf(event.message).length >= LIMITS.minProseChars;
    if (lastProse) sawProse();
  });

  pi.on("tool_call", (event, ctx) => {
    // Paused: a stop is pending, or tools were switched off (older Pi may still offer them).
    if (pendingExplain || savedTools !== null) {
      // Pi releases without `terminate` cannot end the batch; abort rather than loop on blocked calls.
      if (++pausedBlocks > 2) ctx?.abort?.();
      return block(event, `Tools are paused by the no-progress guard. ${EXPLAIN}`, true);
    }
    if (requireProse && !lastProse) {
      if (++proseBlocks >= LIMITS.proseBlocksStop) {
        stop("You kept calling tools without the status line the guard asked for.");
        return block(event, `Blocked: no status line. Tools are paused. ${EXPLAIN}`, true);
      }
      return block(event, "Blocked: the guard asked for a status line and this message has none. " +
        "Write one line saying what the last results showed and what you will do next, then call the tool in that same message.");
    }

    const prior = calls.get(sha(`${event.toolName}:${normalize(event.input)}`));
    if (prior && prior.count >= LIMITS.rerunBlockAfter) {
      const shown = results.get(prior.result)?.excerpt ?? "";
      if (prior.blocked) {
        stop(`You retried a blocked ${event.toolName} call.`);
        return block(event, `Blocked again. Tools are paused. ${EXPLAIN}`, true);
      }
      prior.blocked = true;
      return block(event, `Blocked without running: this exact ${event.toolName} call already returned the same output ${prior.count} times:\n${shown}\n` +
        "Rerunning it cannot tell you anything new. In one sentence, say what that output means, then make a code change, run a different check, or tell the user what blocks you.");
    }

    if (MUTATING.has(event.toolName)) {
      if (isNoopMutation(event.toolName, event.input, ctx?.cwd)) noopIds.add(event.toolCallId);
      return;
    }
    const command = event.toolName === "bash" ? event.input?.command : null;
    if (typeof command !== "string") return;

    const { producer } = producerOf(command);
    const p = producers.get(sha(producer));
    if (p && p.runs >= LIMITS.producerBlockAt && p.views.size >= 2) {
      if (p.blocked) {
        stop("You kept rerunning one command to view different parts of its output.");
        return block(event, `Blocked again. Tools are paused. ${EXPLAIN}`, true);
      }
      p.blocked = true;
      return block(event, `Blocked without running: you have run this command ${p.runs} times only to view different parts of its output. ` +
        `Its output has not changed since your last edit. Save it once (\`${excerpt(producer).slice(0, 120)} > /tmp/pi-run.txt 2>&1\`) and read slices of that file, or act on what you already saw.`);
    }

    const targets = outsideTargets(command, ctx?.cwd);
    if (targets.length) {
      const key = targets.join(" ");
      const runs = sideEffects.get(key) ?? 0;
      if (runs >= LIMITS.sideEffectBlockAt) {
        return block(event, `Blocked: this command deletes or overwrites ${key} outside the project, and has already done so ${runs} times. ` +
          "Remove that part of the command, point it at a scratch path, or ask the user first.");
      }
      sideEffects.set(key, runs + 1);
      if (runs + 1 === LIMITS.sideEffectBlockAt) sideEffectIds.set(event.toolCallId, key);
    }
  });

  pi.on("tool_result", (event) => {
    if (blockedIds.delete(event.toolCallId)) return;
    const text = textOf(event.content);
    if (MUTATING.has(event.toolName) && !event.isError) {
      if (noopIds.delete(event.toolCallId)) {
        sinceProgress += 1;
        return { content: [...event.content, { type: "text", text: "\n[no-progress guard] This left the file unchanged, so it does not count as progress." }] };
      }
      epoch += 1;
      resetProgress();
      return;
    }
    noopIds.delete(event.toolCallId);
    const notes = [];
    const annotate = () => (notes.length ? { content: [...event.content, ...notes.map((t) => ({ type: "text", text: `\n[no-progress guard] ${t}` }))] } : undefined);

    const callKey = sha(`${event.toolName}:${normalize(event.input)}`);
    const resultKey = sha(JSON.stringify([event.toolName, Boolean(event.isError), text]));
    const call = calls.get(callKey);
    calls.set(callKey, { result: resultKey, count: call?.result === resultKey ? call.count + 1 : 1 });

    const command = event.toolName === "bash" ? event.input?.command : null;
    let rerunProducer = false;
    if (typeof command === "string") {
      const { producer } = producerOf(command);
      const pk = sha(producer);
      const p = producers.get(pk) ?? { runs: 0, views: new Set(), blocked: false };
      p.runs += 1;
      p.views.add(sha(squash(command)));
      producers.set(pk, p);
      rerunProducer = p.runs > 1;
      if (p.runs === LIMITS.producerWarnAt && p.views.size >= 2) {
        notes.push(`You have run this same command ${p.runs} times only to view different parts of its output. ` +
          "Save it to a file once and read slices of the file instead of rerunning it.");
      }

      // Did the edits since this check last ran change what it reports?
      const c = checks.get(callKey);
      if (c && c.epoch < epoch) c.ineffective = c.result === resultKey ? c.ineffective + 1 : 0;
      const ineffective = c?.ineffective ?? 0;
      checks.set(callKey, { result: resultKey, epoch, ineffective });
      if (ineffective >= LIMITS.editStopAt) {
        stop(`${ineffective} edits in a row did not change the output of the same check.`);
        notes.push(`${ineffective} edits in a row left this check's output unchanged. Tools are paused. ${EXPLAIN}`);
        return annotate();
      }
      if (ineffective === LIMITS.editWarnAt) {
        notes.push(`Your last ${ineffective} edits did not change this check's output. Read the failing assertion and the code under test before editing again. ` +
          "If you are changing expected values to match the output, first confirm the output is actually correct.");
      }
      const key = sideEffectIds.get(event.toolCallId);
      if (key) {
        sideEffectIds.delete(event.toolCallId);
        notes.push(`This command has now deleted or overwritten ${key}, outside the project, ${LIMITS.sideEffectBlockAt} times. The next run that does so will be blocked.`);
      }
    }

    const seen = results.get(resultKey);
    // A new slice of output from a command already run is not new evidence.
    if (seen || rerunProducer) sinceProgress += 1;
    else {
      sinceProgress = 0;
      budgetLevel = 0;
    }
    if (text.length < LIMITS.minResultChars) {
      if (!seen) results.set(resultKey, { count: 1, excerpt: excerpt(text) });
      return annotate();
    }
    const count = (seen?.count ?? 0) + 1;
    results.set(resultKey, { count, excerpt: excerpt(text) });
    if (count >= LIMITS.resultStopAt) {
      stop(`The same ${event.toolName} output came back ${count} times, from differently worded calls.`);
      notes.push(`This output has now appeared ${count} times. Tools are paused. ${EXPLAIN}`);
    } else if (count === LIMITS.resultWarnAt) {
      notes.push(`You have now seen this exact output ${count} times, from differently worded calls. Rewording the call will not change it. Do not run it again: state what it means and act on it.`);
    }
    return annotate();
  });

  pi.on("turn_end", (event) => {
    const entries = [];
    const parts = event.message?.role === "assistant" && Array.isArray(event.message.content) ? event.message.content : [];
    const usedTools = parts.some((p) => p.type === "toolCall");
    const hasProse = proseOf(event.message).length >= LIMITS.minProseChars;
    toolOnlyStreak = usedTools && !hasProse ? toolOnlyStreak + 1 : 0;
    if (hasProse) sawProse();
    // One ignored status request is enough: from then on, tool calls need a status line.
    else if (statusAsked && usedTools) requireProse = ++statusIgnored >= 1;

    if (!pendingExplain && sinceProgress >= LIMITS.budgetCalls[budgetLevel]) {
      budgetLevel += 1;
      if (budgetLevel >= LIMITS.budgetCalls.length) stop(`${sinceProgress} tool calls without a file change or new evidence.`);
      else entries.push(note(`No-progress guard: ${sinceProgress} tool calls without a file change or new evidence. ` +
        "Stop gathering evidence. Write your current hypothesis in one sentence, then make the change it implies or tell the user what blocks you."));
    }
    if (pendingExplain) {
      const why = pendingExplain;
      pendingExplain = null;
      disableTools();
      return {
        entries: [note(`No-progress guard: ${why} Tools are off for this reply.\n${EXPLAIN}`)],
        continue: true,
      };
    }
    if (toolOnlyStreak >= LIMITS.toolOnlyTurns) {
      toolOnlyStreak = 0;
      statusAsked = true;
      entries.push(note(STATUS));
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
