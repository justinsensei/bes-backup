---
name: obsidian-suggest-promotions
description: Suggest existing notes for promotion up the hierarchy (raw Note/Source -> Thought -> Belief) using semantic analysis, synthesize backlinked context for thoughts -> beliefs, and enforce link hygiene.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, suggest-promotions, thoughts, beliefs, graph-hygiene]
    related_skills: [obsidian, obsidian-notes, obsidian-thoughts-beliefs, obsidian-graph-enrichment]
---

# Obsidian: Suggest Promotions

## Overview
This skill governs the semantic evaluation and promotion of notes up Justin's unidirectional three-tier vault hierarchy:
1. **Tier 1 (Raw/Ephemeral Inputs):** `[[Notes]]`, `[[Sources]]`, `[[Decisions]]`, `[[Memory]]`
2. **Tier 2 (Emergent/Synthesized Thoughts):** `[[Thoughts]]`
3. **Tier 3 (Permanent/Conviction Beliefs):** `[[Beliefs]]`

By analyzing the depth of a note's content and its usage across the vault (via backlinks), Bes identifies notes ready for promotion, drafts synthesized tenets for mature beliefs, and runs link hygiene checks to prevent downward link violations.

---

## When to Use
- **Trigger:** Justin asks to "suggest notes for promotion", "check what needs promotion", "promote some thoughts", or "run note promotion".
- **Rule:** Presents exactly **5 suggestions** per batch.
- **Don't use for:** Brainstorming brand new notes (use `obsidian-suggest-new-notes` instead) or establishing horizontal connections (use `obsidian-suggest-links` instead).

---

## Execution Flow

### Step 1: Get Promotion Candidates
Run the candidate discovery script to pull a pool of Tier 1 and Tier 2 notes along with their backlinks:
`python3 ~/.hermes/skills/note-taking/obsidian-suggest-promotions/scripts/get_promotion_candidates.py`
*(Supports a seed topic keyword if Justin specifies one: `--seed "[topic]"`).*

### Step 2: Semantic Analysis
Analyze the returned notes and their backlink snippets to choose exactly **5 promotion recommendations**:
- **Tier 1 $\rightarrow$ Tier 2 (Note/Source $\rightarrow$ Thought):** Select notes that have transitioned from a simple copy-paste clipping or scratchpad into an active research question, opinion, or emergent theory.
- **Tier 2 $\rightarrow$ Tier 3 (Thought $\rightarrow$ Belief):** Select thoughts that represent highly trusted, stable, foundational mental models or playbooks that Justin frequently backlinks to or cites across multiple meetings or daily notes.

### Step 3: Present the Pitch
Present the 5 suggestions as a numbered list in this exact format:
1. **[[Current Note Title]]** $\rightarrow$ Promote to **[[Thoughts]]** (or **[[Beliefs]]**)
   - **Reasoning:** 1-2 sentences on why its content and backlink profile justify promotion.
   - **Backlink Synthesis Context:** Bulleted list of places it's linked, summarizing the evolution of this idea (e.g., *"Clipped from Reforge, referenced in 2 weekly syncs and 1 decision"*).

### Step 4: Approval & Transition
Ask Justin which promotions he wants to approve. For each approved note:
1. **Change Category:** Use `patch` to update the YAML `category: "[[<NewCategoryName>]]"` property.
2. **For Thoughts $\rightarrow$ Beliefs (Tier 2 $\rightarrow$ Tier 3):**
   - Synthesize the note's original body and all backlinked meeting/daily notes context to draft a high-quality, mature structure.
   - Draft **Core Tenets** (3 numbered, actionable pillars with bolded names) and **Application** guidelines (2 bulleted scenarios with bolded context).
   - Append these sections at the bottom of the file (under a horizontal rules `---` divider).
3. **Run Link Hygiene Check:** Scan the promoted note's *outgoing links*. Since higher-tier notes *must not* link downward to lower tiers:
   - Identify any outgoing links pointing to raw Tier 1 notes (if promoting to Thought or Belief) or Tier 2 thoughts (if promoting to Belief).
   - Flag these downward links for Justin, or propose replacing them with plain text (e.g. converting `[[Raw Note]]` to plain text `Raw Note`) to preserve unidirectional flow.
4. **Save Changes:** Perform the updates cleanly using `patch` and confirm success.

---

## Example Promotion Output (Thoughts $\rightarrow$ Beliefs)
When a Thought is promoted, append the synthesized sections:

```markdown
---

## Core Tenets
1. **[Tenet 1 Name]:** Concise description of the first fundamental pillar or rule supporting this belief.
2. **[Tenet 2 Name]:** Concise description of the second pillar.
3. **[Tenet 3 Name]:** Concise description of the third pillar.

## Application
- **[Domain/Scenario A]:** Specific guideline on how this principle is put into practice in daily life, work, or decision-making.
- **[Domain/Scenario B]:** Practical application rule or playbook instruction.
```

---

## Common Pitfalls
1. **Ignoring Link Hygiene:** Promoting a note to a Belief while leaving outgoing links to random raw meeting notes violates the unidirectional graph rule. You *must* flag and clean up downward links.
2. **Generic Tenets:** For Thoughts $\rightarrow$ Beliefs promotions, do not use generic placeholder tenets. Read the backlinked context and write highly specific, tailored principles matching Justin's product management style.

---

## Verification Checklist
- [ ] Candidates and their backlinks gathered successfully
- [ ] Exactly 5 promotion pitches presented with synthesized context
- [ ] YAML `category` property updated successfully via targeted patch
- [ ] For Beliefs: Actionable Core Tenets and Applications drafted and appended
- [ ] Link Hygiene check executed on all outgoing links and violations resolved or reported
