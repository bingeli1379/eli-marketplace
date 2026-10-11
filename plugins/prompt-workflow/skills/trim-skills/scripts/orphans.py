#!/usr/bin/env python3
"""Classify every bundled file under the target paths by how — if at all — it is reached.

Usage: orphans.py <repo> <target-path>... [--exclude <path>]...

Emits one JSON object on stdout. It reads and reports; it changes nothing.

A filename that no other file mentions is not yet an orphan, because three routes reach a
file without spelling its name, and each is checked before the verdict:

  import by module name   `from common import x` loads common.py and never contains the
                          string "common.py". Observed: a shared helper with zero filename
                          hits and three importers.
  dynamic loading         glob / listdir / walk / importlib / a path assembled from a
                          variable (f"fetch_{kind}.py", `${name}.sh`), or prose pointing at
                          a directory rather than a file ("run the scripts in scripts/").
                          The loader line is reported; whether it can actually reach the
                          file — a runtime cache dir vs. the plugin's own tree — is a read,
                          not a regex, and is left to the caller.
  runtime use only        a file the model was told about once and has run since, with
                          nothing in the repo naming it. Transcripts are the only record, and
                          only a tool call's input counts (a Read's file_path, a Bash command):
                          a path in tool output is an `ls` or a diff stat. They rotate, so a
                          zero covers the window reported; and a hit can be a manual read, so
                          this layer can rescue a file but never convict one.

States, first match wins: convention, referenced, dynamic, runtime-only, orphan. A file
named only by files that are themselves unreached is re-classified as unreached, to a fixed
point, with `named_only_by_unreached` listing them: point edits leave chains, and stopping at
the outer link surfaces one layer per run.
Only `orphan` is a deletion candidate; `dynamic` and `runtime-only` need the user's call.

The corpus searched for references is every text file in the repo, not just the targets:
a file in one plugin may be named by another plugin's prose. Upstream-synced paths passed
with --exclude are left out of the candidates but stay in the corpus.
"""
import fnmatch, json, os, re, subprocess, sys

HOME = os.path.expanduser("~")
PROJECTS = os.path.join(HOME, ".claude", "projects")

# Loaded by the harness or a toolchain from where they sit, never by name.
CONVENTION_NAMES = {
    "SKILL.md", "CLAUDE.md", "AGENTS.md", "plugin.json", "hooks.json", ".mcp.json", "mcp.json",
    "package.json", "package-lock.json", "pnpm-lock.yaml", "tsconfig.json", "pyproject.toml",
    "uv.lock", "poetry.lock", "conftest.py", "__init__.py", "__main__.py", "SOURCES.yaml",
    ".gitignore", ".gitattributes", ".DS_Store",
}
CONVENTION_PREFIXES = ("README", "CHANGELOG", "LICENSE", "requirements")
CONVENTION_DIRS = {"agents", "commands", "output-styles", ".claude-plugin", ".codex-plugin",
                   "__pycache__", "node_modules", ".git"}
CODE_EXT = {".py", ".sh", ".bash", ".ts", ".tsx", ".js", ".mjs", ".cjs"}
NAME_TOKEN = re.compile(r"[\w.@+-]+\.[A-Za-z0-9]+")
TEST_RE = re.compile(r"(^test_.*\.py$|_test\.py$|\.test\.[jt]sx?$|\.spec\.[jt]sx?$)")

EXT = r"(?:py|sh|ts|tsx|js|mjs|json|md|ya?ml|sql|txt|csv|toml)"
LOADER_RES = [
    re.compile(r"\.r?glob\(\s*f?[\"']([^\"']*)[\"']"),
    re.compile(r"\bglob(?:\.glob|\.iglob)?\(\s*f?[\"']([^\"']*)[\"']"),
    re.compile(r"\b(?:os\.listdir|os\.scandir|os\.walk|\.iterdir\(|readdirSync|readdir\(|importlib|__import__|runpy)"),
    re.compile(r"\b(?:import|require)\(\s*(?![\"'])[^)\s]"),
    re.compile(r"f[\"']([^\"']*\{[^}]+\}[^\"']*\." + EXT + r")[\"']"),
    re.compile(r"([\w./-]*\$\{?\w+\}?[\w./-]*\." + EXT + r")\b"),
    re.compile(r"(?:\+\s*[\"']\." + EXT + r"[\"']|%s\." + EXT + r")"),
    re.compile(r"(?<![\w$])([\w./-]*\*[\w.*-]*\." + EXT + r")\b"),
    re.compile(r"\$\(\s*ls\b|\bfor\s+\w+\s+in\s+[^;]*\*"),
]

