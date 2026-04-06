#!/usr/bin/env bash
set -uo pipefail

# Structural integrity check for the plugin marketplace.
# Catches the regression classes found in manual audits:
#   - invalid JSON manifests
#   - marketplace.json <-> on-disk plugin drift
#   - skill/agent `name:` frontmatter not matching its directory/filename (silent load failure)
#   - skills missing from the central SOURCES.yaml registry
#   - bundled-file read instructions using a wrong-base relative path
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

echo ""
echo "Structure check: $errors error(s), $warns warning(s)"
[[ $errors -eq 0 ]]
