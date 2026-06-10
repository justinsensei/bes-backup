---
name: obsidian-thoughts-beliefs
description: Use when creating or recording unstructured personal reflections, emergent ideas, or core guiding beliefs and evolved concepts/thoughts under Notes/.
version: 1.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, notes, thoughts, beliefs, mental-models, audit]
    related_skills: [obsidian, obsidian-notes, obsidian-graph-enrichment, obsidian-categorize-and-sort]
---

# Obsidian: Thoughts & Beliefs Log

## Overview
This skill governs the categorization, formatting, and capture of unstructured personal reflections and emergent ideas (`Thoughts`), and evolved concepts / thoughts that are durably true and shape action (`Beliefs`).

---

## Folder & Category
- **Directory:** `/home/justin.guest/vault/Notes/`
- **Categories & Naming:**
  - **Thoughts:** Thoughts are *my thinking* — raw personal reflections, emergent theories, or open questions.
    - Category link: `category: "[[Thoughts]]"`
    - Filename format: `ID Title.md` (e.g. `20260609120000 Spaced Title.md`).
  - **Beliefs:** Beliefs are *evolved* concepts / thoughts — things that are durably true and shape what Justin does and how he sees the world.
    - Category link: `category: "[[Beliefs]]"`
    - Filename format: `Title.md` (no timestamp prefix, e.g. `Spaced Title.md`).

---

## Note Structures

### Thoughts (Emergent/Reflective Notes)
Thoughts notes capture reflections, opinions, or ideas. They are open, structured, or semi-structured scratchpads.

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
- Emergent observations...
- Open questions...
```

### Beliefs (Evolved Concepts/Thoughts)
Beliefs are *evolved* concepts / thoughts — things that are durably true and that shape what Justin does and how he sees the world. Mature beliefs follow the structured format formalized in `Willpower is limited 20250626165159.md`:

```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Beliefs]]"
---

# Spaced Capitalized Belief Title

Core thesis or definition paragraph. Concise, high-level statement of what this belief represents.

Optional secondary elaboration paragraph providing deeper conceptual context or explaining the underlying mechanics.

---

## Core Tenets
1. **[Tenet 1 Name]:** Concise description of the first fundamental pillar or rule supporting this belief.
2. **[Tenet 2 Name]:** Concise description of the second pillar.
3. **[Tenet 3 Name]:** Concise description of the third pillar.

## Application
- **[Domain/Scenario A]:** Specific guideline on how this principle is put into practice in daily life, work, or decision-making.
- **[Domain/Scenario B]:** Practical application rule or playbook instruction.

---

## Related
* [[Related Note A]]
* [[Related Note B]]

## Sources
* [[Source Note or Book Link]]
```

---

## Reversion & Promotion Constraints (June 2026)
- **Default to Notes:** Mass or manual promotion of existing notes to Thoughts and Beliefs has proven unsatisfactory and was completely reverted in June 2026. All conceptual and personal reflection notes must default to `category: "[[Notes]]"`.
- **Strict Exception:** Only highly structured, long-conviction mental models (such as `Willpower is limited`) should remain or be categorized as `category: "[[Beliefs]]"`.
- **Naming Enforcement on Reversion:** When reverting Thoughts/Beliefs back to Notes, ensure their filename includes the proper 14-digit `ID ` prefix (e.g. `20250523170601 Title.md`), utilizing the `id` field from the note's frontmatter.
- **Do Not Push Promotion:** Never automatically or proactively migrate notes to `Thoughts` or `Beliefs` without explicit user request.

---

## Auditing & Reversion Workflow

When performing a manual or programmatic audit to prune or downgrade category classifications:

### 1. Identify Candidates
Scan notes for high-probability "fleeting, tactical, or operational" traits:
- Contains the `#quick_note` tag or similar fleeting markers.
- Short body length (typically under 400-500 characters).
- Contains checklists (`- [ ]`, `- [x]`) or todo planning indicators.
- Contains highly transactional language (e.g., "emailed", "Slack thread link", "1-on-1 prep", "PostHog/Mixpanel telemetry tracking logs").

### 2. Presentation & Batching Rules
- **Omit Redundant Data:** Do not include a "Current Category" column or line in your proposals if all notes being evaluated share the same starting category.
- **Flag Candidate Counts:** Inform the user of the total candidate count found across the vault first.
- **Batching Threshold:** If there are more than 10 candidates, state the count and present them in batches of exactly 10 for user approval.
- **Diverse Proposals:** Do not default to classifying everything as `[[Notes]]`. Proactively suggest more descriptive categories like `[[Concepts]]`, `[[References]]`, `[[Beliefs]]`, `[[Thoughts]]`, or `[[Memories]]` for entries that capture established, reusable decision patterns, theories, or milestones.


