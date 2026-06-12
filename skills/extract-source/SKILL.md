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

The process is designed to be interactive. It finds unprocessed readings, allows for selection, ingests the full text from the source URL, generates a synthesis by comparing the reading's concepts against the existing vault, and upon confirmation, creates a new, properly formatted `Source` note in the `Inbox/` for final triage.

## When to Use

- When you want to work through your backlog of readings and create synthesized notes that connect to your existing knowledge base.
- As part of a routine like `wind-down` to process one or two articles.
- When you have a specific topic in mind and want to find relevant readings to process and integrate.

## Interactive Workflow (v2)

### Phase 1: Ingestion and Parsing

1.  **Find Unprocessed Readings:** Use `terminal` with `rg` or `find` to list files in `Inputs/Readings/` that do not have a corresponding `Source` note in `Notes/Sources/` or `Inbox/`.
2.  **Present Selection:** Present a random sample of 5 unprocessed readings for user selection.
3.  **Parse Local File:** Read the selected `Reading` file and parse it, extracting the following content to be copied verbatim into the new `Source` note:
    -   Bibliographic data (Author, Title, URL).
    -   The `Document Note` block.
    -   The `Summary` block from Readwise.
4.  **Fetch Full Text:** If a URL is present in the bibliographic data, use the browser tools (`browser_navigate`, then `browser_console` with `document.body.innerText`) to fetch the full, clean text from the source. This is more reliable than older tools like `web_extract`. Hold this, along with any user highlights from the `Reading` file, for the synthesis phase. If the fetch fails, fall back to using only the content present in the `Reading` file.

### Phase 2: Synthesis and Vault Reconnaissance

This is the core knowledge-creation step.

1.  **Identify Core Concepts:** Analyze the full text from the URL and any user highlights to identify the central arguments, claims, and concepts.
2.  **Search the Vault:** Use the semantic search tool (`~/bes/vault_indexer/query_vault.py`) to find the top 3-5 most relevant notes in the vault related to these core concepts. The correct invocation is `python ~/bes/vault_indexer/query_vault.py "your query string"`. Do not use `--query` or other flags.
3.  **Generate Synthesis Sections:** Based on the `Reading`'s concepts and the related notes found in the vault, generate three new sections for the `Source` note:
    -   `## Agreement`: Points from the `Reading` that reinforce or support existing `Thoughts` or `Beliefs`.
    -   `## Tension/Challenge`: Points that contradict, challenge, or offer a different perspective on existing notes.
    -   `## Application & Insights`: Actionable ideas or mental models from the `Reading` that could be applied to active `Projects` or general thinking.

### Phase 3: Assembly, Preview, and Confirmation

This phase is a strict, interactive sequence. Do not proceed to the next step until the user has explicitly approved the current one.

1.  **Assemble Note:** Assemble the final `Source` note content using the `Utilities/Templates/New Source.md` template.
    -   **Frontmatter:** Populate `id`, `daily_note`, `category`, `reading`, and bibliographic data (`author`, `full_title`, `url`).
    -   **Body:** Copy the `Document Note` (if present) and `Summary` from the `Reading` file.
    -   **Synthesis:** Place the generated `Agreement`, `Tension/Challenge`, and `Application & Insights` sections under a `## My Synthesis` heading.
2.  **Write to Temporary File & Preview:** Write the fully assembled note to a temporary file (e.g., `/tmp/{Original Reading Title}.md`).
3.  **Deliver for Review:** Send a message to the user containing:
    -   A brief summary of the synthesis.
    -   The `MEDIA:` tag pointing to the absolute path of the temporary file.
    -   A direct question asking for approval to proceed (e.g., "Shall I create this note in your `Inbox/`?").
    -   **CRITICAL:** Stop and wait for the user's response. Do not perform any file operations on the vault until confirmation is received.
4.  **Finalize on Confirmation:** Once the user explicitly approves:
    -   Write the content from the temporary file to its final destination in the `Inbox/` directory with the filename `{Original Reading Title}.md`.
    -   Rename the original `Reading` file to `{Original Reading Title} {YYYY-MM-DD}.md` to mark it as processed.
    -   Clean up the temporary file.
5.  **Loop:** Offer to process another reading, get a new batch, or exit the workflow.

## Implementation Pitfalls & Lessons Learned

-   **File Paths with Spaces:** When using `terminal` commands like `mv` or `ls` on files with spaces in their names, tilde (`~`) expansion can be unreliable. Prefer using the full absolute path (e.g., `/home/justin.guest/vault/...`) to avoid "No such file or directory" errors.
-   **State Management:** The workflow should be stateless. Rely on direct filesystem checks (`rg`, `find`) to identify unprocessed readings rather than maintaining a separate state or database.
Web Scraping Fragility: Fetching full text from URLs can fail. The workflow must gracefully fall back to using the text available in the local `Reading` file when browser tools fail or return poor quality content.
-   **`web_extract` Deprecation:** The `web_extract` tool may not be available. Prefer using the `browser` toolset for fetching web content.
-   **Subprocess Inception (CRITICAL):** Do **NOT** write a script that calls a subprocess invoking the `hermes-agent` CLI (e.g., `hermes prompt ...`). This anti-pattern pollutes `stdout` and causes catastrophic failures. Handle all reasoning and generation natively in the main conversation context.
-   **Response Truncation:** The final presentation of the synthesized note can be prone to truncation or corruption. Ensure the entire note is delivered in a single, clean markdown block and that no other context (like the raw highlights) leaks into the user-facing message. Double-check the final output before sending.
