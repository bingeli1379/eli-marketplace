#!/usr/bin/env bash
set -euo pipefail

# Update bundled skills from their upstream sources.
# Reads skills/SOURCES.yaml and pulls the latest SKILL.md + references/ (or reference/) + assets/ for each.
#
# LOCAL FRONTMATTER IS PRESERVED: only the SKILL.md body (after the second `---`)
# is replaced from upstream. The local frontmatter block — name, description,
# user-invocable, etc. — is always kept. So you may edit a skill's `description`
# (e.g. to sharpen its trigger wording) and re-run this script without losing it.
# `repo: original` skills are never synced; `frozen: true` skills sync only with --all.
#
# FORKED SKILLS (`repo: original` + an `upstream:` field): a skill we diverged from its
# source stays out of the sync — but going `original` used to also mean going blind to
# upstream improvements forever. Two modes fix that without ever risking the local body:
#
#   --drift    report what upstream changed since we forked (never touches a file)
#   --snapshot record upstream's current body as the new fork baseline
#
# The baseline lives in skills/.baselines/<skill>.md (upstream body at fork time). `--drift`
# diffs that baseline against upstream now, so it shows exactly the upstream changes we have
# not yet considered — our own local edits never appear as noise. After you review a drift
# report and fold in (or reject) what upstream did, run --snapshot to reset the baseline;
# the next --drift then starts from there.
#
# Usage:
#   ./scripts/update-skills.sh                 # update all non-frozen skills
#   ./scripts/update-skills.sh vue             # update a specific skill
#   ./scripts/update-skills.sh --all           # update all including frozen
#   ./scripts/update-skills.sh --drift         # drift report for every forked skill
#   ./scripts/update-skills.sh --drift tdd     # drift report for one skill
#   ./scripts/update-skills.sh --snapshot tdd  # (re)record one skill's baseline
#   ./scripts/update-skills.sh --snapshot      # record baselines for all forked skills

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
# Skills live across sibling plugins (sdd core + sdd-<stack> packs); SOURCES.yaml
# stays the central registry in core. Resolve each skill's actual home at update
# time by searching the plugins dir, so a skill moving between packs needs no edit here.
PLUGINS_DIR="$(dirname "$ROOT_DIR")"
SOURCES_FILE="$ROOT_DIR/skills/SOURCES.yaml"
TMP_DIR=$(mktemp -d)
CLONE_DIR="$TMP_DIR/clones"
mkdir -p "$CLONE_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ ! -f "$SOURCES_FILE" ]]; then
  echo "Error: $SOURCES_FILE not found"
  exit 1
fi

BASELINE_DIR="$ROOT_DIR/skills/.baselines"

FILTER="${1:-}"
INCLUDE_FROZEN=false
MODE=sync
case "$FILTER" in
  --all)      INCLUDE_FROZEN=true; FILTER="" ;;
  --drift)    MODE=drift;    FILTER="${2:-}" ;;
  --snapshot) MODE=snapshot; FILTER="${2:-}" ;;
esac

updated=0
skipped=0
failed=0
drifted=0
no_baseline=0

# Clone a repo (cached by hash of URL)
get_clone() {
  local repo="$1"
  local hash
  hash=$(echo "$repo" | md5 -q 2>/dev/null || echo "$repo" | md5sum | cut -c1-8)
  local dest="$CLONE_DIR/$hash"

  if [[ -d "$dest" ]]; then
    echo "$dest"
    return 0
  fi

  if git clone --depth 1 --quiet "$repo" "$dest" 2>/dev/null; then
    echo "$dest"
    return 0
  else
    mkdir -p "$dest"
    touch "$dest/.clone_failed"
    echo "$dest"
    return 0
  fi
}

# Parse and process
current_skill=""
current_repo=""
current_path=""
current_frozen=""
current_filename=""
current_upstream=""
current_upstream_path=""

# Extract a SKILL.md-style body (everything after the second `---`), or the whole
# file when it has no frontmatter. Used by both drift and snapshot so the two always
# compare the same thing — body only, never frontmatter (ours is local by design).
extract_body() {
  local f="$1"
  if head -1 "$f" | grep -q "^---$"; then
    awk 'BEGIN{c=0} /^---$/{c++; if(c==2){found=1; next}} found{print}' "$f"
  else
    cat "$f"
  fi
}

