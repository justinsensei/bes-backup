---
name: obsidian-references-sources
description: Use when creating or recording cheat sheets, factsheets, guidelines, or other people's conceptual summaries under Notes/.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, notes, references, sources, readwise]
    related_skills: [obsidian, obsidian-notes]
---

# Obsidian: References & Concepts Management

## Overview
This skill governs the structure and standard templates for two categories under `Notes/`:
1. **References:** Highly useful factual notes, guidelines, checklists, cheat sheets, or lookup tables.
2. **Concepts:** What others say / think (book summaries, articles, web clips, external papers, or other people's synthesized thoughts).

---

## References Definition & Boundary
- **Permanent Value:** References are reserved for permanent, highly durable notes that have long-term lookup value (e.g., API schemas, CLI cheat sheets, organization policies, standard operating procedures) and are expected to be referred to frequently over time.
- **Project-Bound Ephemera:** Do NOT categorize ephemeral checklists, migration plans, implementation guides, or setup lists connected to specific, time-bound projects as `[[References]]`. These should remain categorized as `[[Notes]]` or `[[Projects]]` within their project context.

---

---

## Folders & Categories
- **Directory:** `/home/justin.guest/vault/Notes/` or `/home/justin.guest/vault/sources/` (automated external syncs).
- **Categories & Naming:**
  - **References:** Standard reference notes, checklists, lookup tables.
    - Category link: `category: "[[References]]"`
    - Filename format: `Title.md` (no timestamp prefix, e.g. `Spaced Title.md`).
  - **Concepts:** Book summaries, articles, paper summaries, other people's thinking.
    - Category link: `category: "[[Concepts]]"`
    - Filename format: `ID Title.md` (e.g. `20260609120000 Spaced Title.md`).

---

## References vs. Ephemeral Project-Bound Notes
- **References** are meant to be **permanent notes** that contain long-term value, guidelines, or checklists that Justin expects to refer to frequently over time (e.g., API documentation, general checklists, cheat sheets).
- **Ephemeral checklists, plans, or migration guides** connected to specific, time-bound projects are NOT references. Do not categorize them as `[[References]]`; instead, categorize them under `[[Notes]]` or `[[Projects]]` so they stay organized with their respective projects.

---

## References Structure
Reference notes should be highly scannable, starting with a clear purpose block followed by structured facts:

```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[Daily Notes/YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
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

## Sources (Logs) & Readwise Integration
- **Readwise Script:** Justin has a sync script located at `~/sync_readwise.py`. 
- **Trigger:** This script exports any highlight tagged `'vault'` (case-insensitive) from Readwise directly to `/home/justin.guest/vault/Logs/Sources/` (Category: `[[Sources]]`).
- **Machine Summaries:** Keep automated transcripts, web clips, or summaries under the `/sources/` folder instead of `/Logs/Meetings/` to prevent manual log pollution.

## Web Clipping & Bypassing Paywalls / Cloudflare
When creating new `[[Concepts]]` from online articles (e.g. Medium, Substack, paywalled or Cloudflare-protected sites), standard `browser_navigate` or raw `curl` commands may fail with a 403 Forbidden or show a bot challenge page.
To bypass these limitations reliably and retrieve clean markdown content:
- Use **Jina Reader API (`r.jina.ai`)** via a terminal curl command:
  ```bash
  curl -s -L -A "Mozilla/5.0" "https://r.jina.ai/https://example.com/article-slug"
  ```
- This retrieves a beautifully cleaned markdown conversion of the page, bypassing Cloudflare mitigation challenges and standard registration screens.
- Process the retrieved markdown, select key arguments or synthesis, and write it as a new note with a `category: "[[Concepts]]"` property under `Notes/` following the filename convention `ID Title.md`.
