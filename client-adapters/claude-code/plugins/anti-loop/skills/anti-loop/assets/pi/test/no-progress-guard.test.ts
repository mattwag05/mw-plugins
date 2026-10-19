// Run: node --test mac-extras/pi-agent/test/
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import guard, { LIMITS, pipeline, producerOf, outsideTargets } from "../no-progress-guard.ts";

const ALL_TOOLS = ["read", "bash", "edit", "write"];

// Minimal stand-in for the Pi ExtensionAPI surface the guard uses.
function harness() {
  const handlers = {};
  let active = [...ALL_TOOLS];
  const log = { blocked: [], notes: [], annotated: [], continued: 0, executed: 0, aborts: 0 };
  const ctx = { cwd: "/home/user/Desktop", abort: () => { log.aborts += 1; } };
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
    const message = { role: "assistant", content: [
      ...(text ? [{ type: "text", text }] : []),
      ...calls.map((c) => ({ type: "toolCall", name: c.name, arguments: c.input })),
    ] };
    emit("message_end", { message });
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
  // Old guard: first block after 13 calls, then two more aborts, 30 calls and no explanation.
  assert.ok(h.log.executed <= 13, `stopped after ${h.log.executed} executed calls`);
  assert.deepEqual(h.tools(), [], "tools are off for the explanation reply");
  assert.match(h.log.notes.at(-1), /Tools are off for this reply/);
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

const edit = (i) => ({ name: "edit", input: { path: "a.py", edits: [{ oldText: `old ${i}`, newText: `new ${i}` }] } });

test("edits that change a check's output are progress: the same check after each edit never trips the guard", () => {
  const h = harness();
  for (let i = 0; i < 6; i++) {
    h.turn({ text: "Fixing the next case.", calls: [edit(i)] }, fixed("Successfully replaced 1 block(s)"));
    h.turn({ text: "Running tests.", calls: [bash("python3 -m pytest -q")] }, fixed(`${6 - i} failed, ${23 + i} passed in 0.12s`));
  }
  assert.deepEqual(h.log, { blocked: [], notes: [], annotated: [], continued: 0, executed: 12, aborts: 0 });
});

test("edits that leave a check's output unchanged are flagged at 3 and stop the run at 5", () => {
  const h = harness();
  for (let i = 0; i < 6 && !h.log.continued; i++) {
    h.turn({ text: "Adjusting the assertion.", calls: [edit(i)] }, fixed("Successfully replaced 1 block(s)"));
    h.turn({ text: "Running tests.", calls: [bash("python3 test_x.py 2>&1 | tail -4")] }, fixed("Ran 29 tests\n\nFAILED (failures=1)"));
  }
  assert.ok(h.log.annotated.some((t) => /last 3 edits did not change this check's output/.test(t)));
  assert.equal(h.log.continued, 1);
  assert.match(h.log.notes.at(-1), /5 edits in a row/);
});

test("a silent tool-only streak gets one status prompt; a long no-progress stretch gets one steer", () => {
  const h = harness();
  for (let i = 0; i < 6; i++) h.turn({ calls: [bash(`ls dir${i}`)] }, fixed(`listing number ${i} with enough text`));
  assert.equal(h.log.notes.filter((n) => /Status check/.test(n)).length, 1);
  // Cycle through old outputs with new commands: every result is repeated evidence, none is new.
  for (let i = 0; i < 12; i++) h.turn({ text: "Checking again.", calls: [bash(`cat g${i}`)] }, fixed(`listing number ${i % 6} with enough text`));
  assert.equal(h.log.continued, 0);
  assert.equal(h.log.notes.filter((n) => /without a file change or new evidence/.test(n)).length, 1);
});

test("short generic outputs are not compared across different commands", () => {
  const h = harness();
  for (let i = 0; i < 8; i++) h.turn({ text: "Creating a directory.", calls: [bash(`mkdir -p d${i}`)] }, fixed(""));
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

// Replays assistant steps from a fixture until the guard forces an explanation turn.
function replay(steps, results, { compliant = false } = {}) {
  const h = harness();
  for (const e of steps) {
    const b = h.turn(compliant && !e.text ? { ...e, text: "Checking the next part of the output." } : e, (call, id) => results.get(id) ?? { text: "" });
    if (b?.continue) break;
  }
  return h;
}
const paging = JSON.parse(readFileSync(new URL("./labyrinth-paging-20261019.json", import.meta.url)));
const pagingResults = new Map(paging.filter((e) => e.kind === "result").map((e) => [e.id, e]));
const pagingSteps = paging.filter((e) => e.kind === "assistant");
const usesRm = (e) => e.calls.some((c) => (c.input?.command ?? "").includes("rm -f ~/.labyrinth"));

test("second session, edit-test thrash: stops at the 5th ineffective edit instead of running ~100 calls", () => {
  const h = replay(pagingSteps, pagingResults);
  assert.equal(h.log.continued, 1);
  assert.match(h.log.notes.at(-1), /5 edits in a row did not change the output/);
  assert.ok(h.log.executed <= 40, `stopped after ${h.log.executed} executed calls`);
});

test("second session, paging one command through sed windows: warned at 3 runs, blocked after 6, stopped on retry", () => {
  const start = pagingSteps.findIndex(usesRm);
  const h = replay(pagingSteps.slice(start), pagingResults, { compliant: true });
  assert.ok(h.log.annotated.some((t) => /same command 3 times only to view different parts/.test(t)));
  assert.ok(h.log.blocked.some((b) => /run this command 6 times only to view/.test(b.decision.reason)));
  assert.match(h.log.notes.at(-1), /rerunning one command to view different parts/);
});

test("second session, repeated rm of files in the home directory: annotated on the 2nd run, blocked on the 3rd", () => {
  const rmSteps = pagingSteps.filter(usesRm).map((e) => ({ ...e, calls: e.calls.filter((c) => (c.input?.command ?? "").includes("rm -f ~/.labyrinth")) }));
  const h = replay(rmSteps.slice(-3), pagingResults, { compliant: true });
  assert.ok(h.log.annotated.some((t) => /has now deleted or overwritten .*\.labyrinth_best\.json/.test(t)));
  assert.match(h.log.blocked[0].decision.reason, /deletes or overwrites .*outside the project, and has already done so 2 times/);
});

test("a status request ignored once makes silent tool calls wait for a status line", () => {
  const h = harness();
  for (let i = 0; i < 7; i++) h.turn({ calls: [bash(`ls dir${i}`)] }, fixed(`listing number ${i} with enough text`));
  h.turn({ calls: [bash("ls next")] }, fixed("unreachable output text here"));
  assert.match(h.log.blocked.at(-1).decision.reason, /asked for a status line and this message has none/);
  h.turn({ text: "Listings look fine; checking the next directory.", calls: [bash("ls next")] }, fixed("a listing that is new to the guard"));
  assert.equal(h.log.blocked.length, 1, "a message with prose runs again");
});

test("edits and writes that change nothing are not progress", () => {
  const dir = mkdtempSync(join(tmpdir(), "guard-"));
  const file = join(dir, "same.txt");
  writeFileSync(file, "unchanged\n");
  const h = harness();
  h.turn({ text: "Rewriting the file.", calls: [{ name: "write", input: { path: file, content: "unchanged\n" } }] }, fixed("Successfully wrote"));
  h.turn({ text: "Editing a line.", calls: [{ name: "edit", input: { path: file, edits: [{ oldText: "x", newText: "x" }] } }] }, fixed("Successfully replaced 1 block(s)"));
  assert.equal(h.log.annotated.filter((t) => /left the file unchanged/.test(t)).length, 2);
});

test("the no-progress budget steers at 10 and 20 calls and stops at 30", () => {
  const h = harness();
  for (let i = 0; i < 15; i++) h.turn({ text: "Collecting a listing.", calls: [bash(`ls a${i}`)] }, fixed(`listing number ${i} with enough text`));
  for (let i = 0; i < 30 && !h.log.continued; i++) h.turn({ text: "Collecting a listing.", calls: [bash(`ls b${i}`)] }, fixed(`listing number ${i % 15} with enough text`));
  assert.equal(h.log.notes.filter((n) => /tool calls without a file change or new evidence\. Stop/.test(n)).length, 2);
  assert.equal(h.log.continued, 1);
  assert.match(h.log.notes.at(-1), /30 tool calls without a file change/);
});

test("pipeline parsing keeps quoted pipes and || intact, and strips only trailing view stages", () => {
  assert.deepEqual(pipeline(`grep -E "a|b" f | wc -l`), [`grep -E "a|b" f `, " wc -l"]);
  assert.equal(pipeline("make || echo failed").length, 1);
  assert.equal(producerOf(`python3 run.py 2>&1 | sed -n '1,36p'`).producer, "python3 run.py");
  assert.equal(producerOf(`python3 run.py 2>&1 | grep -n x | head -5`).producer, "python3 run.py");
  assert.equal(producerOf("python3 run.py | python3 summarize.py").producer, "python3 run.py | python3 summarize.py");
  assert.deepEqual(outsideTargets('grep -E "a|b" f > /tmp/ok.txt; rm -rf ./build 2>&1 >/dev/null', "/tmp/x"), []);
});
