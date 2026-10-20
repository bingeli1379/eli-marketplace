#!/usr/bin/env python3
"""Measure where a finished /sdd:apply or /sdd:quick run spent its wall clock.

Reads the Claude Code session transcript and its subagent transcripts (every
message carries a timestamp), so nothing has to be logged while the run is live.

Usage:
  scripts/run-timing.py                 # latest session with subagents in the cwd's project
  scripts/run-timing.py <session.jsonl> # a specific session
  scripts/run-timing.py <session-dir>   # the <session-id>/ folder next to the jsonl
  scripts/run-timing.py ... --slow 60   # list Bash calls >= 60s (default 30)

Roles come from the agent's name / type; rounds come from the order agents ran in
(a reviewer started after a fix agent opens the next round), so a run whose agents
were named unusually can mis-group. Transcripts are pruned by Claude Code after a
while, so run this soon after the run, or copy its output somewhere durable.
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

TPE = timezone(timedelta(hours=8))
TEST_CMD = re.compile(
    r"\b(vitest|jest|pytest|playwright|dotnet test|(pnpm|npm|yarn)( -F \S+| run)? test\b|nx (run|affected)\S* .*test)"
)


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def clock(d):
    return d.astimezone(TPE).strftime("%H:%M:%S")


def mins(a, b):
    return max((b - a).total_seconds(), 0) / 60


def load(path):
    out = []
    with open(path) as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def span(events):
    t = [ts(e["timestamp"]) for e in events if "timestamp" in e]
    return (min(t), max(t)) if t else None


def bash_calls(events):
    """Return (start, seconds, command) for every Bash call that got a result."""
    pending, done = {}, []
    for e in events:
        content = (e.get("message") or {}).get("content")
        if not isinstance(content, list) or "timestamp" not in e:
            continue
        for b in content:
            if b.get("type") == "tool_use" and b.get("name") == "Bash":
                pending[b["id"]] = (ts(e["timestamp"]), b.get("input", {}).get("command", ""))
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in pending:
                t0, cmd = pending.pop(b["tool_use_id"])
                done.append((t0, (ts(e["timestamp"]) - t0).total_seconds(), cmd))
    return done


def role_of(name, meta):
    ident = " ".join([name, meta.get("agentType", ""), meta.get("customAgentType", ""), meta.get("spawnedAgentType", "")]).lower()
    if "architect" in ident:
        return "architect"
    if re.search(r"review|security|qa-engineer|\bqa\b|performance", ident):
        return "reviewer"
    if "fix" in ident:
        return "fix"
    if "writer" in ident:
        return "writer"
    return "impl"


def resolve(arg):
    if arg and arg.endswith(".jsonl"):
        return arg[:-6]
    if arg:
        return arg.rstrip("/")
    proj = os.path.expanduser("~/.claude/projects/" + re.sub(r"[^A-Za-z0-9]", "-", os.getcwd()))
    dirs = [d for d in glob.glob(proj + "/*/") if os.path.isdir(d + "subagents")]
    if not dirs:
        sys.exit(f"no session with subagents under {proj}")
    return max(dirs, key=lambda d: os.path.getmtime(d)).rstrip("/")


def main():
    args = sys.argv[1:]
    slow = 30
    if "--slow" in args:
        i = args.index("--slow")
        slow = int(args[i + 1])
        del args[i:i + 2]
    root = resolve(args[0] if args else None)
    if not os.path.exists(root + ".jsonl"):
        sys.exit(f"session transcript not found: {root}.jsonl")
    main_events = load(root + ".jsonl")
    m0, m1 = span(main_events)

    agents = []
    for p in glob.glob(os.path.join(root, "subagents", "*.jsonl")):
        ev = load(p)
        s = span(ev)
        if not s:
            continue
        mp = p[:-6] + ".meta.json"
        meta = json.load(open(mp)) if os.path.exists(mp) else {}
        name = meta.get("name") or os.path.basename(p)[6:-6]
        agents.append({"name": name, "role": role_of(name, meta), "start": s[0], "end": s[1], "bash": bash_calls(ev)})
    agents.sort(key=lambda a: a["start"])
    if not agents:
        sys.exit("no subagent transcripts found")

    print(f"Session {os.path.basename(root)}   all times GMT+8")
    print(f"Whole session   {clock(m0)} -> {clock(m1)}   {mins(m0, m1):6.1f} min\n")

    first_rev = next((a["start"] for a in agents if a["role"] == "reviewer"), None)
    impl = [a for a in agents if a["role"] in ("impl", "writer") and (first_rev is None or a["start"] < first_rev)]
    arch = [a for a in agents if a["role"] == "architect"]
    writer = [a for a in agents if a["role"] == "writer" and first_rev and a["start"] >= first_rev]
    post = [a for a in agents if a["role"] in ("reviewer", "fix") and first_rev and a["start"] >= first_rev]

    if arch:
        print(f"Architect       {clock(arch[0]['start'])} -> {clock(arch[-1]['end'])}   {mins(arch[0]['start'], arch[-1]['end']):6.1f} min")
    if impl:
        s, e = impl[0]["start"], max(a["end"] for a in impl)
        print(f"Phase 1 impl    {clock(s)} -> {clock(e)}   {mins(s, e):6.1f} min   ({len(impl)} agents, {sum(mins(a['start'], a['end']) for a in impl):.1f} min of agent time)")

    rounds = []
    for a in post:
        cur = rounds[-1] if rounds else None
        if a["role"] == "reviewer":
            if cur is None or cur["fix"]:
                cur = {"rev": [], "fix": []}
                rounds.append(cur)
            cur["rev"].append(a)
        elif cur is not None:
            cur["fix"].append(a)

    if rounds:
        print("\nPhase 2 review/fix rounds")
        print(f"  {'round':5s} {'review':>8s} {'triage':>8s} {'fix':>8s} {'handoff':>8s}   agents")
        p2_start = rounds[0]["rev"][0]["start"]
        p2_end = p2_start
        for i, r in enumerate(rounds, 1):
            rs, re_ = min(a["start"] for a in r["rev"]), max(a["end"] for a in r["rev"])
            fs = min((a["start"] for a in r["fix"]), default=None)
            fe = max((a["end"] for a in r["fix"]), default=None)
            nxt = min(a["start"] for a in rounds[i]["rev"]) if i < len(rounds) else None
            triage = f"{mins(re_, fs):.1f}" if fs else "-"
            fix = f"{mins(fs, fe):.1f}" if fs else "-"
            hand = f"{mins(fe, nxt):.1f}" if fe and nxt else "-"
            names = ", ".join(f"{a['name']} {mins(a['start'], a['end']):.1f}" for a in r["rev"] + r["fix"])
            print(f"  r{i:<4d} {mins(rs, re_):8.1f} {triage:>8s} {fix:>8s} {hand:>8s}   {names}")
            p2_end = max(p2_end, re_, fe or re_)
        print(f"  Phase 2 total {mins(p2_start, p2_end):.1f} min over {len(rounds)} round(s)   ({clock(p2_start)} -> {clock(p2_end)})")

    if writer:
        print(f"\nPhase 3 docs    {clock(writer[0]['start'])} -> {clock(writer[-1]['end'])}   {mins(writer[0]['start'], writer[-1]['end']):6.1f} min")

    work = [a for a in agents if a["role"] != "architect"]
    if work:
        s, e = work[0]["start"], max(a["end"] for a in work)
        print(f"\nApply window    {clock(s)} -> {clock(e)}   {mins(s, e):6.1f} min   (first dispatch to last agent finishing)")

    print("\nTest-like commands (approximate regex match on the Bash command; time is the whole command)")
    by_role = {}
    for a in agents:
        for t0, sec, cmd in a["bash"]:
            if TEST_CMD.search(cmd):
                by_role.setdefault(a["role"], []).append(sec)
    for t0, sec, cmd in bash_calls(main_events):
        if TEST_CMD.search(cmd):
            by_role.setdefault("orchestrator", []).append(sec)
    if by_role:
        for role, v in sorted(by_role.items()):
            print(f"  {role:13s} {len(v):3d} runs   total {sum(v):6.0f}s   max {max(v):5.0f}s")
    else:
        print("  none matched")

    print(f"\nBash calls >= {slow}s")
    rows = [(t0, sec, a["name"][:28], cmd) for a in agents for t0, sec, cmd in a["bash"] if sec >= slow]
    rows += [(t0, sec, "orchestrator", cmd) for t0, sec, cmd in bash_calls(main_events) if sec >= slow]
    for t0, sec, who, cmd in sorted(rows):
        print(f"  {clock(t0)} {sec:6.0f}s  {who:28s} {cmd[:100]!r}")
    if not rows:
        print("  none")


if __name__ == "__main__":
    main()
