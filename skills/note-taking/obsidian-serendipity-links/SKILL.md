---
name: obsidian-serendipity-links
description: Core skill to suggest and establish conceptual links among Thoughts and Beliefs using a randomized or seeded serendipity engine, then write approved connections back to Obsidian notes.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, link-suggestions, serendipity, notes, thoughts, beliefs]
    related_skills: [obsidian, obsidian-graph-enrichment, obsidian-thoughts-beliefs]
---

# Obsidian: Serendipity Links

## Overview
This skill provides a randomized/seeded discovery mechanism to help Justin surface surprising cross-connections between existing ideas (`Thoughts` and `Beliefs`) in his vault. It runs an interactive loop where the agent samples notes, pitches exactly 5 candidate connections matching the link hierarchy, and updates the notes with any approved links.

---

## The Link Rules (Constraint Filter)
Suggested links must strictly follow the unidirectional hierarchy defined in `obsidian-graph-enrichment`:
- **Thought** $\rightarrow$ **Thought** (Valid)
- **Thought** $\rightarrow$ **Belief** (Valid)
- **Belief** $\rightarrow$ **Belief** (Valid)
- *Never point a Belief to a Thought, or a Thought/Belief to a raw Tier 1 note.*

---

## Execution Modes

### 1. Manual / On-Demand Invocation
- **Triggers:** Justin asks to "run serendipity links", "suggest new connections", or "spark some ideas".
- **Step 1:** Run `python3 ~/.hermes/skills/note-taking/obsidian-serendipity-links/scripts/suggest_connections.py` to sample 12–15 notes.
- **Step 2:** Analyze the sampled notes and pitch exactly 5 connection candidates (see "Pitch Format" below).
- **Step 3:** Prompt Justin to choose which ones to approve.
- **Step 4:** For each approved link, write it to the source note (see "Writing Approved Links" below).
- **Step 5:** Ask Justin if he would like to run another loop.

### 2. Passing a Seed Topic
- **Triggers:** Justin says "suggest connections around [topic]" or "run serendipity links for [topic]".
- **Step 1:** Run `suggest_connections.py --seed "[topic]"` to pull 6 topic-matching notes mixed with 6 completely random notes.
- **Step 2:** Pitch exactly 5 connection candidates that bridge the seed topic with other ideas.
- **Step 3:** Follow the same approval and writing flow, then ask if they want to run another loop.

### 3. Integrated / Semi-Automated Process (e.g. Morning Briefing)
- **Triggers:** Automatically invoked during a multi-phase briefing.
- **Step 1:** Run `suggest_connections.py` without a seed.
- **Step 2:** Pitch exactly 5 connection candidates.
- **Step 3:** Follow the same approval and writing flow.
- **Step 4:** Transition directly to the next phase of the briefing (do NOT ask to run another loop).

---

## Suggestion & Pitch Format
When pitching connections, output them as a numbered list with the following shape:
1. **[[Source Note Title]]** $\rightarrow$ **[[Target Note Title]]**
   - **Why:** A compelling, 1-2 sentence spark explaining how these two specific ideas intersect, build upon, or challenge each other.

---

## Writing Approved Links
When Justin approves one or more links, update the source note using `patch`:
1. Check if the source note already has a `## Connections` section.
2. If it does, append the new link at the bottom of that section as a bullet:
   `- [[Target Note Title]] — Why: [1-2 sentence spark]`
3. If it does not, append a new section at the end of the file:
   ```markdown
   
   ---

   ## Connections
   - [[Target Note Title]] — Why: [1-2 sentence spark]
   ```
4. Perform the file edit using `patch` (never overwrite the entire file with raw echo or cat).
5. Confirm the edit succeeded and report back cleanly.
