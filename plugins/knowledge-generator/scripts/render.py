#!/usr/bin/env python3
"""Render a generated knowledge base from the bundled templates and a config file.

    render.py --config knowledge.config.json            validate, and list what a render would do
    render.py --config knowledge.config.json --write    apply it

Without --write nothing is written: the config is validated and the run prints a one-line
summary, the user-owned files it would keep, and a diff for every generated file that
differs from what a render would write. The output goes to <paths.repo>/<paths.out>, except the maintainer kit,
which always lands in <paths.repo>/.claude/ because Claude Code loads project skills from there.

Template syntax. It is strict: an unknown name is an error, never an empty string.
    {{ a.b.c }}                          value from the config or the derived context
    {{#if x}} .. {{else}} .. {{/if}}     x is truthy when not empty, not false and not "none"
    {{#unless x}} .. {{/unless}}
    {{#each list}} {{ this.f }} {{/each}}
    \\{{ ... }}                           literal braces
A block tag alone on its line removes the whole line.
In file paths __prefix__ is replaced by identity.prefix, and a .tmpl suffix is dropped.
A template under kit/ is written under <paths.repo>/.claude/ instead of <paths.out>.
A .seed.tmpl is a file the user owns: it is written when missing and never overwritten.
A template that renders to nothing but whitespace is not written;
that is how a whole file is switched off (wrap the whole file in {{#if has.skeleton_x}}).
A generated file may mark one region the user fills in, between "<!-- keep -->" and "<!-- /keep -->" lines;
a render carries the existing content of that region over instead of replacing it.
"""
import argparse
import collections
import difflib
import json
import os
import posixpath
import re
import sys
from pathlib import Path

TAG = re.compile(r"(\\)?\{\{\s*(.*?)\s*\}\}", re.S)
KEEP = re.compile(r"(<!-- keep -->\n)(.*?)(<!-- /keep -->)", re.S)
BLOCK = re.compile(r"^(#(if|unless|each)\s+\S+|else|/(if|unless|each))$")
OPEN = re.compile(r"#(if|unless|each)\s+(\S+)$")
CLOSE = re.compile(r"/(if|unless|each)$")

TOP_KEYS = {
    "config_version", "identity", "paths", "git", "scope",
    "environments", "stack", "capabilities", "reader", "known_context", "audit", "kit",
}
DESCRIPTION_CAP = 1024
KIND_LABELS = {
    "elk": "ELK", "loki": "Loki", "cloudwatch": "CloudWatch", "grafana": "Grafana", "datadog": "Datadog",
    "confluence": "Confluence", "notion": "Notion", "wiki": "wiki",
}
PLATFORM_BASICS = {
    "time": ("Time", "time zone of servers and databases, date conventions"),
    "environments": ("Environments", "which environments exist, and which share data or infrastructure"),
    "domains": ("Domains", "how hosts and domains map to services, and how they are named per environment"),
    "deployment": ("Deployment", "how releases reach each runtime, including any manual or out-of-band step"),
    "clusters": ("Clusters", "which platforms or clusters services run on, and how services reach each other"),
    "config-store": ("Settings store", "where platform settings live and how to read one"),
    "cache": ("Cache", "which cache clusters exist, and that each project doc records its own"),
    "cdn": ("CDN", "where assets are served from, and the authoritative list"),
    "shared-libraries": ("Shared libraries", "the kinds of shared code and which one to install when"),
    "organization": ("Organization", "teams, what each owns, and legacy names still found in config"),
    "cross-team": ("Cross-team work", "how to change code that another team owns"),
    "db-conventions": ("Database conventions", "naming, versioning and append-only rules that keep a recorded reference durable"),
    "db-schema-location": ("Database schema", "which repository holds the schema for each database"),
}
CAPABILITIES = ("logs", "metrics", "global_settings", "db_schema", "external_reference")
STACK_AREAS = ("frontend", "runtime", "database", "messaging")
SKELETONS = ("service", "legacy-vm", "artifact")


class TemplateError(Exception):
    pass


