---
name: obsidian-vault-jam
description: On-demand interactive collaborative session to run vault hygiene/enrichment, discover new notes, suggest connections, and promote thoughts to beliefs. Can be run completely unseeded or seeded with a specific topic.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, vault-jam, interactive, notes, suggest-links, suggest-notes, promotions]
    related_skills: [obsidian, obsidian-suggest-new-notes, obsidian-suggest-links, obsidian-suggest-promotions, obsidian-graph-enrichment, obsidian-utilities]
---

# Obsidian: Vault Jam Session

## Overview
A **Vault Jam** is an interactive, on-demand collaborative session with Justin to perform intensive maintenance, gardening, and creative connection-building inside his Obsidian vault. Unlike the morning briefing, it is never automated — it is invoked explicitly when Justin wants to "jam" on his notes.

---

## The Workflow Loop

When a Vault Jam is initiated, follow these four phases sequentially. 
*   **Batching Rule:** For Phases 2, 3, and 4, always present exactly **5 suggestions** at a time. After presenting and processing a batch of approvals, **ask Justin if he wants to see another batch of 5 for that phase, or move on to the next phase.** Repeat this loop until he instructs you to move to the next phase.
*   **Seeding Rule:** If Justin specifies a topic for the Vault Jam (e.g., "Let's do a vault jam around *special ed strategy*"), **seed every component loop with that topic** using the seeding flags and logic defined below.

---

## Phase 1 — Graph & Entity Enrichment

Before proposing connections, run a diagnostic scan and check for newly mentioned contacts.

1.  **Run Vault Hygiene:** Execute the hygiene diagnostics:
    `python3 ~/.hermes/scripts/vault_hygiene.py`
2.  **Present Summary:** Summarize any unresolved layout issues, duplicate IDs, or entity mentions discovered. Proactively resolve simple fixes (like moving misplaced daily notes to `/Daily Notes/`) and report what was resolved.
3.  **Entity Candidates:** Present any newly discovered, unresolved contact or organization link candidates (if any were flagged). Offer to initialize them now before proceeding.
4.  **Review Slack Logs (Enrichment):** Find any Slack logs (`Logs/Slack/*.md`) created since the previous vault enrichment run. For each newly created log:
    *   Read the original conversation/thread if needed.
    *   Synthesize a brief, **2-3 sentence Topic Description** as a pointer.
    *   Compile the final list of **main participants** and update the frontmatter `participants` list.
    *   **Enforce the Constraints:** Remove any point-by-point summaries, quotes, thoughts, or decisions from the note's body, replacing them strictly with the simple Topic Description pointer format.

---

## Phase 2 — Suggest New Notes

Identify conceptual gaps, insights, or missing definitions in recent logs and initialize stubs in the `Inbox/`.

1.  **Execution (Unseeded):** Scan recent logs for the last 48 hours using the lookback script:
    `python3 ~/.hermes/skills/note-taking/obsidian-suggest-new-notes/scripts/scan_recent_logs.py --hours 48`
2.  **Execution (Seeded):** If a seed topic was specified, scan logs but **bias your analysis heavily toward logs, clips, or meeting agendas matching the seed keyword**. (You can search the vault for log mentions of the keyword using `search_files(target='content', path='/home/justin.guest/vault/Logs', pattern='[keyword]')` to gather extra material if the 48-hour scan is too sparse).
3.  **Pitch Format:** Present exactly **5 candidate stubs** with their categories and 1-2 sentence rationales linking them back to logs.
    *Example:* `1. [[Proposed Title]] (category: "[[Thoughts]]")`
4.  **Creation:** Write approved note stubs into `/home/justin.guest/vault/Inbox/` using valid YAML frontmatter and standard templates matching their target category (Thoughts, Sources, Decisions, Notes). Ensure they follow the correct naming format (`ID Title.md` for Thoughts, Sources, Decisions, Notes).
5.  **Loop/Advance:** Process approvals, write files, then ask Justin: *"Would you like to see another 5 new note suggestions, or move on to Phase 3: Suggest Links?"*

---

## Phase 3 — Suggest Links

Surface surprising cross-connections among your existing Thoughts and Beliefs to grow the depth of your graph.

1.  **Execution (Unseeded):** Run the link-generation script to sample notes:
    `python3 ~/.hermes/skills/note-taking/obsidian-suggest-links/scripts/suggest_connections.py`
2.  **Execution (Seeded):** If a seed topic was specified, pass the seed flag to bias connection suggestions toward the topic:
    `python3 ~/.hermes/skills/note-taking/obsidian-suggest-links/scripts/suggest_connections.py --seed "[topic]"`
3.  **Pitch Format:** Present exactly **5 connection candidates** in the strict unidirectional direction (Thought $\rightarrow$ Thought, Thought $\rightarrow$ Belief, Belief $\rightarrow$ Belief).
    *Example:* `1. [[Source Note]] -> [[Target Note]]`
4.  **Writing Links:** Write approved links back to the source notes under a `## Connections` section using targeted `patch` edits.
5.  **Loop/Advance:** Process approvals, write links, then ask Justin: *"Would you like to see another 5 connection suggestions, or move on to Phase 4: Suggest Promotions?"*

---

## Phase 4 — Suggest Promotions

Evaluate which notes are ready to be promoted up the hierarchical tiers (Note/Source $\rightarrow$ Thought $\rightarrow$ Belief).

1.  **Execution (Unseeded):** Run the candidate discovery script to pull notes and backlinks:
    `python3 ~/.hermes/skills/note-taking/obsidian-suggest-promotions/scripts/get_promotion_candidates.py`
2.  **Execution (Seeded):** If a seed topic was specified, pass the seed topic to bias candidates:
    `python3 ~/.hermes/skills/note-taking/obsidian-suggest-promotions/scripts/get_promotion_candidates.py --seed "[topic]"`
3.  **Pitch Format:** Present exactly **5 promotion pitches** with backlinks context.
    *Example:* `1. [[Current Note]] -> Promote to [[Beliefs]]`
4.  **Promotion & Transition:** For approved notes:
    *   Change the frontmatter `category: "[[<NewCategoryName>]]"`.
    *   **Adjust Naming:** Adjust the filename on disk to match the category naming rules (remove timestamp prefix for Beliefs, ensure timestamp prefix exists for Thoughts/Notes).
    *   **Belief Synthesis:** For Thoughts $\rightarrow$ Beliefs, synthesize and append **Core Tenets** and **Application** guidelines.
    *   **Enforce Link Hygiene:** Scan outgoing links of the promoted note to flag and resolve downward link violations.
5.  **Loop/Conclude:** Process approvals, then ask: *"Would you like to see another 5 promotion suggestions, or shall we conclude this Vault Jam session?"*

---

## Verification & Guardrails
- **No duplicates:** Always run a quick duplicate check before creating any new notes.
- **Unidirectional links:** Never allow a Belief to link to a Thought or raw Tier 1 note.
- **Symmetrical frontmatter:** Double check that any updated or newly written note contains a standard `daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"` link.
