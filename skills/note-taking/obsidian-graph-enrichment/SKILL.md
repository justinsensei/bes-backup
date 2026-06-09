---
name: obsidian-graph-enrichment
description: Principles and link hierarchy conventions for maintaining a clean note graph, tracking chronological thinking evolution, and using semantic AI memory integration in Obsidian.
version: 1.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, link-hierarchy, graph, note-enrichment, thoughts, beliefs, semantic-search, embeddings]
    related_skills: [obsidian, obsidian-thoughts-beliefs, obsidian-notes]
---

# Obsidian: Graph Enrichment & Link Hierarchy

- **Linked References:**
  - **[Semantic Pointer Implementation](references/semantic-pointer-implementation.md):** Tech schema, batching mechanism, and sqlite-vec reference.

## Overview
This skill governs the conventions for link directions and relationship structures between different tiers of notes in Justin's Obsidian vault. By enforcing a unidirectional link hierarchy, we keep high-level notes clean and leverage Obsidian's native backlinks to construct effortless, zero-maintenance historical timelines of thinking.

---

## Note Tier Hierarchy
Justin's notes are organized into a hierarchy of permanence and synthesis. Chronological logs (including Daily Notes, Meetings, and Sources) are treated as Tier 1 raw inputs. Links should flow **from less-permanent notes to more-permanent notes** (pointing upwards in synthesis):

```
+--------------------------------------------+
|  Tier 1 (Raw/Ephemeral Inputs / Logs)      |
|  - Notes, Concepts, Decisions, Memories,    |
|    Daily Notes, Meetings, Sources          |
+---------------------+----------------------+
                      | (can link to other Tier 1 notes
                      |  or pointing UPWARDS to T2 / T3)
                      v
+--------------------------------------------+
|  Tier 2 (Emergent/Synthesized Thoughts)    |
|  - Thoughts                                |
+---------------------+----------------------+
                      | (can link to other Tier 2 notes
                      |  or pointing UPWARDS to T3)
                      v
+--------------------------------------------+
|  Tier 3 (Permanent/Conviction Beliefs)     |
|  - Beliefs                                 |
+--------------------------------------------+
```

### The Rules of Link Direction

1. **Tier 1 (Notes, Concepts, Decisions, Memories, Daily Notes, Meetings, Sources):**
   - Can link to **one another** (e.g., a Decision linking to a Source, or a Daily Note linking to a Note).
   - Can link to **any note below** in the hierarchy (Thoughts and Beliefs).
2. **Tier 2 (Thoughts):**
   - Can link to **one another** (e.g., a Thought linking to another Thought).
   - Can link to **Beliefs** (Tier 3).
   - *Should NOT link back up to Tier 1 notes.*
3. **Tier 3 (Beliefs):**
   - Can link to **one another** (e.g., a Belief linking to another Belief).
   - *Should NOT link back up to Thoughts or Tier 1 notes.*

*Note: Linking between conceptual tiers (Thoughts to Thoughts, Thoughts to Beliefs, or Beliefs to Beliefs) is a reasoning-heavy task and is **NOT automated** by the signals script. Agents must manually establish or propose these conceptual links when drafting, editing, or organizing notes for Justin, following this strict direction rule.*

---

## Implications & Design Decisions

### 1. Backlinks as the Timeline
Rather than manually updating a high-level Thought or Belief to list all resources, events, or decisions associated with it:
- Link *from* the specific Tier 1 note (e.g., a meeting log or reading clipping) *to* the high-level Thought/Belief.
- Use Obsidian's **Backlinks Pane** on the Thought or Belief note to view the chronological evolution of that idea over time.
- **Timeline Ordering:** No date prefixes or timestamps are required in the filenames of Tier 1 notes (Notes, Concepts, Decisions, Memories) to maintain a chronological timeline. Instead, rely entirely on Obsidian's native **Backlinks pane sorting** (e.g., sorting the list by "Created time" or "Modified time") to view the chronological progression of ideas over time. This preserves clean, normal-spaced capitalized titles across the entire vault without sacrificing the temporal view.

