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
# Skills live across sibling plugins (sdd core + sdd-<stack> packs). Mirror
# update-skills.sh and scan EVERY plugin's skills, not just core — the synced
# pack skills are exactly the ones this check exists to police.
PLUGINS_DIR="$(dirname "$ROOT_DIR")"

FILTER="${1:-}"
issues=0
checked=0

# Action verbs OPENING the description, which Claude may follow as an instruction
# instead of reading the full SKILL.md. Checked against the first line of the
# description value only — a folded block's continuation lines are prose, and
# matching them flagged API names such as "ExecuteDeleteAsync" as action verbs.
# The trailing space anchors the match to a real verb, not a longer identifier.
OPENING_VERB_PATTERN="^(Run|Execute|Perform|Create|Build|Generate|Scaffold|Deploy|Configure|Write|Produce|Detect|Analyze|Scan)[[:space:]]"

# Vague capability claims, flagged anywhere in the description.
SOFT_PATTERNS=(
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

  # First line of the description VALUE: the text after "description:", or for a
  # folded/literal block the line below it. Leading quotes are stripped so a
  # quoted description is measured on its first word, not on the quote.
  first_line=$(echo "$desc" | head -1 | sed 's/^description:[[:space:]]*//')
  if [[ -z "$first_line" || "$first_line" == ">" || "$first_line" == "|" ]]; then
    first_line=$(echo "$desc" | sed -n '2p')
  fi
  first_line=$(echo "$first_line" | sed 's/^[[:space:]]*//; s/^["'"'"']//')

  # Check for an action verb opening the description
  if echo "$first_line" | grep -qE "$OPENING_VERB_PATTERN"; then
    echo "WARN: $skill_name"
    found_issue=true
    match=$(echo "$first_line" | grep -oE "$OPENING_VERB_PATTERN" | head -1)
    echo "  Action verb opens description: \"${match% }\""
  fi

  # Check for vague capability claims anywhere in the description
  for pattern in "${SOFT_PATTERNS[@]}"; do
    if echo "$desc" | grep -qE "$pattern"; then
      if [[ "$found_issue" == "false" ]]; then
        echo "WARN: $skill_name"
        found_issue=true
      fi
      match=$(echo "$desc" | grep -oE "$pattern" | head -1)
      echo "  Vague capability claim: \"$match\""
    fi
  done

  # A command-only skill (`disable-model-invocation: true`) cannot be selected by the
  # model at all, so it has no trigger surface to write: the command IS the trigger and
  # a phrasing enumeration is pure standing cost. Exempt it from the trigger-phrase check
  # rather than pushing its description back to "Use when...".
  if awk '
    /^---$/ { fm++; next }
    fm == 1 && /^disable-model-invocation:[[:space:]]*true[[:space:]]*$/ { found=1 }
    fm >= 2 { exit }
    END { exit !found }
  ' "$skill_dir/SKILL.md"; then
    if [[ "$found_issue" == "true" ]]; then
      issues=$((issues + 1))
    fi
    continue
  fi

  # Check if description lacks a trigger phrase
  # `Use BEFORE …` is the same trigger-phrase family, stated as timing rather than condition —
  # a write-time skill fires ahead of an action, not on a symptom. Trigger-only either way.
  if ! echo "$desc" | grep -qiE "(Use when|Use before|Use for|Use this skill when|MUST be loaded when|Load this skill when)"; then
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
fi
