#!/usr/bin/env bash
set -uo pipefail

# Structural integrity check for the plugin marketplace.
# Catches the regression classes found in manual audits:
#   - invalid JSON manifests
#   - marketplace.json <-> on-disk plugin drift
#   - skill/agent `name:` frontmatter not matching its directory/filename (silent load failure)
#   - skills missing from the central SOURCES.yaml registry
#   - bundled-file read instructions using a wrong-base relative path
#   - dangling references: a reference path or a `name.md` cross-reference that resolves to
#     nothing, and a glued `stepN` citation past the skill's real step count (what a rename
#     or a renumber leaves behind wherever the mention did not look like a path)
#
# Usage: ./scripts/check-structure.sh
# Exits non-zero if any ERROR is found (WARN does not fail the build). Wire into CI / pre-commit.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

errors=0
warns=0
err()  { echo "ERROR: $*"; errors=$((errors + 1)); }
warn() { echo "WARN:  $*"; warns=$((warns + 1)); }

# name: value from a markdown file's YAML frontmatter
get_name() {
  awk '/^---[[:space:]]*$/{c++; next}
       c==1 && /^name:/{sub(/^name:[[:space:]]*/,""); gsub(/["'\'']/,""); print; exit}
       c>=2{exit}' "$1"
}

# ---- 1. JSON validity (all manifests) ----
json_files=(".claude-plugin/marketplace.json")
for p in plugins/*/; do
  for m in "${p}.claude-plugin/plugin.json" "${p}.codex-plugin/plugin.json"; do
    [[ -f "$m" ]] && json_files+=("$m")
  done
done
for f in "${json_files[@]}"; do
  python3 -m json.tool "$f" >/dev/null 2>&1 || err "invalid JSON: $f"
done

# ---- 2. marketplace.json <-> disk ----
if python3 -m json.tool .claude-plugin/marketplace.json >/dev/null 2>&1; then
  reg_sources=$(python3 -c "import json; print('\n'.join(p['source'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']))")
  while IFS= read -r src; do
    [[ -z "$src" ]] && continue
    d="${src#./}"
    [[ -f "$d/.claude-plugin/plugin.json" ]] || err "marketplace.json source '$src' has no .claude-plugin/plugin.json"
  done <<< "$reg_sources"
  for p in plugins/*/; do
    name=$(basename "$p")
    echo "$reg_sources" | grep -qx "./plugins/$name" || err "plugin '$name' on disk is not registered in marketplace.json"
  done
fi

# ---- 3. skill name == parent directory ----
for s in plugins/*/skills/*/SKILL.md; do
  [[ -f "$s" ]] || continue
  dir=$(basename "$(dirname "$s")")
  nm=$(get_name "$s")
  [[ -n "$nm" ]] || { err "skill has no name: frontmatter ($s)"; continue; }
  [[ "$nm" == "$dir" ]] || err "skill name '$nm' != directory '$dir' ($s) — silent load failure"
done

# ---- 4. agent name == filename ----
for a in plugins/*/agents/*.md; do
  [[ -f "$a" ]] || continue
  base=$(basename "$a" .md)
  nm=$(get_name "$a")
  [[ -n "$nm" ]] || { err "agent has no name: frontmatter ($a)"; continue; }
  [[ "$nm" == "$base" ]] || err "agent name '$nm' != filename '$base' ($a)"
done

# ---- 5. SOURCES.yaml central registry coverage (WARN) ----
# SOURCES.yaml is the registry for the sdd family ONLY (core + sdd-* packs),
# not for unrelated plugins (dev-workflow, issue-tracing, ...).
SRC="plugins/sdd/skills/SOURCES.yaml"
if [[ -f "$SRC" ]]; then
  for s in plugins/sdd/skills/*/SKILL.md plugins/sdd-*/skills/*/SKILL.md; do
    [[ -f "$s" ]] || continue
    nm=$(basename "$(dirname "$s")")
    grep -qE "^${nm}:" "$SRC" || warn "sdd-family skill '$nm' is not registered in $SRC"
  done
fi

# ---- 6. wrong-base bundled-file read (WARN) ----
# A read/load instruction pointing at a `skills/...` path from inside a skill/agent body
# resolves against the wrong base (cwd, or a doubled skill path). Skill-local reads should
# use `references/x` / `templates/x`; plugin-level reads need ${CLAUDE_PLUGIN_ROOT}/skills/...
while IFS= read -r hit; do
  warn "possible wrong-base bundled read: $hit"
done < <(grep -rnE '(Read|Load|Open) [^`]{0,40}`skills/' plugins/*/skills plugins/*/agents 2>/dev/null | grep -v 'CLAUDE_PLUGIN_ROOT')

# ---- 7. reference integrity (dangling .md mentions, step citations, orphan files) ----
# The regression class that keeps recurring: a reference file gets renamed, or a skill's
# steps get renumbered, and the mentions are updated only where they LOOK like a path.
# Bare `` `name.md` `` cross-references and `step N` citations survive, pointing at nothing —
# and nothing complains, because the skill still loads fine.
# Deliberately NOT checked: a bare `name.md` inside a SKILL.md body. Those legitimately name
# files in the USER's project (spec artifacts like design.md / tasks.md, an audited repo's
# CONTRIBUTING.md), and nothing distinguishes them from a bundled cross-reference — flagging
# them buries the real hits under noise. A bare name inside references/ IS checked: those
# files cross-reference their siblings, they do not discuss user artifacts.
# Batched on purpose: one grep per assertion over the whole tree, not one per file. The
# per-file version spawned ~3000 greps and took 15s+ — slow enough that the check starts
# getting skipped, which costs more than it finds. (No associative arrays: macOS ships bash 3.2.)

skill_dir_of() {  # the skills/<name> dir owning a file, whether it is SKILL.md or a reference
  # parameter expansion, not dirname/basename: those are external processes, and at ~2000 calls
  # they cost more than every grep in this script combined.
  local d="${1%/*}"
  case "$d" in */references|*/templates) echo "${d%/*}";; *) echo "$d";; esac
}

