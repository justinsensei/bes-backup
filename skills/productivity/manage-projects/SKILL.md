---
name: manage-projects
description: 'Use when reviewing historical context only. DEPRECATED/HISTORICAL: Under
  the May 2026 status-project model, Justin does not use dedicated sub-projects in
  Todoist. All tasks live in status-based Projects (Now, Next, Soon, Maybe Later)
  or Inbox, and reference Obsidian project notes in their descriptions.'
version: 2.1.0
metadata:
  hermes:
    related_skills:
    - todoist
    - obsidian
    tags:
    - todoist
    - obsidian
    - projects
    - productivity
    - deprecated
    deprecated: true
author: Bes
license: MIT
platforms:
- linux
---

# Managing Projects (DEPRECATED — HISTORICAL REFERENCE ONLY)

**As of May 2026, Justin has decided to return to simple status-based Projects (Now, Next, Soon, Maybe Later) in Todoist. He no longer uses nested sub-projects or Work/Home/Other top-level folders in Todoist.**

This skill is kept for historical reference. The updated workflow is:
1. **No Todoist Projects are created for new GTD projects.**
2. **Tasks are created in Inbox, Now, Next, Soon, or Maybe Later.**
3. **To link a task to an Obsidian project note**, include the linkage in the task description: `Project: [[Project Name]]`.
4. **Obsidian project notes** (`category: "[[Projects]]"`) are still created in the vault root, but do not contain a `Todoist: <url>` link since there is no matching Project in Todoist. Instead, they can query Todoist for tasks referencing their name.
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
