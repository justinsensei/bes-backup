---
name: obsidian-categorize-and-sort
description: Use when triaging, organizing, or sorting legacy or incoming notes in Justin's vault by determining categories, updating frontmatter, and relocating files.
version: 2.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, operations, triage, sorting, taxonomy]
    related_skills: [obsidian, obsidian-people, obsidian-organizations, obsidian-daily-notes, obsidian-meetings, obsidian-decisions, obsidian-thoughts-beliefs, obsidian-projects, obsidian-references-sources]
---

# Obsidian Operation: Categorize and Sort Notes

## Overview
This operational skill defines the workflow for triaging and sorting new, legacy, or raw notes in Justin's Obsidian vault. It handles category determination, frontmatter updates, file relocation, and bulk batch processing.

---

## The Triage Process

### Step 0 — Scan for Embedded Instructions (Command & Check-off Protocol)
Before classifying or moving any note, scan its content for embedded instructions directed at Bes:
1. **Inline Tasks (`- [ ] @bes <task>`)**: 
   - Parse and execute the instruction (e.g., "create a People note for Clio if we don't have one").
   - Once complete, edit the file to check off the task and log the completion:
     ```markdown
     - [x] @bes <task> (Done YYYY-MM-DD)
     ```
2. **Comment Blocks (`%% bes-instructions ... %%`)**:
   - Execute all listed actions in the block (e.g. metadata overrides, link creation, calendar additions).
   - Once complete, update the block header to reflect processing:
     ```markdown
     %% bes-instructions (processed YYYY-MM-DD)
     ...
     %%
     ```

### Step 1 — Determine the Category
Read the note content and title. Map the note to **exactly one** category from the core taxonomy below. Convert legacy inline tags (e.g. `#people`) to formal category properties.

| Category Link | Destination Folder | Category-Level Formatting Sub-skill |
|---|---|---|
| `category: "[[People]]"` | `Contacts/` | **`obsidian-people`** |
| `category: "[[Organizations]]"` | `Contacts/` | **`obsidian-organizations`** |
| `category: "[[Notes]]"` | `Notes/` | **`obsidian-notes`** |
| `category: "[[References]]"` | `Notes/` | **`obsidian-references-sources`** |
| `category: "[[Sources]]"` | `Notes/` | **`obsidian-references-sources`** |
| `category: "[[Thoughts]]"` | `Notes/` | **`obsidian-thoughts-beliefs`** |
| `category: "[[Beliefs]]"` | `Notes/` | **`obsidian-thoughts-beliefs`** |
| `category: "[[Decisions]]"` | `Notes/` | **`obsidian-decisions`** |
| `category: "[[Projects]]"` | `Notes/Projects/` | **`obsidian-projects`** |
| `category: "[[Daily Notes]]"` | `Daily Notes/` | **`obsidian-daily-notes`** |
| `category: "[[Meetings]]"` | `Logs/Meetings/` | **`obsidian-meetings`** |
| `category: "[[Categories]]"` | `Utilities/Categories/` | **`obsidian-utilities`** |

---

### Step 2 — Format the Content (Sub-Skill Handoff)
Once the category is identified:
1. Ensure the note has standard frontmatter (`id`, `daily_note`, `category`).
2. Update YAML properties cleanly (e.g. `reviewed: true`).
3. Load the corresponding category-specific sub-skill if structural formatting or templates are required.

---

### Step 3 — Move the File to its Target Folder
Identify the target folder from the table above. If the folder is different from the file's current folder (such as moving a note to `Notes/Projects/`), move the file using the filesystem.
```bash
mv "/home/justin.guest/vault/Notes/Some Project.md" "/home/justin.guest/vault/Notes/Projects/Some Project.md"
```
*Note: Always verify or create the target directory using `mkdir -p` before moving.*

---

## Classification Guidelines & Boundary Distinctions

To avoid naive categorization, distinguish clearly between the five main types under `/Notes/`:

### 1. References (`[[References]]`) — Re-usable Decision Patterns & Equations
* **Criteria**: Captures established, re-usable decision patterns, equations, standard formulas, or permanent lookup guides (e.g. *5 Percent Rule for freemium*, *Active user growth equation*, *Counting any action vs just specific actions*, *SignLab glossary*).
* **Boundary**: Do not put highly temporary checklists, ephemeral migration plans, or project-bound guides here; those are fleeting things that belong under `[[Notes]]` or `[[Projects]]`.

### 2. Thoughts (`[[Thoughts]]`) — Subjective & Evolving Reflections
* **Criteria**: Personal strategic critiques, qualitative assessments, subjective opinions, or career/life reflections representing *your own thinking* (e.g. *Signlab K12 GTM*, *Heuristics in the habit loop*, *Second Brain critiques*, *Swim in the morning*).

### 3. Beliefs (`[[Beliefs]]`) — Axioms & Playbook Principles
* **Criteria**: Guiding, core axioms of your professional or personal playbook—hard-won convictions that shape your actions and how you see the world (e.g. *Problems first solutions second*, *Velocity vs speed*, *Digital hoarding kills Zettelkasten*).
* **Pass Rule**: During bulk triage sweeps, do NOT spend time fleshing out, grooming, or elaborating on Beliefs. Focus strictly on correct categorization.

### 4. Concepts (`[[Concepts]]`) — Others' Theories & Models
* **Criteria**: Summaries and breakdowns of *other people's* models, frameworks, academic theories, or book/article insights (e.g. *Continuous interviewing*, *User story maps*, *Expert generalists*, *System 1 works by association*).

### 5. Notes (`[[Notes]]`) — Fleeting & Operational Records
* **Criteria**: Highly temporal, transient, or fleeting tactical operations, specific API troubleshooting logs, tool setup scripts, meeting agendas, temporary schedules, or software configurations (e.g. *Claude vs Perplexity*, *Lovable subscription*, *Ski season dates*).
* **Rule**: Keep these in `category: "[[Notes]]"`. They are ephemeral, factual logs that do not represent concepts or deep strategic reflections.

### 6. Empty Stubs & Obsolete Drafts (Active Pruning)
* **Rule**: Do not try to categorize empty placeholder notes, incomplete stubs, or obsolete structural outlines (e.g. *Discovering the right problems*, *My note taking system* stubs). Proactively propose deleting them from the filesystem.

---

## Batch Triage Operations Protocol

When performing large-scale triage or backlog classification sweeps (e.g., in batches of 10 or 20):

1. **Initialize Tracking**: Run a script to safely append a temporary `reviewed: false` property to the YAML frontmatter of all candidate files. This prevents duplicate triage and establishes a stable, queryable baseline.
2. **Sequential Chronological Batches**: Sort the candidate notes chronologically using their 14-digit timestamp-based ID (`YYYYMMDDHHmmss`) in their filename/ID. Process them in structured, manageable batches (e.g., 20 at a time).
3. **Running Metrics**: Always calculate and display the total number of remaining notes left to review in the backlog (not including the current batch) at the start of your response.
4. **Tabular Design**:
   - Present the batch in a clean, highly compact markdown table.
   - Omit redundant columns (e.g., if all notes currently being processed have the same starting category like `[[Notes]]`, do NOT include a "Current Category" column).
5. **Diverse & Active Proposals**: Proactively suggest precise categories based on the guidelines above. Do not default everything to `[[Notes]]`.
6. **Commit and Advance**: Once approved, run a script to update the frontmatter of each note (changing `reviewed: false` to `reviewed: true` and applying the new category) and move files if necessary.

---

## Common Pitfalls
- **Multiple Categories:** Never assign multiple categories to a single note. Every note gets **exactly one** category.
- **Leaking Inbox:** Do not leave notes in `inbox/` once categorized. All processed notes must reside in their taxonomy folders.
- **Ephemeral Project Guides as References:** Do not categorize temporary checklists or migration guides tied to a specific project as `[[References]]`. References are reserved for permanent, long-term lookup documents. Project-bound checklists/guides belong under `[[Notes]]` or `[[Projects]]`.
- **Links Verification:** moves are generally safe since Obsidian auto-resolves links by note name regardless of folder structure.