resolves() {  # $1 = skill dir, $2 = bundled .md name
  # a single-character stem (`x.md`, `y.md`) is an illustrative placeholder in prose, not a path
  [[ "$2" =~ ^.\.md$ ]] && return 0
  local p="${1%/skills/*}"
  [[ -f "$1/references/$2" || -f "$1/templates/$2" || -f "$1/$2" \
     || -f "$p/references/$2" || -f "$p/agents/$2" || -f "$p/$2" ]]
}

# 7a. a path-shaped mention names a bundled location explicitly — it must resolve
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  f="${line%%:*}"; md="${line#*:}"; md="${md##*/}"
  resolves "$(skill_dir_of "$f")" "$md" || err "dangling reference path '$md' in $f"
done < <(grep -rHoE '(references|templates|agents)/[A-Za-z0-9._-]+\.md' plugins/*/skills 2>/dev/null | sort -u)

# 7b. a bare `name.md` inside a reference/template file — a sibling pointer, so it must resolve
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  f="${line%%:*}"; md="${line#*:}"; md="${md//\`/}"
  [[ "$md" =~ ^(SKILL|README|CHANGELOG|CLAUDE|AGENTS|MEMORY)\.md$ ]] && continue
  resolves "$(skill_dir_of "$f")" "$md" || err "dangling cross-reference '$md' in $f"
done < <(grep -rHoE '`[A-Za-z0-9._-]+\.md`' plugins/*/skills/*/references plugins/*/skills/*/templates 2>/dev/null | sort -u)

# 7c. a GLUED `stepN` citation is a filename stem, not prose — it must be a real step of the
# owning skill. Spaced prose ("propose's Step 9a") is a legitimate cross-skill citation and is
# left alone; renaming stepN-*.md files is what leaves the glued ones behind.
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  f="${line%%:*}"; n="${line#*:}"; n="${n//[!0-9]/}"
  sdir=$(skill_dir_of "$f")
  [[ -f "$sdir/SKILL.md" ]] || continue
  nsteps=$(grep -cE '^[0-9]+\. \*\*' "$sdir/SKILL.md")
  (( nsteps > 0 && n > nsteps )) \
    && err "glued citation 'step$n' in $f, but $sdir has only $nsteps steps"
done < <(grep -rHoE '[Ss]tep[0-9]+' plugins/*/skills 2>/dev/null | sort -u)

# 7d. a skill-level reference file nobody in the plugin points at (WARN). One pass per plugin
# collecting every .md name it mentions, then a set lookup. Upstream-mirrored skills are
# skipped (SOURCES.yaml `repo:` is a URL): their bodies are replaced on the next sync, so a
# pointer added there is lost and the warning would never clear.
# Membership is tested with bash pattern matching, NOT `grep <<<` — a herestring plus a grep
# spawn per file was ~1200 processes and ~10s here, while the greps themselves cost ~140ms.
upstream_skills=$([[ -f "$SRC" ]] && awk '/^[a-z0-9-]+:/{k=$1} /repo: *https?:\/\//{print k}' "$SRC" | tr -d ':')
upstream_set=$'\n'"$upstream_skills"$'\n'
for p in plugins/*/; do
  # both spellings count as a mention: a bare `name.md` and a path-shaped `references/name.md`
  mentioned=$(grep -rhoE '`[A-Za-z0-9._/-]+\.md`' "$p" 2>/dev/null | tr -d '`' | sed -E 's|.*/||' | sort -u)
  mentioned_set=$'\n'"$mentioned"$'\n'
  for r in "$p"skills/*/references/*.md; do
    [[ -f "$r" ]] || continue
    skill="${r%/references/*}"; skill="${skill##*/}"
    [[ "$upstream_set" == *$'\n'"$skill"$'\n'* ]] && continue
    rb="${r##*/}"
    [[ "$mentioned_set" == *$'\n'"$rb"$'\n'* ]] \
      || warn "orphan reference file, nothing points at it: $r"
  done
done

echo ""
echo "Structure check: $errors error(s), $warns warning(s)"
[[ $errors -eq 0 ]]
