#!/usr/bin/env python3
"""Collect the installed inventory and the observed usage for a toolset audit.

Emits one JSON object on stdout. It measures and reports; it changes nothing.

Sources, and why more than one is needed — each is incomplete on its own:

  ~/.claude.json  skillUsage    lifetime per-skill counts. Used skills ONLY: it holds no
                                zero-count entry, so it is a numerator and can never
                                supply the "installed but never fired" set.
                  toolUsage     built-in tools only, and observed stale. Not relied on.
                  mcpServers    user-scoped MCP servers (the denominator's first part).
                  projects[]    per-project mcpServers / enabledMcpjsonServers (second part).
  installed_plugins.json        the authoritative installed set: <plugin>@<marketplace> and the
                                installPath of the version in force. The marketplaces/ tree is a
                                catalogue of what is OFFERED, so it is never scanned.
  <installPath>/.mcp.json       MCP servers shipped by installed plugins (third part) — these
                                never appear in ~/.claude.json, and the manifest is `.mcp.json`
                                or `mcp.json`, wrapped in "mcpServers" or not.
  ~/.claude/projects/**/*.jsonl transcripts: the only per-MCP-tool call record, plus the
                                recency and per-project spread the counters do not carry.
                                Rotated, so its counts are a recent window, not a lifetime.

These are Claude Code internals and may be renamed by a release. Every one is read
defensively: a missing source is reported in `unavailable`, never silently skipped.
"""
import json, os, re, sys, glob
from collections import Counter, defaultdict

HOME = os.path.expanduser("~")
CONFIG = os.path.join(HOME, ".claude.json")
PROJECTS = os.path.join(HOME, ".claude", "projects")

out = {"unavailable": [], "coverage": {}}


def load_config():
    try:
        with open(CONFIG) as f:
            return json.load(f)
    except Exception as e:
        out["unavailable"].append(f"~/.claude.json unreadable ({e.__class__.__name__})")
        return {}


cfg = load_config()

# ---- skills: lifetime counts (numerator only — no zero entries exist here) ----
skill_usage = cfg.get("skillUsage")
if skill_usage is None:
    out["unavailable"].append("skillUsage key absent — skill counts unavailable")
    skill_usage = {}
out["skills_used"] = {
    k: {"count": v.get("usageCount", 0), "last_used_ms": v.get("lastUsedAt")}
    for k, v in skill_usage.items()
}

# ---- what is actually installed ----
# `installed_plugins.json` is the authority, and the only one. The `marketplaces/` tree is the
# catalogue of everything a marketplace OFFERS, installed or not, so scanning it reports plugins
# the user never installed as unused and recommends removing what they do not have. Each entry
# keys on `<plugin>@<marketplace>` and carries the `installPath` of the version in force, which
# also removes any need to pick a version out of the cache by hand.
INSTALLED = os.path.join(HOME, ".claude", "plugins", "installed_plugins.json")
plugins = {}          # "<plugin>@<marketplace>" -> {"plugin","marketplace","path"}
try:
    with open(INSTALLED) as f:
        for key, entries in (json.load(f).get("plugins") or {}).items():
            entry = entries[0] if isinstance(entries, list) and entries else entries
            if not isinstance(entry, dict) or not entry.get("installPath"):
                continue
            name, _, market = key.partition("@")
            plugins[key] = {"plugin": name, "marketplace": market, "path": entry["installPath"]}
except Exception as e:
    out["unavailable"].append(
        f"installed_plugins.json unreadable ({e.__class__.__name__}) — nothing can be called unused, "
        "since the installed set is unknown")
# The `description` of every installed skill sits in context on every request, while its body is
# lazy-loaded — so a skill that never fires costs its description length, every turn, forever.
# That length is the cost of keeping it, and it is what a prune should be ranked by: a plugin with
# thirty terse skills can be cheaper than one with six verbose ones.
FRONTMATTER = re.compile(r"^---\s*$(.*?)^---\s*$", re.S | re.M)
DESCRIPTION = re.compile(r"^description:\s*(.*?)(?=^\w+:|\Z)", re.S | re.M)


