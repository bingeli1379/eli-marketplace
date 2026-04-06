# issue-tracing

On-call triage assistant for Claude Code.

## Skills

### `/issue-tracing` — Incident Triage

Takes a Grafana or Kibana/ELK URL (or an alert description) and produces a structured
**Root Cause / Impact / How to Resolve / Unknowns** report in both Traditional Chinese and English.

- Step-by-step SOP with rules and gates that must be acknowledged before advancing
- Cross-project drill-down, infra-metric correlation, and Elasticsearch query helpers via reference docs
- Times in user-facing output use GMT+8 (Asia/Taipei)