# drift / snapshot for a forked skill (repo: original + upstream: <url>).
process_fork() {
  local skill="$1" upstream="$2" upstream_path="$3" filename="$4"
  local baseline="$BASELINE_DIR/$skill.md"

  local clone_dir
  clone_dir=$(get_clone "$upstream")
  if [[ -f "$clone_dir/.clone_failed" ]]; then
    echo "  FAILED: could not clone $upstream"
    failed=$((failed + 1))
    return
  fi

  local source="$clone_dir/$upstream_path/$filename"
  if [[ ! -f "$source" ]]; then
    echo "  FAILED: $filename not found at $upstream_path — upstream moved or removed it."
    echo "          Drop the upstream: field if it is gone for good."
    failed=$((failed + 1))
    return
  fi

  if [[ "$MODE" == "snapshot" ]]; then
    mkdir -p "$BASELINE_DIR"
    extract_body "$source" > "$baseline"
    echo "  baseline recorded ($(wc -l < "$baseline" | tr -d ' ') lines)"
    updated=$((updated + 1))
    return
  fi

  # drift
  if [[ ! -f "$baseline" ]]; then
    echo "  NO BASELINE — cannot tell what upstream changed since the fork."
    echo "          Run: $(basename "$0") --snapshot $skill  (records upstream's body as of now)"
    no_baseline=$((no_baseline + 1))
    return
  fi

  local upstream_now="$TMP_DIR/$skill.upstream"
  extract_body "$source" > "$upstream_now"

  if diff -q "$baseline" "$upstream_now" >/dev/null 2>&1; then
    echo "  no upstream change since fork"
    skipped=$((skipped + 1))
    return
  fi

  local added removed
  added=$(diff "$baseline" "$upstream_now" | grep -c '^>' || true)
  removed=$(diff "$baseline" "$upstream_now" | grep -c '^<' || true)
  echo "  DRIFT: upstream +$added/-$removed lines since the fork baseline"
  echo "  ----- upstream changes you have not considered yet -----"
  diff -u "$baseline" "$upstream_now" | tail -n +3 | sed 's/^/  /'
  echo "  -------------------------------------------------------"
  drifted=$((drifted + 1))
}