### 2. Low-Friction Writing
- It is always easier to link *from* what you are currently writing (the context of today's work or a newly encountered source) *to* a pre-existing stable concept. You do not need to interrupt your flow to edit a long-standing permanent note.

### 3. Clear Separation of Opinions vs. Principles
- **Thoughts** (Category: `[[Thoughts]]`) are emergent, open reflections, research questions, or current opinions.
- **Beliefs** (Category: `[[Beliefs]]`) are highly trusted, semi-permanent frameworks, convictions, or proven mental models.
- Concepts must prove their durability to move from a Thought to a Belief.

---

## Automated Entity Enrichment (Vault Signals)
While conceptual entities (Thoughts, Beliefs) rely on manual backlinks to form timelines, physical entities (Contacts/People, Organizations) and Projects utilize an automated enrichment mechanism.

### How It Works (`check_vault_signals.py`)
A scheduled script scans the vault for modified markdown files since the last run watermark and enriches existing entity notes automatically:

1. **Entity Directory Mapping:**
   - **People & Organizations:** Managed under `/Contacts/` with categories `[[People]]` and `[[Organizations]]`.
   - **Projects:** Managed under `/Notes/` with category `[[Projects]]` and `type: project` frontmatter.

2. **Trigger-on-Mention Detection:**
   - The script matches text inside newly modified files against existing entity names, their filenames, or configured `aliases` (defined in the entity's frontmatter).
   - Both explicit wikilinks (e.g., `[[Dave Rohrl]]`) and plain-text mentions (e.g., "shared this with Dave Rohrl") trigger enrichment.

3. **Automatic Timeline Appending:**
   - When a match is found, the script automatically writes a timestamped reference to the target entity's `## Timeline` section:
     ```markdown
     ## Timeline
     - YYYY-MM-DD | Mentioned in [[Path/To/Source-Note|Source Note Title]]
     ```
   - This ensures a zero-effort log of interactions, source clippings, and project meetings accumulates directly in the contact's or project's note.

3.  **Candidate Discovery (Unresolved Links):**
   - The script also extracts unresolved wikilinks (e.g., `[[John Doe]]` when no `John Doe.md` file exists).
   - These are surfaced as candidate entities during the Morning Briefing, giving Justin a simple, one-click way to initialize new Contacts.

4.  **Slack Ingestion & Inbox-First Landing:**
   - Ingested notes triggered by Slack custom emoji reactions (`:jg_log:` for standard logs, `:jg_decision:` for decisions) are always written directly into the `/inbox/` folder first (e.g., `inbox/YYYY-MM-DD - Slack - [Title].md` or `inbox/YYYY-MM-DD - Decision - [Title].md`).
   - Standard Slack logs are kept **minimalist** upon creation, containing only frontmatter metadata (participant lists, source links) and a brief, 2-3 sentence Topic Description.
   - During subsequent vault enrichment, triage, or Vault Jam runs:
     - Review newly created Slack logs from `/inbox/` or `/Logs/Slack/`.
     - Refine and write a polished **2-3 sentence Topic Description** pointer.
     - Compile the complete list of **main participants** and update the frontmatter `participants` list.
     - **Enforce the Constraints:** Remove any point-by-point summaries, individual thoughts, quotes, or decisions from standard Slack log bodies, keeping them strictly as lightweight pointers. (Pointers can link to formal Decisions or Thoughts, but must not replicate their details internally).

---

## Semantic Pointer & AI Memory Integration

The Semantic Pointer is a high-performance, lightweight local semantic memory utility designed to solve the **Synonym Problem** (regex failing to map synonyms) and the **Historical Blindspot** (new thoughts lacking retrospective links to old archived logs).

### System Script Details
- **Path:** `~/.hermes/scripts/semantic_pointer.py`
- **Database:** `~/.hermes/state/semantic_memory.db` (utilizes `sqlite-vec` extension and `gemini-embedding-2` embeddings).
- **Indexing Speed:** Multi-file parallel batching indexes **180+ files per minute**.

### Key Workflows

#### 1. On-Demand Historical Bridging
When writing or reviewing a Tier 2 Thought or Tier 3 Belief note, use the Semantic Pointer to retroactively scan older Tier 1 logs (Meetings, Sources, Slack, Daily Notes) and automatically append/update a clean, markdown-compliant `## Related Logs` block at the bottom of the note:
```bash
python3 ~/.hermes/scripts/semantic_pointer.py bridge "vault/Notes/Target Note.md" --limit 5 --commit
```

#### 2. Semantic Context Pruning (Synthesis)
For synthesis, research, or summarization tasks, instead of flooding your context window with entire log files, pull the most semantically dense, highly-relevant paragraphs from across the entire vault history using context pruning:
```bash
python3 ~/.hermes/scripts/semantic_pointer.py prune "your search topic" --limit 10
```

#### 3. General Semantic Search
Run vector similarity queries across either full documents (`--type doc`) or individual paragraph chunks (`--type para`):
```bash
python3 ~/.hermes/scripts/semantic_pointer.py search "search query" --type doc --limit 5
```