def description_chars(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            block = FRONTMATTER.search(f.read())
        if not block:
            return 0
        found = DESCRIPTION.search(block.group(1))
        return len(found.group(1).strip()) if found else 0
    except Exception:
        return 0


skills_installed = {}
for key, meta in plugins.items():
    for path in glob.glob(os.path.join(meta["path"], "skills", "*", "SKILL.md")):
        name = f'{meta["plugin"]}:{os.path.basename(os.path.dirname(path))}'
        skills_installed[name] = {"owner": key, "description_chars": description_chars(path)}
for path in glob.glob(os.path.join(HOME, ".claude", "skills", "*", "SKILL.md")):
    skills_installed.setdefault(os.path.basename(os.path.dirname(path)),
                                {"owner": "(personal)", "description_chars": description_chars(path)})
if not skills_installed:
    out["unavailable"].append(
        "no SKILL.md found under any install path — skills reported usage-only, unused ones cannot be named")
out["skills_installed"] = skills_installed

# ---- MCP servers declared: user scope + project scope + plugin-shipped ----
# Each entry records the scope AND the concrete place it came from, because the scope alone does
# not tell the reader how to remove it: "project" is unactionable until you know which project,
# and "plugin" until you know which plugin under which marketplace.
declared = {}
for name in (cfg.get("mcpServers") or {}):
    declared[name] = {"scope": "user", "where": "~/.claude.json"}
for proj, pcfg in (cfg.get("projects") or {}).items():
    for name in (pcfg.get("mcpServers") or {}):
        declared.setdefault(name, {"scope": "project", "where": proj})
    for name in (pcfg.get("enabledMcpjsonServers") or []):
        declared.setdefault(name, {"scope": "project", "where": proj})
def plugin_servers(plugin_dir):
    """Server names a plugin declares, across the manifest shapes seen in practice: the file is
    `.mcp.json` or `mcp.json`, and its contents are either {"mcpServers": {...}} or the server map
    itself. Assuming one shape drops the others silently — they simply never appear in the
    denominator, which reads exactly like a plugin that ships no MCP server at all."""
    for fn in (".mcp.json", "mcp.json"):
        path = os.path.join(plugin_dir, fn)
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            j = json.load(f)
        if not isinstance(j, dict):
            raise ValueError("manifest is not an object")
        inner = j.get("mcpServers")
        if isinstance(inner, dict):
            return list(inner), path
        # a bare map: values are server configs, recognised by the keys a config carries
        if all(isinstance(v, dict) and ({"command", "url", "type"} & set(v)) for v in j.values()) and j:
            return list(j), path
        raise ValueError(f"unrecognised manifest shape, top-level keys: {sorted(j)[:5]}")
    return [], None


for key, meta in plugins.items():
    try:
        names, path = plugin_servers(meta["path"])
    except Exception as e:
        out["unavailable"].append(
            f"{key}: MCP manifest unreadable ({e}) — its servers are missing from the declared set")
        continue
    for name in names:
        declared.setdefault(name, {"scope": "plugin", "where": meta["path"],
                                   "plugin": meta["plugin"],
                                   "marketplace": meta["marketplace"]})

# `declared` stays internal: `mcp_servers` below is the only shape the report consumes.

# ---- transcripts: per-tool calls, recency, project spread ----
files = glob.glob(os.path.join(PROJECTS, "**", "*.jsonl"), recursive=True)
if not files:
    out["unavailable"].append("no transcripts under ~/.claude/projects — MCP tool counts unavailable")

TOOL_RE = re.compile(r'"name":"(mcp__[^"]+)"')
tool_counts = Counter()
tool_projects = defaultdict(set)
mtimes = []
for path in files:
    project = os.path.basename(os.path.dirname(path))
    try:
        mtimes.append(os.path.getmtime(path))
        with open(path, errors="replace") as f:
            for line in f:
                if "mcp__" not in line:
                    continue
                for name in TOOL_RE.findall(line):
                    tool_counts[name] += 1
                    tool_projects[name].add(project)
    except Exception:
        out["unavailable"].append(f"unreadable transcript: {path}")

def canonical_server(raw):
    """A plugin-shipped server appears in a tool name as `plugin_<plugin>_<server>` while the
    manifest declares it as `<server>`. Left unnormalized, every plugin MCP server looks
    both undeclared and unused at once."""
    return raw.split("_", 2)[2] if raw.startswith("plugin_") and raw.count("_") >= 2 else raw


tools_observed = {
    name: {
        "count": c,
        "projects": len(tool_projects[name]),
        "server": canonical_server(name.split("__")[1]),
    }
    for name, c in tool_counts.items()
}

# server-level roll-up: the only granularity where both halves exist. A declared server's
# individual tools are knowable only by connecting to it, so a tool that never fired cannot
# be named — only a server that never fired can.
server_counts = Counter()
for name, meta in tools_observed.items():
    server_counts[meta["server"]] += meta["count"]
# A project-scoped server is only loaded inside its own project, so its call count is only
# evidence if the window actually contains sessions from there. Zero calls over a window with
# zero sessions says nothing at all — and reads identically to a server nobody wants.
for name, meta in declared.items():
    if meta.get("scope") != "project":
        continue
    # Ask first whether the project itself still exists. A declaration pointing at a directory
    # that is absent cannot load while it stays absent, so its zero is a verdict — dead config left
    # behind in ~/.claude.json — not a measurement gap. It says nothing about WHY the path is gone:
    # a deleted project and an unmounted volume look identical from here, so the report states the
    # absence and leaves the cause to the user who knows it. Without this
    # the run reports "cannot be measured" for something decidable by one stat call, and hands
    # over a removal command that cannot even run (there is no directory to cd into).
    meta["project_exists"] = os.path.isdir(meta["where"])
    # The transcript directory is the project path with its separators replaced, so build the
    # slug from whatever separator this platform uses rather than assuming "/". When no such
    # directory exists the count is unknowable, NOT zero: reporting 0 there is indistinguishable
    # from a project genuinely never opened, and would retire a server on evidence never taken.
    slug = re.sub(r"[\\/:]", "-", meta["where"])
    project_dir = os.path.join(PROJECTS, slug)
    if os.path.isdir(project_dir):
        meta["project_sessions"] = len(glob.glob(os.path.join(project_dir, "*.jsonl")))
    else:
        meta["project_sessions"] = None
        if meta["project_exists"]:
            out["unavailable"].append(
                f"no transcript directory for {meta['where']} — server '{name}' cannot be measured, "
                "so it gets no verdict")

out["mcp_servers"] = {
    s: {
        "count": server_counts.get(s, 0),
        **declared.get(s, {"scope": "observed", "where": None}),
    }
    for s in set(declared) | set(server_counts)
}
out["coverage"] = {
    "transcript_files": len(files),
    "oldest_mtime": min(mtimes) if mtimes else None,
    "newest_mtime": max(mtimes) if mtimes else None,
}

# ---- rollup: everything the report renders, computed once and here ----
# The per-plugin arithmetic is the same every run, so it belongs in the script rather than being
# re-derived per run — the same reason the collection is not composed inline. What is left to
# judgement is which recommendation a row earns, not how many skills or characters it holds.
CHARS_PER_TOKEN = 3.5     # rough, and only ever used for an order-of-magnitude comparison

fired = {name for name in out["skills_used"] if name in skills_installed}
personal_fired = {n for n in fired if skills_installed[n]["owner"] == "(personal)"}

server_calls_by_plugin = {}
for meta in out["mcp_servers"].values():
    if meta.get("scope") == "plugin":
        key = f'{meta["plugin"]}@{meta["marketplace"]}'
        server_calls_by_plugin[key] = server_calls_by_plugin.get(key, 0) + meta["count"]

rollup = {}
for name, meta in skills_installed.items():
    owner = meta["owner"]
    row = rollup.setdefault(owner, {"installed": 0, "never_fired": 0, "description_chars": 0,
                                    "shadowed_by_personal": 0,
                                    "server_calls": server_calls_by_plugin.get(owner, 0)})
    row["installed"] += 1
    if name in fired:
        continue
    row["never_fired"] += 1
    row["description_chars"] += meta["description_chars"]
    # a plugin skill whose bare name is also installed personally, where that copy is the one firing
    if owner != "(personal)" and name.split(":")[-1] in personal_fired:
        row["shadowed_by_personal"] += 1

for row in rollup.values():
    row["approx_tokens"] = round(row["description_chars"] / CHARS_PER_TOKEN)
out["rollup_by_plugin"] = dict(
    sorted(rollup.items(), key=lambda kv: -kv[1]["description_chars"]))

all_chars = sum(m["description_chars"] for m in skills_installed.values())
dead_chars = sum(r["description_chars"] for r in rollup.values())
out["description_cost"] = {
    "installed_skills": len(skills_installed),
    "never_fired_skills": len(skills_installed) - len(fired),
    "all_chars": all_chars,
    "never_fired_chars": dead_chars,
    "all_approx_tokens": round(all_chars / CHARS_PER_TOKEN),
    "never_fired_approx_tokens": round(dead_chars / CHARS_PER_TOKEN),
    "never_fired_pct": round(dead_chars * 100 / all_chars) if all_chars else 0,
    "chars_per_token": CHARS_PER_TOKEN,
    "orphan_recorded_names": len([n for n in out["skills_used"] if n not in skills_installed]),
}

json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
