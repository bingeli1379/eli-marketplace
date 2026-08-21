#!/usr/bin/env python3
"""Collect the installed inventory and the observed usage for a toolset audit.

Emits one JSON object on stdout. It measures and reports; it changes nothing.

Sources, and why more than one is needed — each is incomplete on its own:

  ~/.claude.json  skillUsage    lifetime per-skill counts. Used skills ONLY: it holds no
                                zero-count entry, so it is a numerator and can never
                                supply the "installed but never fired" set.
                  pluginUsage   installed plugins WITH zero-count entries — a real
                                denominator, but only down to the plugin, not the skill.
                  toolUsage     built-in tools only, and observed stale. Not relied on.
                  mcpServers    user-scoped MCP servers (the denominator's first part).
                  projects[]    per-project mcpServers / enabledMcpjsonServers (second part).
  plugin dirs     .mcp.json     MCP servers shipped by installed plugins (third part) —
                                these never appear in ~/.claude.json.
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
PLUGIN_ROOTS = [os.path.join(HOME, ".claude", "plugins")]

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

# ---- plugins: installed set WITH zero-count entries (a real denominator) ----
plugin_usage = cfg.get("pluginUsage")
if plugin_usage is None:
    out["unavailable"].append("pluginUsage key absent — unused plugins cannot be named")
    plugin_usage = {}
out["plugins_installed"] = {
    k: {"count": v.get("usageCount", 0), "last_used_ms": v.get("lastUsedAt")}
    for k, v in plugin_usage.items()
}

# ---- skills installed: read off disk, since skillUsage holds no zero-count entry ----
# Cache layout is <root>/cache/<marketplace>/<plugin>/<version>/skills/<skill>/SKILL.md, and
# every previously installed version is kept. Counting the tree as-is multiplies each skill by
# its version history, so only the newest version of each plugin is counted.
def parse_version(v):
    parts = []
    for chunk in v.split("."):
        parts.append(int(chunk) if chunk.isdigit() else -1)
    return parts


newest = {}   # (marketplace, plugin) -> (version_key, version_dir)
for root in PLUGIN_ROOTS:
    for vdir in glob.glob(os.path.join(root, "cache", "*", "*", "*")):
        if not os.path.isdir(os.path.join(vdir, "skills")):
            continue
        version = os.path.basename(vdir)
        plugin = os.path.basename(os.path.dirname(vdir))
        market = os.path.basename(os.path.dirname(os.path.dirname(vdir)))
        key = parse_version(version)
        if newest.get((market, plugin), ([-1], None))[0] < key:
            newest[(market, plugin)] = (key, vdir)

skills_installed = {}
for (market, plugin), (_, vdir) in newest.items():
    for path in glob.glob(os.path.join(vdir, "skills", "*", "SKILL.md")):
        skills_installed[f"{plugin}:{os.path.basename(os.path.dirname(path))}"] = path
for path in glob.glob(os.path.join(HOME, ".claude", "skills", "*", "SKILL.md")):
    skills_installed.setdefault(os.path.basename(os.path.dirname(path)), path)
if not skills_installed:
    out["unavailable"].append(
        "no SKILL.md found on disk — skills reported usage-only, unused ones cannot be named")
out["skills_installed"] = sorted(skills_installed)

# ---- MCP servers declared: user scope + project scope + plugin-shipped ----
declared = {}
for name in (cfg.get("mcpServers") or {}):
    declared[name] = "user"
for proj, pcfg in (cfg.get("projects") or {}).items():
    for name in (pcfg.get("mcpServers") or {}):
        declared.setdefault(name, "project")
    for name in (pcfg.get("enabledMcpjsonServers") or []):
        declared.setdefault(name, "project")

plugin_mcp_found = False
for root in PLUGIN_ROOTS:
    for path in glob.glob(os.path.join(root, "**", ".mcp.json"), recursive=True):
        plugin_mcp_found = True
        try:
            with open(path) as f:
                for name in (json.load(f).get("mcpServers") or {}):
                    declared.setdefault(name, "plugin")
        except Exception:
            out["unavailable"].append(f"unparsable plugin MCP manifest: {path}")
if not plugin_mcp_found:
    out["unavailable"].append(
        "no plugin-shipped .mcp.json found — plugin MCP servers may be declared elsewhere; "
        "servers seen only in transcripts are reported as source 'observed'"
    )
out["mcp_declared"] = declared

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


out["mcp_tools_observed"] = {
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
for name, meta in out["mcp_tools_observed"].items():
    server_counts[meta["server"]] += meta["count"]
out["mcp_servers"] = {
    s: {"count": server_counts.get(s, 0), "source": declared.get(s, "observed")}
    for s in set(declared) | set(server_counts)
}
out["coverage"] = {
    "transcript_files": len(files),
    "oldest_mtime": min(mtimes) if mtimes else None,
    "newest_mtime": max(mtimes) if mtimes else None,
}

json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