process_skill() {
  [[ -z "$current_skill" || -z "$current_repo" ]] && return

  # Apply filter
  if [[ -n "$FILTER" && "$current_skill" != "$FILTER" ]]; then
    return
  fi

  # Forked skills: sync skips them entirely; drift/snapshot handle only them.
  if [[ -n "$current_upstream" ]]; then
    if [[ "$MODE" != "sync" ]]; then
      echo "Checking $current_skill (forked from $current_upstream) ..."
      process_fork "$current_skill" "$current_upstream" "${current_upstream_path:-.}" "${current_filename:-SKILL.md}"
    fi
    return
  fi

  # No upstream: field. In drift/snapshot mode there is nothing to compare against.
  [[ "$MODE" != "sync" ]] && return
  [[ "$current_repo" == "original" ]] && return

  # Skip frozen unless --all
  if [[ "$current_frozen" == "true" && "$INCLUDE_FROZEN" == "false" ]]; then
    echo "Skipping $current_skill (frozen)"
    skipped=$((skipped + 1))
    return
  fi

  # Locate the skill's current home across all plugins; new skills default to core.
  local skill_dir
  skill_dir=$(find "$PLUGINS_DIR" -maxdepth 3 -type d -path "*/skills/$current_skill" 2>/dev/null | head -1 || true)
  [[ -z "$skill_dir" ]] && skill_dir="$ROOT_DIR/skills/$current_skill"
  local skill_filename="${current_filename:-SKILL.md}"

  echo "Updating $current_skill ..."

  local clone_dir
  clone_dir=$(get_clone "$current_repo")

  if [[ -f "$clone_dir/.clone_failed" ]]; then
    echo "  FAILED: could not clone $current_repo"
    failed=$((failed + 1))
    return
  fi

  # Resolve source directory
  local source_dir="$clone_dir/$current_path"

  if [[ ! -f "$source_dir/$skill_filename" ]]; then
    echo "  FAILED: $skill_filename not found at $current_path"
    failed=$((failed + 1))
    return
  fi

  # Update skill directory
  mkdir -p "$skill_dir"

  # Copy SKILL.md but preserve our frontmatter (name, description, user-invocable, etc.)
  # Only update the body content (everything after the second "---")
  local target="$skill_dir/SKILL.md"
  local source="$source_dir/$skill_filename"

  if [[ -f "$target" ]]; then
    # Extract our existing frontmatter block (between first and second ---)
    local our_frontmatter
    our_frontmatter=$(awk 'BEGIN{c=0} /^---$/{c++; next} c==1{print}' "$target")
    # Extract upstream body (everything after second ---)
    local upstream_body
    upstream_body=$(awk 'BEGIN{c=0} /^---$/{c++; if(c==2){found=1; next}} found{print}' "$source")

    # Check if upstream has frontmatter (starts with ---)
    local has_upstream_frontmatter=false
    if head -1 "$source" | grep -q "^---$"; then
      has_upstream_frontmatter=true
    fi

    if [[ -n "$our_frontmatter" && "$has_upstream_frontmatter" == "true" ]]; then
      # Upstream has frontmatter: keep ours, take upstream body
      local upstream_body
      upstream_body=$(awk 'BEGIN{c=0} /^---$/{c++; if(c==2){found=1; next}} found{print}' "$source")
      printf '%s\n' "---" > "$target"
      printf '%s\n' "$our_frontmatter" >> "$target"
      printf '%s\n' "---" >> "$target"
      printf '%s\n' "$upstream_body" >> "$target"
    elif [[ -n "$our_frontmatter" ]]; then
      # Upstream has NO frontmatter: keep ours, take entire upstream as body
      printf '%s\n' "---" > "$target"
      printf '%s\n' "$our_frontmatter" >> "$target"
      printf '%s\n' "---" >> "$target"
      printf '' >> "$target"
      cat "$source" >> "$target"
    else
      # We have no frontmatter either: just copy
      cp "$source" "$target"
    fi
  else
    cp "$source" "$target"
  fi

  # Copy references/ if exists
  if [[ -d "$source_dir/references" ]]; then
    rm -rf "$skill_dir/references"
    cp -r "$source_dir/references" "$skill_dir/references"
  fi

  # Copy reference/ (singular) if exists
  if [[ -d "$source_dir/reference" ]]; then
    rm -rf "$skill_dir/reference"
    cp -r "$source_dir/reference" "$skill_dir/reference"
  fi

  # Copy assets/ if exists — the synced BODY links to these files (google/skills ships example
  # manifests as assets/*.yaml), so leaving them behind syncs a body pointing at nothing.
  if [[ -d "$source_dir/assets" ]]; then
    rm -rf "$skill_dir/assets"
    cp -r "$source_dir/assets" "$skill_dir/assets"
  fi

  echo "  OK"
  updated=$((updated + 1))
}

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip comments and empty lines
  [[ "$line" =~ ^[[:space:]]*#.*$ || -z "${line// }" ]] && continue

  # Skill name line (no leading whitespace, ends with colon)
  if [[ "$line" =~ ^([a-zA-Z0-9_-]+):[[:space:]]*$ ]]; then
    process_skill
    current_skill="${BASH_REMATCH[1]}"
    current_repo=""
    current_path="."
    current_frozen=""
    current_filename=""
    current_upstream=""
    current_upstream_path=""
    continue
  fi

  # Property lines
  if [[ "$line" =~ ^[[:space:]]+repo:[[:space:]]+([^[:space:]#]+) ]]; then
    # capture only the first token — tolerate a trailing inline `# comment`
    current_repo="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ ^[[:space:]]+path:[[:space:]]+(.+)$ ]]; then
    current_path="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ ^[[:space:]]+frozen:[[:space:]]+(.+)$ ]]; then
    current_frozen="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ ^[[:space:]]+filename:[[:space:]]+(.+)$ ]]; then
    current_filename="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ ^[[:space:]]+upstream:[[:space:]]+([^[:space:]#]+) ]]; then
    # Provenance for a forked (`repo: original`) skill — used by --drift / --snapshot only.
    current_upstream="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ ^[[:space:]]+upstream_path:[[:space:]]+(.+)$ ]]; then
    current_upstream_path="${BASH_REMATCH[1]}"
  fi
done < "$SOURCES_FILE"

# Process last skill
process_skill

echo ""
if [[ "$MODE" == "drift" ]]; then
  echo "Drift: $drifted with upstream changes, $skipped unchanged, $no_baseline without a baseline, $failed failed"
  if [[ "$drifted" -gt 0 ]]; then
    echo "Review each diff above, fold in what is worth taking, then re-run with --snapshot <skill>"
    echo "to reset that skill's baseline. Nothing was modified by this run."
  fi
elif [[ "$MODE" == "snapshot" ]]; then
  echo "Snapshot: $updated baseline(s) recorded, $failed failed"
else
  echo "Done: $updated updated, $skipped skipped, $failed failed"
fi
