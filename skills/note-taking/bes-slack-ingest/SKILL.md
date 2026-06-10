---
name: bes-slack-ingest
description: Use when working with bes slack ingest. Capture and ingest Slack conversations
  as brief pointer records with a short topic description and participant list.
version: 2.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - slack
    - obsidian
    - ingest
    - logs
    related_skills:
    - obsidian
    - obsidian-logs
    - obsidian-graph-enrichment
    - obsidian-vault-jam
platforms:
- linux
---

# Bes Slack Ingest

Captures noteworthy Slack threads and brain-dumps as lightweight pointer records inside `Logs/Slack/`. 

These notes are intentionally **minimalist**. They must never contain point-by-point summaries, individual quotes, or try to capture decisions or thoughts. They function purely as a index/pointer back to Slack with a brief human-readable description.

## Synced Path
- `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/Logs/Slack/YYYY-MM-DD - Spaced Title.md`

---

## Slack Log Note Structure

Every Slack log note must start with this frontmatter format:

```yaml
---
id: 'YYYYMMDDHHmmss'                 # Numerical string based on first message's timestamp
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]" # Symmetrical daily note link
category: "[[Slack]]"                 # Quoted category link
channel: "channel-name"              # The source Slack channel
original_url: "https://slack.com/..." # Link to original discussion
participants:
  - "User A"
  - "User B"
---
```

Below the frontmatter, the body is kept super short:

```markdown
# 💬 Slack Thread: [Cleaned Title]

- **Channel:** #channel-name
- **Date:** YYYY-MM-DD
- **Original Thread:** [Slack Link](https://slack.com/...)

---

## 🎯 Topic Description
[A brief, 2-3 sentence human-readable description of the topic discussed. Acts as a simple pointer to the conversation without listing thoughts, decisions, or individual quotes.]
```

---

## The Creation vs. Enrichment Lifecycle

### 1. Initial Creation (First Ingest)
When a Slack brain reaction or capture is first triggered, create a **super short stub note** containing only the basic frontmatter (with initial participants found) and a temporary 1-sentence topic description placeholder.

### 2. Vault Enrichment Step
During subsequent vault enrichment runs (e.g., during Wind-Down, Morning Briefings, or an on-demand Vault Jam):
1. Review all Slack logs created since the previous vault enrichment run.
2. Read the source Slack thread replies if needed to refine and write a polished **2-3 sentence Topic Description**.
3. Verify and compile the complete list of **main participants** and ensure they are added to the frontmatter `participants` list.
4. **Enforce the Constraints:** Actively prune and remove any point-by-point summaries, individual thoughts, quotes, or decision trees that may have leaked into the logs. Keep them strictly as simple pointers.
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
