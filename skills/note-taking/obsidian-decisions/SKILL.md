---
name: obsidian-decisions
description: Use when creating or recording team or individual decisions, trade-offs,
  and reasoning logs under Notes/ with category "[[Decisions]]".
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - obsidian
    - notes
    - decisions
    - architecture
    - product
    related_skills:
    - obsidian
    - obsidian-notes
platforms:
- linux
---

# Obsidian: Decisions Log Management

## Overview
This skill governs the capture and structured recording of individual or team decisions. These files act as historical records of tradeoffs, constraints, and reasoning.

---

## Folder & Category
- **Directory:** Always draft decision notes in the inbox: `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/inbox/` (the user will review and move them later).
- **Category link:** `category: "[[Decisions]]"`

---

## Note Layout & Structure
A Decision Note is a simplified narrative highlighting the context, shift, and implications.

```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Decisions]]"
---
## Decision: Spaced Capitalized Topic Name
[Concise narrative of the decision (1-2 short paragraphs) covering:]
- What was the status quo before the decision
- What changed our minds & why (with accurate attribution to the actual decision-maker)
- What might cause us to change our minds later (if applicable)

## Related
- [[Link to relevant note or log]]
- [[Link to another log]]
```

---

## Core Rules
- **Accurate Attribution:** Always attribute the decision to the actual decision-maker. Do not assume or state Justin made a decision unless he explicitly did.
- **Capitalized spaced names:** Use `ID Title.md` format for the filename (where ID is the creation timestamp, e.g. `20260609170500 Pause app-to-web payment flow.md`).
- **Drafting Location:** Always place new decision notes in the inbox folder (`vault/inbox/`).
- **No Pipe Tables:** Avoid using markdown pipe tables; represent trade-offs or lists using clean bulleted list structures.
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