out = {"unavailable": [], "coverage": {}}


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=60)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def read_text(path):
    try:
        with open(path, "rb") as f:
            data = f.read(2_000_000)
        if b"\0" in data[:4096]:
            return None
        return data.decode("utf-8", "replace")
    except Exception:
        return None


def plugin_root(rel):
    parts = rel.split("/")
    return "/".join(parts[:2]) if len(parts) > 2 and parts[0] == "plugins" else ""


def is_convention(rel):
    parts = rel.split("/")
    name = parts[-1]
    return (name in CONVENTION_NAMES or name.startswith(CONVENTION_PREFIXES)
            or bool(TEST_RE.search(name)) or any(p in CONVENTION_DIRS for p in parts[:-1]))


def import_re(stem):
    s = re.escape(stem)
    return re.compile(
        r"^\s*(?:from\s+[\w.]*\b" + s + r"\b|import\s+[\w., ]*\b" + s + r"\b"
        r"|from\s+[\w.]+\s+import\s+[^\n#]*\b" + s + r"\b)"
        r"|(?:from|import|require)\s*\(?\s*[\"'][^\"']*\b" + s + r"(?:\.\w+)?[\"']",
        re.M)


def loader_pattern(line):
    """The glob-shaped part of a loader line, braces flattened to *, or None when the line
    names no pattern at all (listdir, walk, importlib) and so could reach anything."""
    for rx in LOADER_RES:
        m = rx.search(line)
        if not m:
            continue
        pat = m.group(1) if m.groups() and m.group(1) is not None else None
        if pat is None:
            return ("*", True)
        pat = re.sub(r"\$?\{[^}]*\}|\$\w+|%s", "*", pat)
        return (pat.rsplit("/", 1)[-1] or "*", True)
    return (None, False)


def main(argv):
    if len(argv) < 2:
        sys.exit("usage: orphans.py <repo> <target-path>... [--exclude <path>]...")
    repo = os.path.abspath(argv[0])
    targets, excludes, it = [], [], iter(argv[1:])
    for a in it:
        if a == "--exclude":
            excludes.append(next(it))
        else:
            targets.append(a)
    rel = lambda p: os.path.relpath(os.path.abspath(os.path.join(repo, p)), repo)
    targets, excludes = [rel(t) for t in targets], [rel(e) for e in excludes]

    # Untracked-but-not-ignored files count too: --report-only runs on a dirty tree, where a
    # new uncommitted file may be the only thing naming a tracked one.
    tracked = git(repo, "ls-files", "--cached", "--others", "--exclude-standard")
    if tracked is None:
        sys.exit(f"{repo} is not a git working copy")
    files = [f for f in tracked.splitlines() if os.path.isfile(os.path.join(repo, f))]
    corpus = {f: t for f in files if (t := read_text(os.path.join(repo, f))) is not None}

    under = lambda f, roots: any(f == r or f.startswith(r.rstrip("/") + "/") for r in roots)
    candidates = [f for f in files if (targets == ["."] or under(f, targets)) and not under(f, excludes)]

    mentions = {}  # basename -> files whose text contains it as a whole token
    for g, text in corpus.items():
        for tok in set(NAME_TOKEN.findall(text)):
            mentions.setdefault(tok, set()).add(g)

    # Only code that runs can load a file; a loader inside a markdown example is teaching
    # material, and prose pointing at a directory is matched separately below.
    loaders = []  # (file, lineno, line, pattern)
    for f, text in corpus.items():
        if os.path.splitext(f)[1] not in CODE_EXT:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            pat, hit = loader_pattern(line)
            if hit:
                loaders.append((f, n, line.strip()[:200], pat))

    results, pending = [], []
    for f in candidates:
        name = os.path.basename(f)
        stem, parent = os.path.splitext(name)[0], os.path.basename(os.path.dirname(f))
        if is_convention(f):
            results.append({"file": f, "state": "convention"})
            continue
        refs = sorted(mentions.get(name, set()) - {f})
        if not refs and stem and os.path.splitext(name)[1] in CODE_EXT:
            rx = import_re(stem)
            refs = [g for g, t in corpus.items() if g != f and rx.search(t)]
        if refs:
            results.append({"file": f, "state": "referenced", "by": sorted(refs)[:5], "by_count": len(refs),
                            "_refs": set(refs)})
            continue
        results.append(unreached(f, name, parent, loaders, corpus, pending))

    # A file named only by files nothing reaches is unreached too: point edits leave chains,
    # and stopping at the outer link surfaces one layer per run.
    dead = {e["file"] for e, _ in pending if not e["dynamic_loader_count"]}
    changed = True
    while changed:
        changed = False
        for i, r in enumerate(results):
            if r.get("state") == "referenced" and r["_refs"] <= dead:
                f = r["file"]
                name, parent = os.path.basename(f), os.path.basename(os.path.dirname(f))
                e = unreached(f, name, parent, loaders, corpus, pending)
                e["named_only_by_unreached"] = sorted(r["_refs"])[:8]
                results[i] = e
                if not e["dynamic_loader_count"]:
                    dead.add(f)
                    changed = True
    for r in results:
        r.pop("_refs", None)

    scan_transcripts(pending)
    for entry, _ in pending:
        entry["state"] = ("dynamic" if entry["dynamic_loader_count"]
                          else "runtime-only" if entry.get("transcripts") else "orphan")
        entry["last_mention_change"] = git(repo, "log", "-1", "--format=%h %ad %s", "--date=short",
                                           "-S", os.path.basename(entry["file"])) or None
        entry["last_commit"] = git(repo, "log", "-1", "--format=%h %ad %s", "--date=short", "--", entry["file"])

    order = {"orphan": 0, "runtime-only": 1, "dynamic": 2, "referenced": 3, "convention": 4}
    results.sort(key=lambda r: (order[r["state"]], r["file"]))
    out["repo"] = repo
    out["counts"] = {s: sum(r["state"] == s for r in results) for s in order}
    out["files"] = [r for r in results if r["state"] not in ("referenced", "convention")]
    out["referenced_or_convention"] = len(results) - len(out["files"])
    print(json.dumps(out, ensure_ascii=False, indent=1))


