---
name: obsidian-thoughts-beliefs
description: Use when creating or recording unstructured personal reflections, emergent ideas, or core guiding beliefs and mental models under Notes/.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, notes, thoughts, beliefs, mental-models]
    related_skills: [obsidian, obsidian-notes, obsidian-graph-enrichment]
---

# Obsidian: Thoughts & Beliefs Log

## Overview
This skill governs the categorization, formatting, and capture of unstructured personal reflections, emergent product ideas (`Thoughts`), and core guiding principles or mental models (`Beliefs`).

---

## Folder & Category
- **Directory:** `/home/justin.guest/vault/Notes/`
- **Categories:**
  - Raw personal reflections, emergent theories, or open questions: `category: "[[Thoughts]]"`
  - Trusted frameworks, core guiding principles, or proven mental models: `category: "[[Beliefs]]"`

---

## Note Structures

### Thoughts (Emergent/Reflective Notes)
Thoughts notes capture reflections, opinions, or ideas. They are open, structured, or semi-structured scratchpads.

```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[Daily Notes/YYYY-MM-DD-weekday|YYYY-MM-DD Weekday]]"
category: "[[Thoughts]]"
---

# Spaced Capitalized Thought Title

What is the core idea or reflection? Keep it atomic.

---

## Context & Details
- Emergent observations...
- Open questions...
```

### Beliefs (Guiding Principles/Mental Models)
Beliefs notes capture highly trusted, semi-permanent ideas, frameworks, and principles that shape Justin's product management playbook or personal standards. Mature beliefs follow the structured format formalized in `Willpower is limited 20250626165159.md`:

```markdown
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[Daily Notes/YYYY-MM-DD-weekday|YYYY-MM-DD Weekday]]"
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
