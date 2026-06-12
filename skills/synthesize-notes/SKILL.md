---
name: synthesize-notes
description: Answers durable research questions by searching the vault, synthesizing findings, and filing the answer as a new note for future reference.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, research, synthesis, query, knowledge]
    related_skills: [obsidian, session_search, obsidian-ingest-log]
---

# synthesize-notes

## Overview

This skill handles interactive, durable research questions about the content of the Obsidian vault. It follows a "Search → Synthesize → File" workflow to create a persistent, atomic note that answers the user's question, ensuring the knowledge is captured and easily retrievable later.

This skill replaces the `integrate-query` workflow from the deprecated `llm-wiki` skill.

## When to Use

This is an interactive-only skill. Use it when Justin asks a question that requires synthesizing information from multiple notes, such as:

-   "What do my notes say about X?"
-   "Compare and contrast X and Y based on my notes."
-   "Synthesize everything I've written about Z."
-   When the same topic comes up for the second time in a session.
-   When Justin explicitly says "file this" or "this is important".

## Durability Threshold

A new synthesis note should be created when the topic meets a certain threshold for importance, typically indicated by:

-   The query involves three or more source notes.
-   It requires a comparison or decision analysis.
-   It connects ideas from different projects or domains.
-   The user gives an explicit instruction to save the answer.

## Workflow

1.  **Search:** Use `session_search` and other tools to find all relevant notes in the vault related to the user's query.
2.  **Synthesize:** Read the content of the source notes and compose a concise, atomic answer to the question. The synthesis should be original and not merely a concatenation of source text.
3.  **File:** Write the synthesis to a new markdown file in the `Inbox/` directory for manual review and filing by Justin. The note should use a standard template.
4.  **Report:** Print the full content of the newly created note directly in the chat for immediate review.
5.  **Log:** Call the `obsidian-ingest-log` skill to append a record of the new synthesis note to the vault's central log.

### Synthesis Note Template

```yaml
---
id: 'YYYYMMDDHHmmss'
daily_note: "[[YYYY-MM-DD Weekday|YYYY-MM-DD Weekday]]"
category: "[[Notes]]"
---

# Title: Synthesis on [Topic]

## Question
> [The user's original question]

## Synthesis
[A concise, synthesized answer, typically 1-3 paragraphs.]

## Sources Consulted
- [[Link to Source Note 1]]
- [[Link to Source Note 2]]
- [[Link to Source Note 3]]
```

## Pitfalls

-   **Overly Broad Synthesis:** Notes should be atomic. Avoid creating large, multi-topic summaries. If a query is very broad, consider breaking it down into smaller, more focused synthesis notes.
-   **Forgetting to Log:** Failing to call `obsidian-ingest-log` at the end of the workflow makes the new note "invisible" to the vault's chronological audit trail.
-   **Not Reporting Back:** Always print the full note in the chat. This confirms the action was taken and allows for immediate feedback.
-   **Using from Cron:** This is an interactive workflow that requires nuance. It should not be run from an automated cron job.