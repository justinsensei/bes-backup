---
name: obsidian-references-sources
description: Use when creating or recording cheat sheets, factsheets, guidelines,
  or other people's conceptual summaries under Notes/.
version: 1.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - obsidian
    - notes
    - references
    - sources
    - readwise
    related_skills:
    - obsidian
    - obsidian-notes
platforms:
- linux
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

## Folders & Categories
- **Directory:** `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/Notes/` (or `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/inbox/` when drafting).
- **Categories & Naming:**
  - **References:** Standard reference notes, checklists, lookup tables.
    - Category link: `category: "[[References]]"`
    - Filename format: `Title.md` (no timestamp prefix, e.g. `Spaced Title.md`).
  - **Concepts:** Book summaries, articles, paper summaries, other people's thinking.
    - Category link: `category: "[[Concepts]]"`
    - Filename format: `ID Title.md` (e.g. `20260609120000 Spaced Title.md`).
  - **Sources (Logs):** Raw reading notes and bibliographical information (synced from Readwise).
    - Category link: `category: "[[Sources]]"`
    - Filename format: `Title.md` (no timestamp prefix, e.g. `Spaced Title.md`).

---

## Preventing Concept & Note Duplication
Before proposing, suggesting, or creating any new `[[Concepts]]` (or `[[References]]`), always scan the vault (specifically the `/Notes/` directory) for any existing notes with similar names, synonyms, or highly overlapping content, even if they are currently classified under `category: "[[Notes]]"`.
- **Search First:** Use `search_files` to verify whether there is an existing raw note that covers the same conceptual territory.
- **Consolidate & Promote over Creating Fresh:** If an existing raw note is found, do not create a duplicative new note. Instead, propose reclassifying the existing note to `[[Concepts]]`, merging any extra details if necessary.
- **De-duplication & Pruning:** If multiple similar/duplicate notes exist (e.g., `Continuous interviewing.md` and `Continuous interviewing torres.md`), consolidate the best text, links, and references into a single canonical note under the `[[Concepts]]` category and delete/prune the redundant raw notes to keep the vault clean.

---

## References Structure
Reference notes should be highly scannable, starting with a clear purpose block followed by structured facts:

```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
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

## Concepts Structure
Concept notes are simplified narratives that explain a theory, mental model, or concept without any initial heading (since the filename carries the title).

- **Drafting Location:** Always draft new concepts in the inbox (`vault/inbox/`) so the user can tweak and move them later.

```markdown
---
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
id: YYYYMMDDHHmmss
category: "[[Concepts]]"
---
[Concise narrative explaining the concept (1-2 short paragraphs) covering:]
- What the concept represents / core definition
- Its mechanics or how it operates
- Why it matters / context

# Related
- [[Link to relevant note or log]]
- [[Link to another log]]
```

---

## Sources (Logs) & Readwise Integration
- **Readwise Script:** Justin has a sync script located at `~/sync_readwise.py`. 
- **Trigger:** This script exports any highlight tagged `'vault'` (case-insensitive) from Readwise directly to `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/Logs/Sources/` (Category: `[[Sources]]`).
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
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
