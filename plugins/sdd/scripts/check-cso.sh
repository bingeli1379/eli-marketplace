#!/usr/bin/env bash
set -euo pipefail

# Check skill descriptions for CSO (Claude Search Optimization) violations.
# Descriptions should contain triggering conditions only, not workflow summaries.
#
# Usage:
#   ./scripts/check-cso.sh              # check all skills
#   ./scripts/check-cso.sh vue          # check a specific skill
#
# Run after update-skills.sh to catch newly synced skills with bad descriptions.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
# Skills live across sibling plugins (sdd core + sdd-<lang> packs). Mirror
# update-skills.sh and scan EVERY plugin's skills, not just core — the synced
# pack skills are exactly the ones this check exists to police.
PLUGINS_DIR="$(dirname "$ROOT_DIR")"

FILTER="${1:-}"
issues=0
checked=0

# Dangerous patterns: action verbs at start of description that Claude may follow
# as instructions instead of reading the full SKILL.md
DANGEROUS_PATTERNS=(
  "^  (Run|Execute|Perform|Create|Build|Generate|Scaffold|Deploy|Configure|Write|Produce|Detect|Analyze|Scan)"
  "^description: (Run|Execute|Perform|Create|Build|Generate|Scaffold|Deploy|Configure|Write|Produce|Detect|Analyze|Scan)"
  "(Auto-detect|Automatically|Adapts|Handles|Manages)"
)

for skill_dir in "$PLUGINS_DIR"/*/skills/*/; do
  skill_name=$(basename "$skill_dir")

  # Skip non-skill directories
  [[ ! -f "$skill_dir/SKILL.md" ]] && continue
  [[ "$skill_name" == "SOURCES.yaml" ]] && continue

  # Apply filter
  if [[ -n "$FILTER" && "$skill_name" != "$FILTER" ]]; then
    continue
  fi

  checked=$((checked + 1))

  # Extract description block from frontmatter
  desc=$(awk '
    BEGIN { in_fm=0; in_desc=0 }
    /^---$/ { in_fm++; next }
    in_fm == 1 && /^description:/ { in_desc=1; print; next }
    in_fm == 1 && in_desc && /^  / { print; next }
    in_fm == 1 && in_desc && !/^  / { in_desc=0 }
    in_fm >= 2 { exit }
  ' "$skill_dir/SKILL.md")

  if [[ -z "$desc" ]]; then
    continue
  fi

  found_issue=false

  # Check for dangerous action-verb patterns
  for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$desc" | grep -qE "$pattern"; then
      if [[ "$found_issue" == "false" ]]; then
        echo "WARN: $skill_name"
        found_issue=true
      fi
      match=$(echo "$desc" | grep -oE "$pattern" | head -1)
      echo "  Action verb in description: \"$match\""
    fi
  done

  # Check if description lacks "Use when" or "MUST be loaded when" trigger
  if ! echo "$desc" | grep -qiE "(Use when|Use for|MUST be loaded when|Load this skill when)"; then
    if [[ "$found_issue" == "false" ]]; then
      echo "WARN: $skill_name"
      found_issue=true
    fi
    echo "  Missing trigger phrase (\"Use when...\", \"Load this skill when...\")"
  fi

  if [[ "$found_issue" == "true" ]]; then
    issues=$((issues + 1))
  fi
done

echo ""
if [[ $issues -eq 0 ]]; then
  echo "OK: $checked skills checked, no CSO issues found"
else
  echo "DONE: $checked skills checked, $issues with CSO warnings"
  echo ""
  echo "Fix: Rewrite description to start with \"Use when...\" and remove workflow/action verbs."
  echo "See: skills/skill-authoring-guidelines/SKILL.md for CSO rules."
fi
