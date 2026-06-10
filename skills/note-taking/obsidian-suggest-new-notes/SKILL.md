---
name: obsidian-suggest-new-notes
description: Use when working with obsidian suggest new notes. Suggest brand new Notes,
  Concepts, Decisions, or Thoughts based on a temporal scan of active logs over the
  last 48 hours, and initialize approved notes in the inbox.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - obsidian
    - suggest-notes
    - notes
    - sources
    - decisions
    - thoughts
    related_skills:
    - obsidian
    - obsidian-notes
    - obsidian-thoughts-beliefs
    - obsidian-decisions
    - obsidian-references-sources
platforms:
- linux
---

# Obsidian: Suggest New Notes

## Overview
This skill scans recent logs (Daily Notes, Meetings, and Sources) to identify conceptual gaps, insights, or missing definitions that are ripe for being captured as dedicated files. When Justin approves a suggestion, Bes immediately initializes the note in the `inbox/` directory with correct YAML frontmatter and a standard template.

---

## When to Use
- **Trigger:** Justin asks to "suggest new notes", "find gaps in my notes", or "scan recent logs for new note ideas".
- **Default:** Default lookback is the last 48 hours of log activity.
- **Don't use for:** Connecting pre-existing conceptual notes (use `obsidian-serendipity-links` instead).

---

## Execution Flow

### Step 1: Scan Recent Logs
Run the lookback script to get recent log content (truncates automatically to avoid token flood):
`python3 ~/.hermes/skills/note-taking/obsidian-suggest-new-notes/scripts/scan_recent_logs.py --hours 48`
*(Accepts custom lookback via `--hours X` if explicitly requested by Justin).*

### Step 2: Analyze & Curate
Analyze the returned logs and select exactly **5 candidate new notes**. Curate a balanced mix across these categories:
- **`Notes`**: Conceptual mappings or raw ideas (Category: `[[Notes]]`).
- **`Concepts`**: Summaries of books, articles, or tools mentioned (Category: `[[Concepts]]`).
- **`Decisions`**: Strategic, product, or architectural decisions made (Category: `[[Decisions]]`).
- **`Thoughts`**: Open research questions, emergent opinions, or theories (Category: `[[Thoughts]]`).

### Step 3: Present the Pitch
Present the 5 suggestions as a numbered list in this exact format:
1. **[[Proposed Note Title]]** (`category: "[[CategoryName]]"`)
   - **Why:** 1-2 sentence compelling rationale linking the note back to the specific log file/timestamp where it was discussed.

### Step 4: Approval & Creation
Ask Justin which suggestions he would like to approve. For each approved note:
1. Generate a unique 14-character ID: `YYYYMMDDHHmmss` (based on the current timestamp).
2. Create the file at `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/inbox/[Proposed Note Title].md` (Capitalized, spaced, with no numerical prefix or ID in the filename).
3. Populate the file with standard frontmatter and the corresponding category template (see "Templates" below).
4. Report successful creation of the stubs in the `inbox/` folder.

---

## Note Templates

### 1. Thoughts Template
```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Thoughts]]"
---

# Spaced Capitalized Thought Title

What is the core idea or reflection? Keep it atomic.

---

## Context & Details
- Emergent observations from logs...
- Open questions...
```

### 2. Concepts Template
```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Concepts]]"
---

### Citation
**Title** [Title]
**Author(s)** [Author]
**URL** [URL if available]

### Notes
- Key takeaways or summaries...

### Thoughts
- Reflections...
```

### 3. Decisions Template
```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Decisions]]"
---

# Spaced Capitalized Decision Title

## Context
Why was this decision discussed?

## Decision
What was decided, and who made the final call?

## Rationale
Why was this path chosen over others?

## Alternatives Considered
- **[Alternative A]:** Why it was rejected...
```

### 4. Notes Template
```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Notes]]"
---

# Spaced Capitalized Note Title

Core summary of the note topic.

---

## Details
- Supporting details or raw logs...
```

---

## Common Pitfalls
1. **Duplicate Creation:** Before pitching any note title or suggesting a new Concept, check if a file with that name, a synonym, or overlapping content already exists in the vault (even if currently classified under `category: \"[[Notes]]\"`). If it exists, do not suggest a brand-new note. Instead, propose reclassifying, merging, and consolidating the existing notes according to the **Preventing Concept & Note Duplication** guidelines in `obsidian-references-sources`.
2. **Path Misplacement:** Approved notes *must* always be written to the `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/inbox/` directory first, allowing manual review and triage later.
3. **Overwriting Frontmatter:** Ensure frontmatter strings use single or double quotes around the ID and wikilink to avoid parsing breaks.

---

## Verification Checklist
- [ ] Log scan output parsed successfully
- [ ] Exactly 5 suggestions presented with the correct pitch format
- [ ] Verified that none of the 5 candidate titles exist in the vault
- [ ] Approved notes written to `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/inbox/` with valid YAML frontmatter and proper templates
