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

1.  **Find Unprocessed Readings:** Use `terminal` with `rg` or `find` to list files in `Inputs/Readings/` or custom raw research dumps in the `Inbox/` (e.g., named with an ID or having `category: "[[Readings]]"`) that do not have a corresponding `Source` note in `Notes/Sources/` or `Inbox/`.
2.  **Present Selection:** Present a random sample of 5 unprocessed readings for user selection.
3.  **Parse Local File:** Read the selected `Reading` file and parse it. Extract bibliographic data (Author, Title, URL). For AI-generated research logs or dialogues (e.g., from Dia or Claude) that lack formal bibliographic fields, infer the author (e.g., "Dia" or "Claude"), title, and query context to use as the `Document Note` or `Summary` base.
4.  **Fetch Full Text:** If a URL is present in the bibliographic data, use the browser tools (`browser_navigate`, then `browser_console` with `document.body.innerText`) to fetch the full, clean text from the source. This is more reliable than older tools like `web_extract`. Hold this, along with any user highlights from the `Reading` file, for the synthesis phase. If no URL is present (e.g. self-generated or AI research logs), fall back to using the text already in the `Reading` file.

### Phase 2: Synthesis and Vault Reconnaissance

This is the core knowledge-creation step.

1.  **Identify Core Concepts:** Analyze the full text from the URL and any user highlights to identify the central arguments, claims, and concepts.
2.  **Search the Vault:** Use the semantic search tool (`~/bes/vault_indexer/query_vault.py`) to find the top 3-5 most relevant notes in the vault related to these core concepts. The correct invocation is `python ~/bes/vault_indexer/query_vault.py "your query string"`. Do not use `--query` or other flags.
3.  **Generate Synthesis Sections:** Based on the `Reading`'s concepts and the related notes found in the vault, generate three new sections for the `Source` note:
    -   `## Agreement`: Points from the `Reading` that reinforce or support existing `Thoughts` or `Beliefs`.
    -   `## Tension/Challenge`: Points that contradict, challenge, or offer a different perspective on existing notes.
    -   `## Application & Insights`: Actionable ideas or mental models from the `Reading` that could be applied to active `Projects` or general thinking.

### Phase 3: Assembly and Finalization

This phase compiles the finalized notes directly into the vault. No confirmation loop is needed; the note is created immediately, and the user can revise or edit it directly in Obsidian.

1.  **Assemble Note:** Assemble the final `Source` note content using the `Utilities/Templates/New Source.md` template.
    -   **Frontmatter:** Populate `id`, `daily_note`, `category`, `reading`, and bibliographic data (`author`, `full_title`, `url`).
    -   **Body:** Copy the `Document Note` (if present) and `Summary` from the `Reading` file.
    -   **Synthesis:** Place the generated `Agreement`, `Tension/Challenge`, and `Application & Insights` sections under a `## My Synthesis` heading.
    -   **No Raw Inputs:** Do not append raw highlights, original text, or raw inputs to the end of the note. Keep the final Source note focused solely on metadata, summaries, and synthesis.
2.  **Write Final Source Note directly to Obsidian Inbox:** Write the fully assembled note directly to the Obsidian `Inbox/` directory with the filename `{Original Reading Title} {YYYY-MM-DD}.md` (aligning with the naming rule for new Source notes).
3.  **Mark Original Reading as Processed:** Rename the original `Reading` file to `{Original Reading Title} {YYYY-MM-DD}.md` and move it to `Inputs/Readings/` to mark it as processed.
4.  **Notify User:** Deliver a message containing a concise summary of the synthesis and a notice that the Source note has been successfully written and the Reading file has been archived.
5.  **Loop:** Offer to process another reading, get a new batch, or exit the workflow.

## Implementation Pitfalls & Lessons Learned

-   **File Paths with Spaces:** When using `terminal` commands like `mv` or `ls` on files with spaces in their names, tilde (`~`) expansion can be unreliable. Prefer using the full absolute path (e.g., `/home/justin.guest/vault/...`) to avoid "No such file or directory" errors.
-   **State Management:** The workflow should be stateless. Rely on direct filesystem checks (`rg`, `find`) to identify unprocessed readings rather than maintaining a separate state or database.
-   **Semantic Search Failure Fallback:** If the local semantic search script (`~/bes/vault_indexer/query_vault.py`) fails (e.g., if the `obsidian_vault` collection is missing or unbuilt), fall back to manual keyword searches across the vault using `search_files` to find relevant notes for synthesis.
-   **Web Scraping Fragility:** Fetching full text from URLs can fail. The workflow must gracefully fall back to using the text available in the local `Reading` file when browser tools fail or return poor quality content.
-   **`web_extract` Deprecation:** The `web_extract` tool may not be available. Prefer using the `browser` toolset for fetching web content.
-   **Subprocess Inception (CRITICAL):** Do **NOT** write a script that calls a subprocess invoking the `hermes-agent` CLI (e.g., `hermes prompt ...`). This anti-pattern pollutes `stdout` and causes catastrophic failures. Handle all reasoning and generation natively in the main conversation context.
-   **Response Truncation:** The final presentation of the synthesized note can be prone to truncation or corruption. Ensure the entire note is delivered in a single, clean markdown block and that no other context (like the raw highlights) leaks into the user-facing message. Double-check the final output before sending.
-   **Inbox-origin Naming Conflicts:** When the raw Reading file starts in `Inbox/` (instead of `Inputs/Readings/`), rename and move the raw file to `Inputs/Readings/` *before* or *simultaneously with* writing the new Source note back to `Inbox/` to prevent overwriting or name conflicts in the same folder.
-   **Preserving Original Metadata:** If the raw reading file contains custom frontmatter (e.g., an explicit custom `id` or `daily_note` links), preserve those original fields in the newly compiled `Source` note rather than generating fresh timestamps.
