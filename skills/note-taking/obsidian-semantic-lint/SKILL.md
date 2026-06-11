---
name: obsidian-semantic-lint
description: Performs high-level semantic health checks on the vault, identifying potential contradictions, stale summaries, and structural anomalies in the knowledge graph.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags: [obsidian, lint, hygiene, knowledge-graph, semantics]
    related_skills: [obsidian, obsidian-hygiene]
---

# obsidian-semantic-lint

## Overview

This skill is responsible for running Tier-3 (semantic) health checks on the Obsidian vault. Unlike `obsidian-hygiene`, which focuses on structural issues like broken links and file locations, this skill analyzes the *content* of the notes to find potential issues in the knowledge graph.

This skill absorbs the `Semantic Lint` workflow from the deprecated `llm-wiki` skill.

## When to Use

-   **On-demand:** When Justin asks to "run a wiki lint" or "check for contradictions". It should always be run *after* `obsidian-hygiene` to ensure a clean structural baseline.
-   **Via Cron:** A monthly cron job runs this skill to generate a report of potential issues for review.

## Checks Performed

This skill runs the `wiki_semantic_lint.py` script, which checks for several classes of semantic problems:

1.  **Deterministic Orphans:** Notes with no inbound links from other conceptual notes (excluding indexes, logs, and daily notes). These are potential knowledge silos.
2.  **Stale Summaries:** `Source` notes whose underlying `Reading` notes have been updated more recently than the `Source` summary itself.
3.  **Promotion Gaps:** High-level `Beliefs` that are not supported by a chain of `Thoughts` or `Concepts`, indicating a potential leap in logic.
4.  **Circular Reasoning:** Identifies link chains that form a closed loop (e.g., A → B → C → A), which can be a sign of a tautological argument.
5.  **Contradiction Candidates:** Flags pairs of notes (especially `Beliefs` and `Thoughts`) that make opposing claims. This is a heuristic and requires human review.

## Workflow

1.  **Baseline with Structural Lint:** When run on-demand, first ensure `obsidian-hygiene` has been run to fix any structural problems.
2.  **Execute Script:** Run the `wiki_semantic_lint.py` script.
3.  **Generate Report:** The script outputs a report in markdown format to `Utilities/reports/semantic-lint-YYYY-MM-DD.md`.
4.  **State Management:** The script also updates a state file at `~/.hermes/state/semantic_lint_last.json` to track findings between runs.
5.  **Review (Agent/User):** The agent should review the "Contradiction Candidates" section of the report. It should *never* auto-edit notes based on these findings, especially not `Beliefs`. The findings should be presented to Justin for review.

## Pitfalls

-   **Auto-Editing:** Never automatically change the content of a note based on a semantic lint report. These are candidates for review, not definitive errors.
-   **Running Before Hygiene:** Running semantic checks on a structurally unsound vault can lead to confusing or inaccurate results. Fix the simple problems first.
-   **Confusing with Structural Lint:** Remember the division of labor: `obsidian-hygiene` is for structure (files, links, IDs), `obsidian-semantic-lint` is for content and meaning.