class ConfigError(Exception):
    pass


def line_of(src, pos):
    return src.count("\n", 0, pos) + 1


def tokenize(src):
    tokens, pos = [], 0
    for m in TAG.finditer(src):
        start, end = m.span()
        if m.group(1):
            tokens.append(("text", src[pos:start] + m.group(0)[1:]))
            pos = end
            continue
        expr = m.group(2)
        ln = line_of(src, start)
        if BLOCK.match(expr):
            ls = src.rfind("\n", 0, start) + 1
            le = src.find("\n", end)
            le = len(src) if le == -1 else le
            if not src[ls:start].strip() and not src[end:le].strip():
                tokens.append(("text", src[pos:ls]))
                tokens.append(("tag", expr, ln))
                pos = min(le + 1, len(src))
                continue
        tokens.append(("text", src[pos:start]))
        tokens.append(("tag", expr, ln))
        pos = end
    tokens.append(("text", src[pos:]))
    return tokens


def parse(tokens, name):
    stack = [{"kind": "root", "body": [], "alt": [], "in_alt": False, "line": 0}]

    def cur(frame):
        return frame["alt"] if frame["in_alt"] else frame["body"]

    for tok in tokens:
        if tok[0] == "text":
            if tok[1]:
                cur(stack[-1]).append(("text", tok[1]))
            continue
        _, expr, ln = tok
        m = OPEN.match(expr)
        if m:
            stack.append({"kind": m.group(1), "path": m.group(2), "body": [], "alt": [],
                          "in_alt": False, "line": ln})
            continue
        if expr == "else":
            frame = stack[-1]
            if frame["kind"] not in ("if", "unless") or frame["in_alt"]:
                raise TemplateError(f"{name}:{ln}: unexpected else")
            frame["in_alt"] = True
            continue
        m = CLOSE.match(expr)
        if m:
            frame = stack.pop()
            if frame["kind"] != m.group(1):
                raise TemplateError(f"{name}:{ln}: /{m.group(1)} does not match {frame['kind']}")
            cur(stack[-1]).append((frame["kind"], frame["path"], frame["body"], frame["alt"], frame["line"]))
            continue
        cur(stack[-1]).append(("var", expr, ln))
    if len(stack) != 1:
        raise TemplateError(f"{name}:{stack[-1]['line']}: unclosed {stack[-1]['kind']}")
    return stack[0]["body"]


def lookup(path, scopes, name, ln):
    parts = path.split(".")
    if parts[0] == "this":
        if len(scopes) < 2:
            raise TemplateError(f"{name}:{ln}: 'this' used outside #each")
        node, parts = scopes[-1], parts[1:]
    else:
        node = scopes[0]
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            raise TemplateError(f"{name}:{ln}: unknown name {path!r}")
    return node


def truthy(value):
    return value not in (None, False, "", [], {}) and value != "none"


def render_nodes(nodes, scopes, name):
    out = []
    for node in nodes:
        kind = node[0]
        if kind == "text":
            out.append(node[1])
        elif kind == "var":
            value = lookup(node[1], scopes, name, node[2])
            if isinstance(value, (dict, list)):
                raise TemplateError(f"{name}:{node[2]}: {node[1]!r} is not a scalar")
            out.append(("true" if value else "false") if isinstance(value, bool) else str(value))
        elif kind in ("if", "unless"):
            _, path, body, alt, ln = node
            flag = truthy(lookup(path, scopes, name, ln))
            out.append(render_nodes(body if (flag != (kind == "unless")) else alt, scopes, name))
        else:
            _, path, body, alt, ln = node
            if alt:
                raise TemplateError(f"{name}:{ln}: else is not allowed in #each")
            items = lookup(path, scopes, name, ln)
            if not isinstance(items, list):
                raise TemplateError(f"{name}:{ln}: {path!r} is not a list")
            for item in items:
                out.append(render_nodes(body, scopes + [item], name))
    return "".join(out)


def render(src, ctx, name="<template>"):
    return render_nodes(parse(tokenize(src), name), [ctx], name)


