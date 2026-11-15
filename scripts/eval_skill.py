#!/usr/bin/env python3
"""Run a skill's fixture evals headless and print PASS/FAIL per case.

Layout: <skill-dir>/evals/<case>/task.md, optional workspace/, and an executable
`check` run in the workspace copy after the agent finishes (exit 0 = pass).

  python3 scripts/eval_skill.py plugins/core/skills/debug [--runs 3] [--model ID]

The default agent is `pi -p` with only the skill under test loaded. --agent-cmd
replaces it: the command is run as `<cmd> <skill-dir> <task-file>` in the workspace.
Exit status: 0 all cases passed, 1 any failed, 2 usage error.
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def pi_command(skill_dir, task_text, model):
    cmd = [
        "pi", "-p", "--no-session", "--no-skills", "--skill", str(skill_dir),
        "--no-context-files", "--no-extensions", "--no-mcp", "--no-prompt-templates",
        "--offline",
    ]
    if model:
        cmd += ["--model", model]
    return cmd + ["--", task_text]


def find_cases(skill_dir):
    evals = skill_dir / "evals"
    if not evals.is_dir():
        return []
    return sorted(p for p in evals.iterdir() if (p / "task.md").is_file())


def run_case(case, skill_dir, args, out_dir, run_no):
    check = case / "check"
    if not (check.is_file() and os.access(check, os.X_OK)):
        return False, "check missing or not executable", None
    work = Path(tempfile.mkdtemp(prefix=f"eval-{case.name}-", dir=out_dir))
    if (case / "workspace").is_dir():
        shutil.copytree(case / "workspace", work, dirs_exist_ok=True)
    task_file = case / "task.md"
    if args.agent_cmd:
        cmd = shlex.split(args.agent_cmd) + [str(skill_dir), str(task_file)]
    else:
        cmd = pi_command(skill_dir, task_file.read_text(), args.model)
    transcript = Path(out_dir) / f"{case.name}-run{run_no}.log"
    with transcript.open("w") as log:
        try:
            agent = subprocess.run(cmd, cwd=work, stdout=log, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            return False, f"agent timed out after {args.timeout}s", transcript
        except FileNotFoundError as e:
            return False, f"agent not runnable: {e}", transcript
    if agent.returncode != 0:
        return False, f"agent exited {agent.returncode}", transcript
    env = dict(os.environ, EVAL_TRANSCRIPT=str(transcript), EVAL_WORKSPACE=str(work))
    result = subprocess.run([str(check.resolve())], cwd=work, env=env,
                            capture_output=True, text=True, timeout=120)
    reason = (result.stdout + result.stderr).strip().splitlines()
    return result.returncode == 0, (reason[-1] if reason else f"check exited {result.returncode}"), transcript


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("skill_dir", type=Path)
    ap.add_argument("--runs", type=int, default=1, help="runs per case; a case passes only if every run passes")
    ap.add_argument("--model", help="pi model ID (default: pi's configured default)")
    ap.add_argument("--agent-cmd", help="replace pi: run '<cmd> <skill-dir> <task-file>' in the workspace")
    ap.add_argument("--timeout", type=int, default=900, help="seconds per agent run")
    ap.add_argument("--out", type=Path, help="directory for workspaces and transcripts (default: a new temp dir)")
    ap.add_argument("--case", action="append", help="run only this case name (repeatable)")
    args = ap.parse_args(argv)

    skill_dir = args.skill_dir.resolve()
    if not (skill_dir / "SKILL.md").is_file():
        print(f"error: {skill_dir}/SKILL.md not found", file=sys.stderr)
        return 2
    cases = [c for c in find_cases(skill_dir) if not args.case or c.name in args.case]
    if not cases:
        print(f"error: no cases under {skill_dir}/evals", file=sys.stderr)
        return 2
    out_dir = args.out.resolve() if args.out else Path(tempfile.mkdtemp(prefix="skill-eval-"))
    out_dir.mkdir(parents=True, exist_ok=True)

    failed = 0
    for case in cases:
        passes = 0
        for n in range(1, args.runs + 1):
            start = time.monotonic()
            ok, reason, transcript = run_case(case, skill_dir, args, out_dir, n)
            passes += ok
            print(f"{'PASS' if ok else 'FAIL'} {case.name} run {n}/{args.runs} "
                  f"({time.monotonic() - start:.0f}s): {reason}", flush=True)
        if passes < args.runs:
            failed += 1
    print(f"{len(cases) - failed}/{len(cases)} cases passed; transcripts in {out_dir}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
