---
name: obsidian-categorize-and-sort
description: Use when triaging, organizing, or sorting a new or incoming note (e.g. in inbox/) by determining its category, formatting its template via sub-skills, and moving it to its correct directory.
version: 1.3.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, operations, triage, sorting, taxonomy]
    related_skills: [obsidian, obsidian-people, obsidian-organizations, obsidian-daily-notes, obsidian-meetings, obsidian-decisions, obsidian-thoughts-beliefs, obsidian-projects, obsidian-references-sources]
---

# Obsidian Operation: Categorize and Sort Notes

## Overview
This operational skill handles the workflow of triaging new, raw, or incoming notes. It guides determining the category, formatting the note structure using category-specific sub-skills, and moving the file to its designated physical folder.

---

## The Triage Process

### Step 0 — Scan for Embedded Instructions (Command & Check-off Protocol)
Before classifying or moving a new note, scan its content for embedded instructions directed at Bes:
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
Read the note content and title. Map the note to **exactly one** category from the table below. Convert legacy inline tags (e.g. `#people`) to formal category properties.

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
2. Load the corresponding category-specific sub-skill (e.g. `obsidian-people` for a biography note, or `obsidian-decisions` for a choice log).
3. Format or scaffold the note body according to that category's standard template.

---

### Step 3 — Move the File to its Target Folder
Identify the target folder from the table above. Move the file from its source folder (such as `inbox/`) to the target destination folder.
```bash
mv "/home/justin.guest/vault/inbox/Some Note.md" "/home/justin.guest/vault/Notes/Some Note.md"
```
*Note: Always verify or create the target directory using `mkdir -p` before moving.*

---

## Bulk Triage & Migration Protocol (Batch Processing)
When handling bulk classification or cleanups (e.g., triaging hundreds of legacy notes):
1. **Initialize Tracking**: Run a script to safely append a temporary `reviewed: false` property to the YAML frontmatter of all candidate files. This prevents duplicate triage and establishes a stable, queryable baseline.
2. **Chronological Batches**: Sort the candidate notes chronologically using their 14-digit timestamp-based ID (`YYYYMMDDHHmmss`). Process them in structured, manageable batches of 10.
3. **Interactive Proposals**: For each batch of 10, present the note titles, snippets, proposed categories, and brief rationales to the user for feedback.
4. **Commit and Advance**: Once approved, update the frontmatter of each note (changing `reviewed: false` to `reviewed: true` and applying the new category) before relocating the files.

---

## Classification Guidelines & Ambiguities

To avoid incorrect or naive categorization, always classify notes into exactly one of these five core sub-categories under `/Notes/`:

### 1. Notes (Fleeting & Operational)
* **Definition:** Fleeting, operational, short-lived, or troubleshooting logs (e.g., *Obsidian Claude use cases*, *Claude Obsidian issues*, *Zettelkasten updates*).
* **Rule:** If the content is highly transactional, temporary, or serves as a fleeting reference/work-log, keep it as `category: "[[Notes]]"` and set `reviewed: true`.

### 2. Thoughts (Subjective & Evolving)
* **Definition:** Evolving personal opinions, subjective reflections, career thoughts, and strategic or methodological critiques (e.g., *Product vs development methodologies*, *Second Brain critiques*, *Swim in the morning*).
* **Rule:** Put personal reflections and subjective, fluid ideas here under `category: "[[Thoughts]]"`.

### 3. Beliefs (Axioms & Playbook Principles)
* **Definition:** Core, durable guiding principles or playbook axioms that govern action and shape how you see the world (e.g., *Problems first solutions second*, *Velocity vs speed*, *Digital hoarding kills Zettelkasten*, *Common habit loop mistakes*).
* **Rule:** Use `category: "[[Beliefs]]"` for hard-won, structured convictions that represent your professional or personal operating principles. No need to flesh out/elaborate new Beliefs immediately during bulk triage passes.