def validate(cfg):
    errs = []
    if not isinstance(cfg, dict):
        raise ConfigError("config must be a JSON object")
    for key in sorted(set(cfg) - TOP_KEYS):
        errs.append(f"unknown top-level key {key!r}")
    for key in sorted(TOP_KEYS - set(cfg)):
        errs.append(f"missing top-level key {key!r}")
    if errs:
        raise ConfigError("; ".join(errs))

    def need(path):
        node = cfg
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                errs.append(f"missing {path}")
                return None
            node = node[part]
        if node in ("", None, [], {}):
            errs.append(f"empty {path}")
        return node

    prefix = need("identity.prefix")
    if isinstance(prefix, str) and not re.fullmatch(r"[a-z][a-z0-9-]*", prefix):
        errs.append("identity.prefix must match [a-z][a-z0-9-]*")
    for path in ("identity.display_name", "paths.repo", "paths.out", "paths.repos_root", "git.host",
                 "git.user_label", "scope.rule", "scope.owner_source", "scope.audience", "environments.names"):
        need(path)
    rule = cfg["scope"].get("rule")
    if isinstance(rule, str) and rule.strip() and not re.search(r"[.!?\u3002\uff01\uff1f][\"')\uff09]*$", rule.strip()):
        errs.append("scope.rule must be a sentence ending in a full stop; the templates continue after it")
    for entry in (cfg["scope"].get("audience") or []):
        if not isinstance(entry.get("deployed"), bool):
            errs.append(f"scope.audience[{entry.get('slug')}].deployed must be true or false")
    for area in STACK_AREAS:
        if not isinstance(cfg["stack"].get(area), dict) or not isinstance(cfg["stack"][area].get("presets"), list):
            errs.append(f"stack.{area}.presets must be a list")
    for name in cfg["stack"].get("skeletons") or []:
        if name not in SKELETONS:
            errs.append(f"stack.skeletons: unknown skeleton {name!r}")
    if not errs:
        wanted = effective_skeletons(cfg)
        deployed = {a.get("deployed") for a in cfg["scope"].get("audience") or []}
        if "artifact" in wanted and False not in deployed:
            errs.append("scope.audience needs an entry with deployed false for the artifact template; "
                        "add one, or list only the other skeletons in stack.skeletons")
        if any(s in wanted for s in ("service", "legacy-vm")) and True not in deployed:
            errs.append("scope.audience needs an entry with deployed true for the service and legacy-vm templates")
    need("scope.owners")
    reader = cfg["reader"]
    for key in ("example_projects", "example_flows", "example_questions"):
        if not isinstance(reader.get(key), list):
            errs.append(f"reader.{key} must be a list (it may be empty)")
    caps = need("capabilities") or {}
    for cap in CAPABILITIES:
        if not isinstance(caps.get(cap), dict) or "kind" not in caps[cap]:
            errs.append(f"capabilities.{cap}.kind is required (use \"none\" to turn it off)")
    settings = caps.get("global_settings")
    if isinstance(settings, dict) and settings.get("kind") not in ("none", "", None) and not settings.get("lookup"):
        errs.append("capabilities.global_settings.lookup must say how to read a live value when kind is not \"none\"")
    db_map = (caps.get("db_schema") or {}).get("map", [])
    if not isinstance(db_map, list) or any(not isinstance(e, dict) or not e.get("db") or not e.get("repo") for e in db_map):
        errs.append("capabilities.db_schema.map must be a list of { db, repo } entries (it may be empty)")
    if not isinstance(caps.get("shared_catalogs"), list):
        errs.append("capabilities.shared_catalogs must be a list")
    tools = caps.get("tools", [])
    if not isinstance(tools, list):
        errs.append("capabilities.tools must be a list (it may be empty or absent)")
    else:
        for i, tool in enumerate(tools):
            label = f"capabilities.tools[{i}]"
            if not isinstance(tool, dict):
                errs.append(f"{label} must be an object")
                continue
            if isinstance(tool.get("name"), str) and tool["name"].strip():
                label += f" ({' '.join(tool['name'].split())})"
            for key in ("name", "purpose"):
                if not isinstance(tool.get(key), str) or not tool[key].strip():
                    errs.append(f"{label}.{key} is required")
            for key in ("access", "project_identity"):
                if key in tool and not isinstance(tool[key], str):
                    errs.append(f"{label}.{key} must be a string")
            for key in ("name", "purpose", "access", "project_identity"):
                if isinstance(tool.get(key), str) and re.search(r"[|\r\n]", tool[key]):
                    errs.append(f"{label}.{key} must not contain | or a line break (it is written into a table row)")
    if errs:
        raise ConfigError("; ".join(errs))


