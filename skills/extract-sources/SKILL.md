---
name: extract-sources
description: An interactive workflow for compiling immutable `Inputs/Readings` into mutable, summary-focused `Notes/Sources`.
version: 1.3.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, sources, readings, pkm, synthesis]
    related_skills: [obsidian, obsidian-ingest-log, wind-down]
---

# extract-sources

## Overview

This skill facilitates the creation of "reading notes" (`Source` notes) from raw `Reading` inputs. It transforms the previous bibliographic function into an active, human-in-the-loop knowledge synthesis task.

The process is designed to be interactive. It finds unprocessed readings, allows for selection, generates a summary for preview, and upon confirmation, creates a new, properly formatted `Source` note in the `inbox/` for final triage.

## When to Use

- When you want to work through your backlog of readings and create synthesized notes.
- As part of a routine like `wind-down` to process one or two articles.
- When you have a specific topic in mind and want to find relevant readings to summarize.

## User-Requested Workflow

-   **Invocation:** The skill can be invoked manually or as a sub-skill.
-   **Selection:**
    -   *Unseeded:* Presents a random selection of 5 unprocessed `Readings`.
    -   *Seeded:* (Future) Presents readings relevant to a given keyword.
-   **Preview:** The proposed text of the new `Source` note (frontmatter + summary) is displayed in the chat for review before creation.
-   **Creation:** Upon confirmation, the new `Source` note is written to the `inbox/` directory, not directly into `Notes/Sources/`. This allows for manual review and triage.
-   **Looping:** The interactive session should offer to process another reading, get a new batch, or exit.

## Interactive Execution Steps (Native Workflow)

Do **NOT** write, execute, or maintain any Python or Shell scripts to handle this skill. Avoid spawning background subprocesses or CLI invocations of `hermes-agent prompt` or `hermes-agent delegate-task`. Perform the entire workflow natively inside your main conversation using your primary toolsets:

1. **Find Unprocessed Readings (using `terminal`):**
   Run a `ripgrep` (`rg`) command or similar in `terminal` to list files inside `Inputs/Readings/` that do not have a corresponding file with the same name in `Notes/Sources/` or `inbox/`.
2. **Present a Selection (using `clarify`):**
   Take a random sample of 5 unprocessed reading file paths, and present their names as choice items to the user via the `clarify` tool.
3. **Read File Content (using `read_file`):**
   Once the user selects a reading, use the `read_file` tool to read the entire text content.
4. **Generate Summary (Natively):**
   Do **NOT** call external models or subprocesses. Generate the summary natively in your own thinking process. Format the note content with:
   - Frontmatter containing:
     - `id`: Unique timestamp ID (YYYYMMDDHHMMSS).
     - `daily_note`: Wikilink to today's daily note (e.g. `[[2026-06-11 Thursday]]`).
     - `category`: `[[Sources]]`.
     - `reading`: Wikilink to the raw reading file.
   - Markdown header with the reading title.
   - A structured, insightful Markdown summary of the reading.
5. **Show Preview & Confirm (using `clarify`):**
   Present the exact generated Markdown file content to the user in the chat, and use the `clarify` tool with multiple choice options ("Yes, create it" and "No, cancel") to get explicit confirmation.
6. **Create the Note (using `write_file`):**
   Upon explicit user confirmation, write the completed Markdown note to the vault's `inbox/` path.
7. **Offer to Loop (using `clarify`):**
   Ask if they want to process another reading, pull a fresh batch, or finish.

## Implementation Pitfalls & Lessons Learned

-   **Discovery of Unprocessed Readings:**
    -   *Failed Approach:* An initial attempt to use a complex, stateful Python script with `os.walk` to find unprocessed readings by checking for backlinks proved fragile and difficult to debug.
    -   *Correct Approach:* Use a simple, stateless `terminal` invocation with `ripgrep` (`rg`) or `find` to check the filesystem directly.

-   **Subprocess Inception (CRITICAL PITFALL):**
    -   *Problematic:* Writing a script that calls a subprocess invoking the `hermes-agent` CLI is an extreme anti-pattern. Banners, status updates, and decorative outputs from the CLI pollute `stdout` captures and corrupt the programmatic parse blocks, causing catastrophic loop failures and 404 model mismatches.
    -   *Rule:* **Never call `hermes-agent` inside a script.** Always stay native and handle reasoning/text generation directly in your own active context. If you need text summarized, read the file and summarize it yourself.