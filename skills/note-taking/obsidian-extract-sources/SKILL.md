---
name: obsidian-extract-sources
description: Use when creating or recording cheat sheets, factsheets, guidelines, or other people's conceptual summaries under Notes/. Also contains the workflow for compiling immutable `Inputs/Readings` into mutable `Notes/Sources`.
version: 1.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, references, sources, readings, compile]
    related_skills: [obsidian, obsidian-ingest-log, obsidian-suggest-promotions]
---

# obsidian-extract-sources

## Overview

This skill has two primary functions:

1.  Creating general reference notes like cheat sheets, factsheets, and summaries of external concepts.
2.  Executing the formal workflow for compiling raw, immutable `Inputs/Readings` into refined, mutable `Notes/Sources` that can be linked to from other parts of the vault.

This skill absorbs the `integrate-full` workflow from the deprecated `llm-wiki` skill.

## When to Use

-   When Justin asks to create a reference note, cheat sheet, or factsheet.
-   When explicitly triggered to process the day's or a specific project's readings ("compile today's readings", "extract sources for [[Project]]").
-   As a step in the `wind-down` ritual.

## Readings → Sources Workflow

This is the formal process for promoting a raw input into a structured source that can be used for synthesis.

**Trigger:** Manual, on-demand. Not run from cron automatically.

**Process:** For each `Reading` note in scope, create or update a corresponding `Source` note in `Notes/`.

### Source Note Template

```yaml
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Sources]]"
---

# Title of Source Material

- **Author:** [Author Name]
- **URL:** [Original URL]
- **Type:** book | article | paper | video

## Summary
A Bes-compiled synthesis of the key ideas from the raw input. This summary is kept up-to-date by subsequent runs of this skill.

## Raw inputs
- [[Link to the original Reading note]]

## Related
- [[Links to Concepts or Projects that use this source]]
```

### Key Principles

-   **Link Direction:** The proper link hierarchy is `Concept` → `Source` → `Reading`. Never link a `Concept` or `Thought` directly to a `Reading` if a `Source` note for it exists.
-   **Confirmation:** Always confirm with Justin before performing bulk creations or edits of `Source` notes.
-   **Atomicity:** Each `Source` note should correspond to a single `Reading`.

## Pitfalls

-   **Compiling into Reading bodies:** `Inputs` are immutable. The compiled summary and metadata belong exclusively in the `Source` note.
-   **Linking directly to Readings:** Bypassing the `Source` note breaks the intended knowledge graph structure and makes it difficult to track how raw information is synthesized.
-   **Automatic Execution:** This workflow requires judgment and synthesis, and should not be run automatically from cron without explicit approval for the batch.