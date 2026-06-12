---
name: extract-source
description: An interactive workflow for compiling an immutable `Inputs/Reading` into a mutable, synthesis-focused `Notes/Source`.
version: 2.1.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, sources, readings, pkm, synthesis, knowledge-integration]
    related_skills: [obsidian, obsidian-ingest-log, synthesize-notes, web]
---

# extract-source

## Overview

This skill facilitates the creation of a "reading note" (`Source` note) from a raw `Reading` input. It transforms the previous bibliographic/summary function into an active, human-in-the-loop knowledge integration task.

The process is designed to be interactive. It finds unprocessed readings, allows for selection, ingests the full text from the source URL, generates a synthesis by comparing the reading's concepts against the existing vault, and upon confirmation, creates a new, properly formatted `Source` note in the `inbox/` for final triage.

## When to Use

- When you want to work through your backlog of readings and create synthesized notes that connect to your existing knowledge base.
- As part of a routine like `wind-down` to process one or two articles.
- When you have a specific topic in mind and want to find relevant readings to process and integrate.

## Interactive Workflow (v2)

### Phase 1: Ingestion and Parsing

1.  **Find Unprocessed Readings:** Use `terminal` with `rg` or `find` to list files in `Inputs/Readings/` that do not have a corresponding `Source` note in `Notes/Sources/` or `inbox/`.
2.  **Present Selection:** Present a random sample of 5 unprocessed readings for user selection.
3.  **Parse Local File:** Read the selected `Reading` file and parse it, extracting the following content to be copied verbatim into the new `Source` note:
    -   Bibliographic data (Author, Title, URL).
    -   The `Document Note` block.
    -   The `Summary` block from Readwise.
4.  **Fetch Full Text:** If a URL is present in the bibliographic data, use the `web_extract` tool to fetch the full, clean text from the source. Hold this, along with any user highlights from the `Reading` file, for the synthesis phase. If the fetch fails, fall back to using only the content present in the `Reading` file.

### Phase 2: Synthesis and Vault Reconnaissance

This is the core knowledge-creation step.

1.  **Identify Core Concepts:** Analyze the full text from the URL and any user highlights to identify the central arguments, claims, and concepts.
2.  **Search the Vault:** Use the semantic search tool (`~/bes/vault_indexer/query_vault.py`) to find the top 3-5 most relevant notes in the vault related to these core concepts.
3.  **Generate Synthesis Sections:** Based on the `Reading`'s concepts and the related notes found in the vault, generate three new sections for the `Source` note:
    -   `## Agreement`: Points from the `Reading` that reinforce or support existing `Thoughts` or `Beliefs`.
    -   `## Tension/Challenge`: Points that contradict, challenge, or offer a different perspective on existing notes.
    -   `## Application & Insights`: Actionable ideas or mental models from the `Reading` that could be applied to active `Projects` or general thinking.

### Phase 3: Assembly and Confirmation

1.  **Assemble Note:** Assemble the final `Source` note using the `Utilities/Templates/New Source.md` template.
    -   **Frontmatter:** Populate `id`, `daily_note`, `category`, `reading`, and bibliographic data (`author`, `full_title`, `url`).
    -   **Body:** Copy the `Document Note` (if present) and `Summary` from the `Reading` file.
    -   **Synthesis:** Place the generated `Agreement`, `Tension/Challenge`, and `Application & Insights` sections under a `## My Synthesis` heading.
2.  **Add Quick Thoughts:** If the user provides additional "quick thoughts" during the interactive session, append them under a `### Quick Thoughts` heading.
3.  **Preview:** Present the complete, final Markdown content of the proposed note for user review.
4.  **Create Note and Rename Reading:** Upon user confirmation, write the `Source` note to the `inbox/` directory with the filename `{Original Reading Title}.md`. Then, rename the original `Reading` file to `{Original Reading Title} {YYYY-MM-DD}.md` to mark it as processed.
5.  **Loop:** Offer to process another reading, get a new batch, or exit the workflow.

## Implementation Pitfalls & Lessons Learned

-   **State Management:** The workflow should be stateless. Rely on direct filesystem checks (`rg`, `find`) to identify unprocessed readings rather than maintaining a separate state or database.
-   **Web Scraping Fragility:** Fetching full text from URLs can fail. The workflow must gracefully fall back to using the text available in the local `Reading` file when `web_extract` fails or returns poor quality content.
-   **Subprocess Inception (CRITICAL):** Do **NOT** write a script that calls a subprocess invoking the `hermes-agent` CLI (e.g., `hermes prompt ...`). This anti-pattern pollutes `stdout` and causes catastrophic failures. Handle all reasoning and generation natively in the main conversation context.
