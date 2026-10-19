// Run: node --test mac-extras/pi-agent/test/
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import guard from "../no-progress-guard.ts";

const ALL_TOOLS = ["read", "bash", "edit", "write"];

// Minimal stand-in for the Pi ExtensionAPI surface the guard uses.
function harness() {
  const handlers = {};
  let active = [...ALL_TOOLS];
  const log = { blocked: [], notes: [], annotated: [], continued: 0, executed: 0, aborts: 0 };
  const ctx = { abort: () => { log.aborts += 1; } };
  const pi = {
    on: (name, fn) => ((handlers[name] ??= []).push(fn)),
    getActiveTools: () => [...active],
    setActiveTools: (names) => { active = [...names]; },
  };
  guard(pi);
  const emit = (name, event) => handlers[name]?.map((fn) => fn({ type: name, ...event }, ctx)).find(Boolean);
  emit("session_start", {});
  let n = 0;

  // Runs one assistant message: its tool calls, their results, then turn_end.
  function turn({ text = "", calls = [] }, resultFor) {
    for (const call of calls) {
      const id = call.id ?? `c${n++}`;
      const decision = emit("tool_call", { toolName: call.name, toolCallId: id, input: call.input });
      if (decision?.block) { log.blocked.push({ call, decision }); continue; }
      log.executed += 1;
      const result = resultFor(call, id);
      const out = emit("tool_result", { toolName: call.name, toolCallId: id, input: call.input,
        content: [{ type: "text", text: result.text }], isError: result.isError ?? false });
      if (out?.content) log.annotated.push(out.content.at(-1).text);
    }
    const message = { role: "assistant", content: [
      ...(text ? [{ type: "text", text }] : []),
      ...calls.map((c) => ({ type: "toolCall", name: c.name, arguments: c.input })),
    ] };
    const boundary = emit("turn_end", { message });
    for (const e of boundary?.entries ?? []) log.notes.push(e.content);
    if (boundary?.continue) log.continued += 1;
    return boundary;
  }
  const user = (prompt) => emit("before_agent_start", { messageType: "user", prompt, systemPrompt: "SYS" });
  return { emit, turn, user, log, tools: () => active };
}

const bash = (command) => ({ name: "bash", input: { command } });
const fixed = (text) => () => ({ text });

test("today's labyrinth loop: stops and forces an explanation before the user has to intervene", () => {
  const events = JSON.parse(readFileSync(new URL("./labyrinth-loop-20261019.json", import.meta.url)));
  const results = new Map(events.filter((e) => e.kind === "result").map((e) => [e.id, e]));
  const h = harness();
  let stoppedAt = null;
  for (const [i, e] of events.entries()) {
    if (e.kind === "user") {
      if (i > 0) break; // the original run never reached the user's follow-ups under the new guard
      h.user(e.prompt);
    }
    if (e.kind !== "assistant") continue;
    const b = h.turn(e, (call, id) => results.get(id) ?? { text: "" });
    if (b?.continue) { stoppedAt = i; break; }
  }
  assert.ok(stoppedAt !== null, "guard must force an explanation turn");
  // Old guard: first block after these same 13 calls, then two more aborts, 30 calls and no explanation.
  assert.equal(h.log.executed, 13);
  assert.equal(h.log.blocked.length, 0, "the stop comes from the repeated result, not an abort path");
  assert.deepEqual(h.tools(), [], "tools are off for the explanation reply");
  assert.match(h.log.notes.at(-1), /Tools are off for this reply/);
  assert.ok(h.log.annotated.some((t) => /3 times, from differently worded calls/.test(t)), "third repeat is annotated");
});

test("a question after a stop gets a text-only answer carrying the evidence; tools return when settled", () => {
  const h = harness();
  for (let i = 0; i < 4; i++) h.turn({ calls: [bash(`python3 -c 'x=${i}'`)] }, fixed("real work for 22 commands: 0.001s"));
  assert.equal(h.log.continued, 1);
  h.emit("agent_settled", {});
  assert.deepEqual(h.tools(), ALL_TOOLS);
  const start = h.user("What happened?");
  assert.deepEqual(h.tools(), []);
  assert.match(start.systemPrompt, /seen 4x: real work for 22 commands/);
  h.emit("agent_settled", {});
  assert.deepEqual(h.tools(), ALL_TOOLS);
});

test("an instruction after a stop keeps tools but blocks the old measurement", () => {
  const h = harness();
  for (let i = 0; i < 4; i++) h.turn({ calls: [bash(`run ${i}`)] }, fixed("real work for 22 commands: 0.001s"));
  h.emit("agent_settled", {});
  const start = h.user("You're looping, try a different approach.");
  assert.deepEqual(h.tools(), ALL_TOOLS);
  assert.match(start.systemPrompt, /Do not rerun calls/);
});

