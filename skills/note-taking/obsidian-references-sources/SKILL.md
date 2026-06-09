---
name: obsidian-references-sources
description: Use when creating or recording cheat sheets, factsheets, guidelines, or article clips and external literature summaries under Notes/.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, notes, references, sources, readwise]
    related_skills: [obsidian, obsidian-notes]
---

# Obsidian: References & Sources Management

## Overview
This skill governs the structure and standard templates for two categories under `Notes/`:
1. **References:** Highly useful factual notes, guidelines, checklists, cheat sheets, or lookup tables.
2. **Sources:** What others say (book summaries, articles, web clips, external papers, or Readwise highlights).

---

## References Definition & Boundary
- **Permanent Value:** References are reserved for permanent, highly durable notes that have long-term lookup value (e.g., API schemas, CLI cheat sheets, organization policies, standard operating procedures) and are expected to be referred to frequently over time.
- **Project-Bound Ephemera:** Do NOT categorize ephemeral checklists, migration plans, implementation guides, or setup lists connected to specific, time-bound projects as `[[References]]`. These should remain categorized as `[[Notes]]` or `[[Projects]]` within their project context.

---

---

## Folders & Categories
- **Directory:** `/home/justin.guest/vault/Notes/` or `/home/justin.guest/vault/sources/` (automated external syncs).
- **Categories:**
  - Standard reference/checklists: `category: "[[References]]"`
  - Book highlights, articles, paper summaries: `category: "[[Sources]]"`

---

## References Structure
Reference notes should be highly scannable, starting with a clear purpose block followed by structured facts:

```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[Daily Notes/YYYY-MM-DD-weekday|YYYY-MM-DD Weekday]]"
category: "[[References]]"
---

# Topic Name Guideline / Checklist

> Purpose: quick-reference or guidelines for a specific domain.

---

## Guidelines & Checklists
- [ ] Checklist item 1
- [ ] Checklist item 2

## Facts & Lookup Tables
- Labeled facts or lists of properties.
```

---

## Sources & Readwise Integration
- **Readwise Script:** Justin has a sync script located at `~/sync_readwise.py`. 
- **Trigger:** This script exports any highlight tagged `'vault'` (case-insensitive) from Readwise directly to `/home/justin.guest/vault/sources/`.
- **Machine Summaries:** Keep automated transcripts, web clips, or summaries under the `/sources/` folder instead of `/Logs/Meetings/` to prevent manual log pollution.
