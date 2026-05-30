#!/usr/bin/env bash
set -euo pipefail

# Update bundled skills from their upstream sources.
# Reads skills/SOURCES.yaml and pulls the latest SKILL.md + references/ for each.
#
# Usage:
#   ./scripts/update-skills.sh          # update all non-frozen skills
#   ./scripts/update-skills.sh vue      # update a specific skill
#   ./scripts/update-skills.sh --all    # update all including frozen

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCES_FILE="$ROOT_DIR/skills/SOURCES.yaml"
TMP_DIR=$(mktemp -d)
CLONE_DIR="$TMP_DIR/clones"
mkdir -p "$CLONE_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ ! -f "$SOURCES_FILE" ]]; then
  echo "Error: $SOURCES_FILE not found"
  exit 1
fi

FILTER="${1:-}"
INCLUDE_FROZEN=false
if [[ "$FILTER" == "--all" ]]; then
  INCLUDE_FROZEN=true
  FILTER=""
fi

updated=0
skipped=0
failed=0

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

process_skill() {
  [[ -z "$current_skill" || -z "$current_repo" ]] && return
  [[ "$current_repo" == "original" ]] && return

  # Apply filter
  if [[ -n "$FILTER" && "$current_skill" != "$FILTER" ]]; then
    return
  fi

  # Skip frozen unless --all
  if [[ "$current_frozen" == "true" && "$INCLUDE_FROZEN" == "false" ]]; then
    echo "Skipping $current_skill (frozen)"
    skipped=$((skipped + 1))
    return
  fi

  local skill_dir="$ROOT_DIR/skills/$current_skill"
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
    continue
  fi

  # Property lines
  if [[ "$line" =~ ^[[:space:]]+repo:[[:space:]]+(.+)$ ]]; then
    current_repo="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ ^[[:space:]]+path:[[:space:]]+(.+)$ ]]; then
    current_path="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ ^[[:space:]]+frozen:[[:space:]]+(.+)$ ]]; then
    current_frozen="${BASH_REMATCH[1]}"
  elif [[ "$line" =~ ^[[:space:]]+filename:[[:space:]]+(.+)$ ]]; then
    current_filename="${BASH_REMATCH[1]}"
  fi
done < "$SOURCES_FILE"

# Process last skill
process_skill

echo ""
echo "Done: $updated updated, $skipped skipped, $failed failed"
