---
name: extract-concepts
description: |
  Extracts concepts from source notes, proposing links, revisions, or new concept notes.
tags:
  - obsidian
  - knowledge-management
  - synthesis
---

# Extract Concepts

This skill facilitates the creation of new knowledge by synthesizing information from `Source` notes into `Concept` notes. It takes a "seed" (either a direct path to a `Source` note or a topic query) and proposes three types of actions for user review:

1.  **Simple links:** Connecting `Source` notes to existing, relevant `Concept` notes.
2.  **Revisions:** Updating existing `Concept` notes with new information from `Source`s.
3.  **New Concepts:** Creating new `Concept` notes based on ideas found in the `Source`s.

This is an interactive, human-in-the-loop workflow. All proposals require user approval before execution.

## Workflow

### 1. Seed Interpretation

The skill begins by interpreting the user-provided seed.

1.  **Receive Seed:** The user provides either a path to a specific `Source` note or a general topic/query.
2.  **Identify Target Sources:**
    *   If the seed is a path, that file is the single target `Source`.
    *   If the seed is a query, use the `obsidian-semantic-pointer` tool to search for relevant notes within the `~/vault/Notes/Sources/` and `~/vault/Inbox/` directory. The top 3-5 results become the target `Source` notes.

    ```bash
    # Example for a query seed
    python3 ~/bes/vault_indexer/query_vault.py "your query here"
    ```

### 2. Content Aggregation & Discovery

Once the target `Source` notes are identified, the skill gathers the necessary context.

1.  **Read Sources:** Read the full content of all target `Source` notes.
2.  **Create Corpus:** Combine the content into a single text corpus.
3.  **Discover Related Concepts:** Use the `obsidian-semantic-pointer` tool again, this time searching the `~/vault/Notes/Concepts/` directory with the `Source` corpus as the query.
4.  **Read Concepts:** Read the full content of the top 3-5 related `Concept` notes found.

### 3. Planning and Iteration

This phase focuses on creating a high-level plan for knowledge integration, which is then refined with the user.

1.  **Propose Plan:** After analyzing the source(s) and related concepts, propose a plan with three sections:
    *   **Link to Existing Concepts:** List existing `Concept` notes that should be linked from the source(s). Provide a brief rationale for each link.
    *   **Revise Existing Concepts:** List existing `Concept` notes that should be updated. Provide a brief rationale explaining what new information the source(s) contribute.
    *   **Create New Concepts:** List new `Concept` notes that should be created. Provide a brief rationale and a suggested title for each.
2.  **Iterate with User:** The user reviews the plan and provides feedback. The plan is updated based on this feedback until the user gives explicit approval to proceed with execution.

### 4. Step-by-Step Execution

Once the plan is approved, the skill executes it in a granular, one-by-one interactive process.

1.  **Add Links:**
    *   All approved links are added to the relevant `Source` notes using the `patch` tool. This step is done in a single batch and does not require further approval.
2.  **Revise Concepts (One by One):**
    *   For the first concept marked for revision, generate and display a diff of the proposed changes.
    *   The user can approve the changes or request modifications.
    *   Upon approval, the `patch` tool applies the changes to the original note.
    *   The updated note is then moved to `~/vault/Inbox/` using `mv`.
    *   This process repeats for each concept on the revision list.
3. **Create New Concepts (One by One):**
    *   For the first new concept, generate and display the full draft of the note content.
    *   The user can approve the draft or request modifications.
    *   Upon approval, the `write_file` tool creates the new note directly in `~/vault/Inbox/` under the filename `{Concept Name} {ID}.md` (where `{ID}` is the same unique ID string `YYYYMMDDHHmmss` used in the frontmatter, and `{Concept Name}` is the concept's title). It must use the following template:

        ```markdown
        ---
        id: 'YYYYMMDDHHmmss'
        daily_note: "[[YYYY-MM-DD Weekday]]"
        category: "[[Concepts]]"
        ---

        > A brief, one-sentence summary of the core concept.

        A more detailed explanation of the concept, including its key principles and implications.

        Sources: [[Source Note 1]], [[Source Note 2]]
        ```

    *   This process repeats for each concept on the creation list until the workflow is complete.


## Pitfalls

-   **Semantic Drift:** Semantic search is powerful but not perfect. The skill must be prepared for tangentially related or irrelevant results and avoid forcing connections where none exist.
-   **Over-creation:** The default should be to integrate with existing knowledge (linking and revising) before creating something new. Avoid proposing a new `Concept` for every minor detail.
-   **User Context:** The skill operates without the user's full mental model. Its proposals are best-effort suggestions and rely on the user for final validation and contextual fitness.