def other_tools(caps):
    """The entries of capabilities.tools, normalised so templates never test a missing key."""
    out = []
    for tool in caps.get("tools") or []:
        access = (tool.get("access") or "").strip()
        live = access.lower() not in ("", "none")
        identity = (tool.get("project_identity") or "").strip()
        out.append({
            "name": tool["name"].strip(),
            "purpose": tool["purpose"].strip(),
            "live": live,
            "reach": f"the `{access}` MCP" if live else "no connected tool",
            "identity": identity,
            "find": identity or "not recorded per project",
            "access": access if live else "none",
        })
    return out


def stack_on(entry):
    return any(p != "none" for p in entry["presets"]) or bool(entry["other"])


def effective_skeletons(cfg):
    """An empty stack.skeletons derives from the runtime; artifact is always offered."""
    if cfg["stack"]["skeletons"]:
        return list(cfg["stack"]["skeletons"])
    runtime = cfg["stack"]["runtime"]["presets"]
    out = []
    if any(r in runtime for r in ("kubernetes", "serverless", "paas")):
        out.append("service")
    if "vm" in runtime:
        out.append("legacy-vm")
    return out + ["artifact"]


def join_and(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def reader_description(cfg, has, observability_tools):
    """The reader skill is the one model-selectable skill, so its description is the trigger."""
    name = cfg["identity"]["display_name"]
    reader = cfg["reader"]
    teams = [o["label"] for o in cfg["scope"]["owners"] if o["reachable"]]
    head = f"{name} project and business-flow knowledge"
    if teams:
        head += f" across the {join_and(teams)} {'team' if len(teams) == 1 else 'teams'}"
    projects = f" ({', '.join(reader['example_projects'])})" if reader["example_projects"] else ""
    flows = f" ({', '.join(reader['example_flows'])})" if reader["example_flows"] else ""
    asks = "architecture, dependencies, deployment, environments, or cross-project conventions"
    if has["observability_doc"]:
        asks += f", or how to investigate it through {observability_tools}"
    text = (
        f"{head}. Use when developing, debugging, reviewing, or planning any {name} project{projects} "
        f"or flow{flows}; when the user names a project, team, or flow of {name}; or asks about its {asks}"
    )
    if reader["example_questions"]:
        text += " — " + ", ".join(f"\"{q}\"" for q in reader["example_questions"])
    text += "."
    if len(text) > DESCRIPTION_CAP:
        raise ConfigError(
            f"the reader skill description is {len(text)} characters, over the {DESCRIPTION_CAP} cap; "
            "shorten reader.example_projects, reader.example_flows or reader.example_questions"
        )
    return text


def platform_basics(slugs, has_catalogs):
    out = []
    for slug in slugs:
        label, hint = PLATFORM_BASICS.get(slug, (slug.replace("-", " ").capitalize(), "<fact>"))
        if slug == "cache" and not has_catalogs:
            hint = "which cache clusters exist"
        out.append({"slug": slug, "label": label, "hint": hint})
    return out


def derive(cfg):
    """Everything the config implies, so templates never compute anything themselves."""
    prefix = cfg["identity"]["prefix"]
    caps = cfg["capabilities"]
    base = f"{prefix}-knowledge"
    repo = cfg["paths"]["repo"].rstrip("/")
    out_rel = posixpath.normpath(cfg["paths"]["out"])
    ctx = dict(cfg)
    ctx["names"] = {
        "knowledge": base,
        "authoring_core": f"{base}-authoring-core",
        "local_rules": f"{base}-local-rules",
        "add_project": f"{base}-add-project",
        "add_domain": f"{base}-add-domain",
        "sync_local": f"{base}-sync-local",
        "verify": f"{base}-verify",
        "list_markers": f"{base}-list-markers",
    }
    ctx["has"] = {
        name: caps[name]["kind"] not in ("none", "") for name in CAPABILITIES
    }
    ctx["has"]["shared_catalogs"] = bool(caps["shared_catalogs"])
    ctx["has"].update({area: stack_on(cfg["stack"][area]) for area in STACK_AREAS})
    runtime = cfg["stack"]["runtime"]["presets"]
    ctx["has"]["kubernetes"] = "kubernetes" in runtime
    ctx["has"]["vm"] = "vm" in runtime
    skeletons = effective_skeletons(cfg)
    for name in SKELETONS:
        ctx["has"]["skeleton_" + name.replace("-", "_")] = name in skeletons
    ctx["has"]["db_projects"] = caps["db_schema"]["kind"] == "repo-per-db"
    ctx["has"]["observability_doc"] = ctx["has"]["logs"] or ctx["has"]["metrics"]
    ctx["has"]["deployed_skeleton"] = ctx["has"]["skeleton_service"] or ctx["has"]["skeleton_legacy_vm"]
    extra_tools = other_tools(caps)
    ctx["has"]["tools"] = bool(extra_tools)
    ctx["has"]["tool_identity"] = any(t["identity"] for t in extra_tools)
    ctx["has"]["tools_live"] = any(t["live"] for t in extra_tools)
    ctx["has"]["observability_section"] = ctx["has"]["observability_doc"] or ctx["has"]["tool_identity"]
    ctx["has"]["observability_file"] = (
        ctx["has"]["observability_doc"] or ctx["has"]["db_projects"] or ctx["has"]["tools"]
    )
    # the live tools a verification step can name; dashboards (metrics) are not one of them
    ctx["has"]["live_tools"] = ctx["has"]["tools_live"] or any(
        ctx["has"][name] for name in ("logs", "global_settings", "external_reference")
    )
    # a project doc only consults a live tool that names a project identity
    ctx["has"]["project_live_tools"] = any(
        ctx["has"][name] for name in ("logs", "global_settings", "external_reference")
    ) or any(t["live"] and t["identity"] for t in extra_tools)
    ctx["has"]["excluded_envs"] = bool(cfg["environments"]["exclude"])
    ctx["has"]["owner_source"] = cfg["scope"]["owner_source"] != "none"
    audience = cfg["scope"]["audience"]
    names = cfg["environments"]["names"]
    ctx["lists"] = {
        "owners": " | ".join([o["code"] if o["code"] == o["label"] else f"{o['code']} ({o['label']})" for o in cfg["scope"]["owners"]] + ["unknown"]),
        "audiences_deployed": " | ".join(a["slug"] for a in audience if a["deployed"]),
        "audiences_artifact": " | ".join(a["slug"] for a in audience if not a["deployed"]),
        "audience_meanings_deployed": "; ".join(f"{a['slug']} = {a['meaning']}" for a in audience if a["deployed"]),
        "audience_meanings_artifact": "; ".join(f"{a['slug']} = {a['meaning']}" for a in audience if not a["deployed"]),
        "env_names": ", ".join(names),
        "env_excluded": ", ".join(cfg["environments"]["exclude"]),
    }
    labels = {n: KIND_LABELS.get(caps[n]["kind"], caps[n]["kind"]) for n in CAPABILITIES}
    obs = [labels[n] for n in ("logs", "metrics") if ctx["has"][n]]
    tools = " and ".join(obs)
    owners = cfg["scope"]["owners"]
    ctx["has"]["owners_external"] = any(not o["reachable"] for o in owners)
    ctx["lists"]["skeletons"] = " / ".join(f"`{n}`" for n in skeletons)
    ctx["lists"]["owners_reachable"] = ", ".join(o["code"] for o in owners if o["reachable"])
    ctx["lists"]["owners_external"] = ", ".join(o["code"] for o in owners if not o["reachable"])
    ctx["lists"]["live_checks"] = " / ".join(
        [label for name, label in (("logs", "log identity"), ("global_settings", "settings"),
                                   ("external_reference", "external-reference pages")) if ctx["has"][name]]
        + [t["name"] for t in extra_tools if t["live"]]
    )
    ctx["lists"]["tools_live_names"] = ", ".join(t["name"] for t in extra_tools if t["live"])
    value_kinds = (
        (["a log identity"] if ctx["has"]["logs"] else [])
        + (["a setting value"] if ctx["has"]["global_settings"] else [])
        + (["a tool identifier"] if ctx["has"]["tool_identity"] else [])
    )
    ctx["has"]["live_value_kinds"] = bool(value_kinds)
    ctx["lists"]["live_value_kinds"] = ", ".join(value_kinds)
    ctx["lists"]["tool_identity_names"] = ", ".join(t["name"] for t in extra_tools if t["identity"])
    ctx["lists"]["tool_identities"] = "; ".join(f"{t['name']}: {t['identity']}" for t in extra_tools if t["identity"])
    dir_map = cfg["paths"]["repo_dir_map"]
    ctx["lists"]["repo_rules"] = "; ".join(f"`{r['from']}` → `{r['to']}`" for r in dir_map["rules"])
    ctx["lists"]["repo_aliases"] = "; ".join(f"`{k}` → `{v}`" for k, v in dir_map["aliases"].items())
    ctx["has"]["repo_rules"] = bool(dir_map["rules"])
    ctx["has"]["repo_aliases"] = bool(dir_map["aliases"])
    wave = cfg["audit"]["fan_out"]["wave_size"]
    ctx["lists"]["wave_size"] = f"{wave[0]} to {wave[-1]}"
    access = []
    for name in ("logs", "metrics"):
        if ctx["has"][name] and caps[name]["access"] not in ("none", ""):
            access.append(f"the `{caps[name]['access']}` MCP ({labels[name]})")
    if ctx["has"]["global_settings"] and caps["global_settings"]["lookup"]:
        access.append(caps["global_settings"]["lookup"])
    access.extend(f"{t['reach']} ({t['name']})" for t in extra_tools if t["live"])
    ctx["has"]["live_access"] = bool(access)
    ctx["lists"]["live_access"] = join_and(access)
    ctx["derived"] = {
        "reader_description": reader_description(cfg, ctx["has"], f"{tools} data" if obs else ""),
        "platform_basics": platform_basics(cfg["known_context"]["platform_basics"], ctx["has"]["shared_catalogs"]),
        "observability_tools": tools,
        "labels": labels,
        "db_map": caps["db_schema"].get("map", []),
        "tools": extra_tools,
        "catalog_headings": ", ".join(c["heading"] for c in caps["shared_catalogs"]),
        "knowledge_root": posixpath.join(repo, out_rel, "skills", base) if out_rel != "." else posixpath.join(repo, "skills", base),
        "kit_root": posixpath.join(repo, ".claude/skills"),
        "skills_root": posixpath.normpath(posixpath.join(out_rel, "skills")),
        "ledger_dir": f".claude/{base}-sync",
        "kit_rel": ("" if posixpath.relpath(".claude/skills", out_rel).startswith("..") else "./") + posixpath.relpath(".claude/skills", out_rel),
        "first_env": names[0],
        "envs_reversed": list(reversed(names)),
    }
    return ctx


KIT_DIR = "kit/"


def output_rel(rel):
    """Where a template is written: relative to <paths.repo> for the kit, to <paths.out> for the rest."""
    return ".claude/" + rel[len(KIT_DIR):] if rel.startswith(KIT_DIR) else rel


def strip_suffixes(rel):
    rel = rel[: -len(".tmpl")]
    return rel[: -len(".seed")] if rel.endswith(".seed") else rel


def seed_paths(templates, cfg):
    """Output paths of the files a user owns after the first render: written once, never overwritten."""
    prefix = cfg["identity"]["prefix"]
    return {
        output_rel(strip_suffixes(src.relative_to(templates).as_posix().replace("__prefix__", prefix)))
        for src in Path(templates).rglob("*.seed.tmpl")
    }


def render_tree(templates, cfg):
    validate(cfg)
    ctx = derive(cfg)
    prefix = cfg["identity"]["prefix"]
    files = []
    for src in sorted(Path(templates).rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(templates).as_posix().replace("__prefix__", prefix)
        if rel.endswith(".tmpl"):
            text = render(src.read_text(encoding="utf-8"), ctx, str(src))
            if text.strip():
                files.append((output_rel(strip_suffixes(rel)), text))
        else:
            files.append((output_rel(rel), src.read_text(encoding="utf-8")))
    return files


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN_ROOT / "templates"


def default_out(cfg):
    repo = os.path.expanduser(cfg["paths"]["repo"])
    return Path(posixpath.normpath(posixpath.join(repo, cfg["paths"]["out"])))


def destination(cfg):
    """Maps an output path to the file it is written at: the kit under the repo root, the rest under paths.out."""
    repo = Path(os.path.expanduser(cfg["paths"]["repo"]))
    out = default_out(cfg)
    return lambda rel: (repo if rel.startswith(".claude/") else out) / rel


def keep_regions(text, dest):
    """Carry the user's content of each keep region from the file on disk into a fresh render."""
    if not dest.exists():
        return text
    old = iter(KEEP.findall(dest.read_text(encoding="utf-8")))

    def put(m):
        prev = next(old, None)
        return m.group(0) if prev is None else m.group(1) + prev[1] + m.group(3)

    return KEEP.sub(put, text)


def plan_status(rel, text, dest_of, seeds):
    dest = dest_of(rel)
    if not dest.exists():
        return "new"
    if rel in seeds:
        return "kept"
    return "unchanged" if dest.read_text(encoding="utf-8") == text else "changed"


def show_plan(rows, dest_of):
    counts = collections.Counter(status for status, _, _ in rows)
    print("plan: " + ", ".join(f"{counts[k]} {k}" for k in ("new", "changed", "unchanged", "kept")))
    diffs = []
    for status, rel, text in rows:
        if status == "kept":
            print(f"kept     {rel}")
        elif status == "changed":
            old = dest_of(rel).read_text(encoding="utf-8")
            diff = list(difflib.unified_diff(old.splitlines(True), text.splitlines(True),
                                             f"existing/{rel}", f"rendered/{rel}"))
            added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
            removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
            print(f"changed  {rel}  (+{added} -{removed})")
            diffs.append(diff)
    for diff in diffs:
        print()
        sys.stdout.writelines(line if line.endswith("\n") else line + "\n" for line in diff)


def apply(rows, dest_of):
    wrote = kept = 0
    for status, rel, text in rows:
        if status == "kept":
            print(f"kept   {rel}")
            kept += 1
            continue
        dest = dest_of(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        print(f"wrote  {rel}")
        wrote += 1
    print(f"done: wrote {wrote}, kept {kept}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--write", action="store_true", help="apply the render; without it nothing is written")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        validate(cfg)
        derive(cfg)
        files = render_tree(TEMPLATES, cfg)
    except (ConfigError, TemplateError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyError as exc:
        print(f"error: the config lacks the key {exc.args[0]!r}; schema/config.reference.yaml lists every field",
              file=sys.stderr)
        return 1
    dest_of = destination(cfg)
    seeds = seed_paths(TEMPLATES, cfg)
    files = [(rel, keep_regions(text, dest_of(rel))) for rel, text in files]
    rows = [(plan_status(rel, text, dest_of, seeds), rel, text) for rel, text in files]
    if args.write:
        apply(rows, dest_of)
    else:
        show_plan(rows, dest_of)
    return 0


if __name__ == "__main__":
    sys.exit(main())
