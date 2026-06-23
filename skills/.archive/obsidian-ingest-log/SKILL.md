---
name: obsidian-ingest-log
description: Logs new vault inputs and updates related project notes. Called by ingest skills (email, Slack, etc.) to ensure every new artifact is tracked.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, ingest, log, projects, entities]
    related_skills: [obsidian, bes-email-dispatch, bes-slack-ingest, bes-linear-ingest, bes-granola-ingest]
---

# obsidian-ingest-log

## Overview

This skill handles the immediate, lightweight integration steps that must happen every time a new input artifact is added to the vault. Its purpose is to ensure every new item is logged for traceability and that relevant project notes are updated with any new status information.

This skill combines the `integrate-light` and `integrate-entities` workflows from the deprecated `llm-wiki` skill.

## When to Use

This skill should be called as the final step by any other skill that creates a new note in the `Inputs/` directory (e.g., `bes-email-dispatch`, `bes-slack-ingest`). It is not intended to be used directly by a user in most cases.

## Workflow

The process consists of two main parts, executed sequentially.

### 1. Log Append (`integrate-light`)

A one-line entry is appended to the vault's central log file to record the ingestion event.

1.  **Target File:** `Utilities/log.md` (This file will be created from a template if it does not exist).
2.  **Log Format:** A single line is appended containing the timestamp, type of ingest, a wikilink to the new note, the note's path, and a wikilink to the corresponding daily note.
3.  **Immutability:** This process *never* modifies the body of the ingested input file. Inputs are immutable.

### 2. Entity Integration (`integrate-entities`)

After logging, the system attempts to connect the new input to existing project notes.

1.  **Script:** Runs `integrate_entities.py` on the newly ingested note.
2.  **Action:** The script scans the note for keywords or IDs that link it to known projects. If a definitive link is found, the `## State` section of the corresponding project note (`Notes/Projects/<Project Name>.md`) is updated with a brief summary of the new information (e.g., status changes, decisions).
3.  **Constraints:**
    - This is an **update-only** operation. It will never create new project notes or stubs.
    - Automated timeline entries are disabled in favor of Obsidian's native backlinks. Only the `## State` section is modified.

## Pitfalls

-   **Skipping this step:** Failing to run this skill after an ingest makes the new file untraceable and breaks the vault's chronological audit trail.
-   **Modifying Input bodies:** Input files under `Inputs/` must remain immutable. All commentary or summary should happen in other notes (like Project notes or Source notes).