def unreached(f, name, parent, loaders, corpus, pending):
    root = plugin_root(f)
    dir_rx =re.compile(r"(?<![\w.-])" + re.escape(parent) + r"/(?![\w.-])") if parent else None
    reach = []
    for g, n, line, pat in loaders:
        if root and plugin_root(g) != root:
            continue
        if pat and fnmatch.fnmatch(name, pat):
            reach.append(f"{g}:{n}: {line}")
    if dir_rx:
        for g, t in corpus.items():
            if g.endswith(".md") and (not root or plugin_root(g) == root) and dir_rx.search(t):
                reach.append(f"{g}: names the directory `{parent}/` without a file")
    entry = {"file": f, "dynamic_loaders": reach[:8], "dynamic_loader_count": len(reach)}
    pending.append((entry, f"{parent}/{name}" if parent else name))
    return entry


def scan_transcripts(pending):
    if not pending:
        return
    if not os.path.isdir(PROJECTS):
        out["unavailable"].append(f"{PROJECTS} missing — runtime-only cannot be told from orphan")
        return
    by_key = {}
    for entry, key in pending:
        by_key.setdefault(key, []).append(entry)
    # Only what a tool call was asked to read or run counts — a path in a tool's OUTPUT is
    # an `ls`, a diff stat, or this very audit printing its findings, not a use.
    tool_args = re.compile(r'"(?:command|file_path|path|notebook_path)"\s*:\s*"((?:[^"\\]|\\.)*)"')
    combined = re.compile("|".join(re.escape(k) for k in sorted(by_key, key=len, reverse=True)))
    ts = re.compile(r'"timestamp"\s*:\s*"(\d{4}-\d\d-\d\d)')
    n, lo, hi = 0, None, None
    for d, _, names in os.walk(PROJECTS):
        for nm in names:
            if not nm.endswith(".jsonl"):
                continue
            text = read_text(os.path.join(d, nm))
            if text is None:
                continue
            n += 1
            dates = ts.findall(text)
            if dates:
                lo = min(lo or dates[0], min(dates))
                hi = max(hi or dates[-1], max(dates))
            hits = set()
            for arg in tool_args.findall(text):
                hits.update(combined.findall(arg))
            for key in hits:
                for entry in by_key[key]:
                    entry["transcripts"] = entry.get("transcripts", 0) + 1
    out["coverage"] = {"transcript_files": n, "window_start": lo, "window_end": hi}


if __name__ == "__main__":
    main(sys.argv[1:])