### 4. Concepts (Others' Models)
* **Definition:** Summaries and breakdowns of other people's models, frameworks, theories, or book/article insights (e.g., *Continuous interviewing*, *User story maps*, *Expert generalists*).
* **Rule:** Use `category: "[[Concepts]]"` when documenting external thought leadership or objective conceptual models designed by others.

### 5. References (Objective Lookups)
* **Definition:** Permanent objective data, glossaries, taxonomies, standard cheat sheets, and structural lookup lists (e.g., *SignLab glossary*, *The five product risks*, *API Agent Stack Cheat Sheet*).
* **Rule:** Use `category: "[[References]]"` for permanent, highly functional, objective lookup documents.

### 6. Empty Stubs & Obsolete Drafts (Active Pruning)
* **Rule:** Actively prune and delete empty placeholder notes, incomplete stubs, or obsolete structural outlines (e.g. *Discovering the right problems*, *My note taking system* stubs) rather than trying to classify them. Delete them from the filesystem.

---

### Additional Boundary Distinctions

#### A. Conceptual/Methodology Notes vs. Logs
* **Linguistic Overlap:** Notes discussing "meetings," "interviews," "syncs," or "conversations" as general methodologies or abstract concepts (e.g., *Zettelkasten for product development*, *Continuous interviewing*) must stay in `/Notes/` under `category: "[[Notes]]"`. Do not naively sort them into `/Logs/Meetings/` just because their title matches keywords.
* **Meeting Prep/Agendas:** Personal talking points or draft agendas written *prior* to a meeting represent personal planning files and should reside in `/Notes/` (as `[[Notes]]` or `[[Memories]]`). Only actual collaborative records of conversations/outcomes belong in `/Logs/Meetings/` as `[[Meetings]]`.

#### B. Interaction Logs vs. Contact Profiles
* **Interaction Logs:** A quick note recording a specific interaction (e.g., "Emailed Andrew Novak about room design") contains a person's name in the title but is transactional and belongs in `/Notes/` (under `category: "[[Notes]]"` or `category: "[[Memories]]"`).
* **Contact Profiles:** Only actual profiles, bios, or contact directories (e.g., `/Contacts/Andrew novak.md`) belong in `/Contacts/` under `category: "[[People]]"`.
* *Exception:* Contact details imported or synced into `/sources/` from external systems should be migrated to `/Contacts/` under `category: "[[People]]"`.

---

## Bulk Categorization Pass Protocol
When performing large-scale triage or classification sweeps (e.g., sorting notes in batches of 10):
1. **Focus on Triage Only**: Do NOT attempt to groom, flesh out, or elaborate on the content of the notes during the sweep. Keep the momentum high. Defer detailed note grooming to later dedicated sessions.
2. **Track with Temporary State**: Add a temporary tracker like `reviewed: false` to the frontmatter of target files. Switch it to `reviewed: true` along with the category update as each batch is approved.
3. **Establish Stable Order**: Process files chronologically using the YYYYMMDDHHmmss timestamp in their ID or filename to trace the natural evolution of thoughts.

### 4. Guides/Checklists vs. Default Notes
* **Guides and Handbooks:** Technical procedures, step-by-step migration guides, or checklists (e.g., *Mixpanel to Posthog migration guide*) should be categorized as `[[References]]` (using sub-skill `obsidian-references-sources`) rather than the default `[[Notes]]`.

---

## Common Pitfalls
## Common Pitfalls
- **Multiple Categories:** Never assign multiple categories to a single note. Every note gets **exactly one** category.
- **Leaking Inbox:** Do not leave notes in `inbox/` once categorized. All processed notes must reside in their taxonomy folders.
- **Ephemeral Project Guides as References:** Do not categorize temporary checklists or migration guides tied to a specific project as `[[References]]`. References are reserved for permanent, long-term lookup documents. Project-bound checklists/guides belong under `[[Notes]]` or `[[Projects]]`.
- **Links Verification:** moves are generally safe since Obsidian auto-resolves links by note name regardless of folder structure.
