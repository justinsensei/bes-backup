---
name: obsidian-notes
description: Use when managing the Notes/ directory, conceptual mapping, and coordinating
  Thoughts, Beliefs, Decisions, Projects, References, and Concepts categories.
version: 1.0.0
author: Bes
license: MIT
metadata:
  hermes:
    tags:
    - obsidian
    - notes
    - folder-conventions
    related_skills:
    - obsidian
    - obsidian-thoughts-beliefs
    - obsidian-decisions
    - obsidian-projects
    - obsidian-references-sources
    - obsidian-graph-enrichment
platforms:
- linux
---

# Obsidian Type: Notes Directory Conventions

## Overview
This skill governs the physical structure and coordinate mapping of the `/Notes/` top-level directory in Justin's vault.

---

## Directory & Sub-skills
- **Directory:** `${OBSIDIAN_VAULT_PATH:-/home/justin.guest/vault}/Notes/`
- **Sub-skills (Categories):**
  - **`obsidian-thoughts-beliefs`**: For raw reflections or core principles (`category: "[[Thoughts]]"` or `category: "[[Beliefs]]"`).
  - **`obsidian-decisions`**: For trade-offs, architecture decisions, and reasoning logs (`category: "[[Decisions]]"`).
  - **`Memories`**: For journal-like personal notes, conversations, and good days (`category: "[[Memories]]"`).
  - **`obsidian-projects`**: For ongoing project hubs, travel, or milestones (`category: "[[Projects]]"`).
  - **`obsidian-references-sources`**: For factsheets or conceptual summaries (`category: "[[References]]"` or `category: "[[Concepts]]"`).
  - **`obsidian-graph-enrichment`**: Rules and link hierarchy conventions for maintaining a clean note graph.
  - **`obsidian-suggest-links`**: Proactively find surprising linkages among Thoughts and Beliefs.
  - **`obsidian-suggest-new-notes`**: Proactively discover and initialize new notes from log files.
  - **`obsidian-suggest-promotions`**: Proactively promote notes up the hierarchical tiers.

---

## Folder-Level Rules

### Naming Conventions
- All files under `/Notes/` must use Spaced, Capitalized names, adhering to category-specific prefixing rules.
- **Notes, Decisions, Thoughts, Memories, Concepts:** Must be named `ID Title.md` (where ID is the creation timestamp, e.g. `20260609120000 Spaced Title.md`).
- **References, Beliefs, Projects:** Must be named `Title.md` (no timestamp prefix, e.g. `Spaced Title.md`).

### Rationale for Naming
As notes become less ephemeral and more authoritative, we de-emphasize the date and/or the ID in the filename:
1. **Temporality:** More ephemeral, lower-tier notes are more "temporal"—their sequence and place in time matter more.
2. **At-a-Glance Context:** This distinction makes it easy to tell immediately from the note's title whether you are looking at a canonical/authoritative document (project, person, belief, reference) or an ephemeral/temporal one.

### Aliases
- Ensure complex, conceptual, or heavily-referenced notes define clean `aliases:` lists in their YAML frontmatter. This allows effortless wikilinking without typing the full exact title every time.
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