test("an exact rerun is blocked on the third try, and a retry after the block stops the run", () => {
  const h = harness();
  const cmd = bash("python3 test_labyrinth.py 2>&1 | tail -3");
  h.turn({ calls: [cmd] }, fixed("Ran 29 tests in 0.003s\n\nOK"));
  h.turn({ calls: [{ ...cmd, input: { command: "python3  test_labyrinth.py 2>&1 |  tail -3" } }] }, fixed("Ran 29 tests in 0.003s\n\nOK"));
  h.turn({ calls: [cmd] }, fixed("unreachable"));
  assert.equal(h.log.blocked.length, 1, "whitespace respelling counts as the same call");
  assert.match(h.log.blocked[0].decision.reason, /Ran 29 tests/);
  h.turn({ calls: [cmd] }, fixed("unreachable"));
  assert.equal(h.log.blocked.at(-1).decision.terminate, true);
  assert.equal(h.log.continued, 1);
  assert.equal(h.log.executed, 2);
});

test("a successful edit is progress: repeated test output after edits never trips the guard", () => {
  const h = harness();
  for (let i = 0; i < 6; i++) {
    h.turn({ text: "Fixing the next case.", calls: [{ name: "edit", input: { path: "a.py", i } }] }, fixed("Successfully replaced 1 block(s)"));
    h.turn({ text: "Running tests.", calls: [bash("python3 -m pytest -q")] }, fixed("1 failed, 28 passed in 0.12s"));
  }
  assert.deepEqual(h.log, { blocked: [], notes: [], annotated: [], continued: 0, executed: 12, aborts: 0 });
});

test("a silent tool-only streak gets one status prompt; a long no-progress stretch gets one steer", () => {
  const h = harness();
  for (let i = 0; i < 6; i++) h.turn({ calls: [bash(`ls dir${i}`)] }, fixed(`listing number ${i} with enough text`));
  assert.equal(h.log.notes.filter((n) => /Status check/.test(n)).length, 1);
  // Cycle through old outputs with new commands: every result is repeated evidence, none is new.
  for (let i = 0; i < 12; i++) h.turn({ text: "Checking again.", calls: [bash(`cat g${i}`)] }, fixed(`listing number ${i % 6} with enough text`));
  assert.equal(h.log.continued, 0);
  assert.equal(h.log.notes.filter((n) => /without a file change or a new result/.test(n)).length, 1);
});

test("short generic outputs are not compared across different commands", () => {
  const h = harness();
  for (let i = 0; i < 8; i++) h.turn({ text: "Step.", calls: [bash(`mkdir -p d${i}`)] }, fixed(""));
  assert.equal(h.log.continued, 0);
  assert.equal(h.log.blocked.length, 0);
});

test("older Pi (turn_end results ignored, no agent_settled): explanation arrives in-band, paused calls stop, agent_end restores", () => {
  const h = harness();
  for (let i = 0; i < 4; i++) h.turn({ calls: [bash(`probe ${i}`)] }, fixed("real work for 22 commands: 0.001s"));
  // The explanation request rides on the tool result itself, not only on the turn_end note.
  assert.match(h.log.annotated.at(-1), /Tools are paused\. Answer the user in plain text/);
  // Old Pi may keep offering tools: every call is blocked, and a third paused call aborts the run.
  for (let i = 0; i < 3; i++) h.turn({ calls: [bash(`other ${i}`)] }, fixed("unreachable"));
  assert.equal(h.log.executed, 4);
  assert.match(h.log.blocked[0].decision.reason, /Answer the user in plain text/);
  assert.equal(h.log.aborts, 1);
  h.emit("agent_end", { messages: [] });
  assert.deepEqual(h.tools(), ALL_TOOLS);
  h.turn({ text: "New approach.", calls: [bash("python3 -m pytest -q")] }, fixed("29 passed in 0.10s, all green"));
  assert.equal(h.log.executed, 5, "tools work again after the run ends");
});

test("old-style before_agent_start without messageType still answers a question with tools off", () => {
  const h = harness();
  for (let i = 0; i < 4; i++) h.turn({ calls: [bash(`probe ${i}`)] }, fixed("real work for 22 commands: 0.001s"));
  h.emit("agent_end", { messages: [] });
  const start = h.emit("before_agent_start", { prompt: "What happened?", systemPrompt: "SYS" });
  assert.deepEqual(h.tools(), []);
  assert.match(start.systemPrompt, /seen 4x/);
});
