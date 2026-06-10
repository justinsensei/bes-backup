# integrate-query

Interactive Q&A with durable synthesis — file answers back to the vault.

## When to use

Justin asks a research/knowledge question where the answer should persist:
- "What do my notes say about X?"
- "Synthesize everything on Y"
- "Compare these two Sources"

## Workflow

1. **Search** — `semantic_pointer.py search` + vault grep for relevant Inputs/Sources/Concepts
2. **Synthesize** — compose answer citing upstream links (Concept→Source→Reading)
3. **File** — write durable note to appropriate maturity category:

| Answer type | Category | Folder |
|-------------|----------|--------|
| Fleeting answer / working notes | `[[Notes]]` | `Notes/` |
| Personal take | `[[Thoughts]]` | `Notes/` |
| Others' model extracted | `[[Concepts]]` | `Notes/` |
| Trusted principle | `[[Beliefs]]` | `Notes/` |
| Decision record | `[[Decisions]]` | `Notes/` |

4. **integrate-light** — log + index + daily notepad bullet

## Link rules

- Link to Sources when they exist; never skip Source to link Reading directly from Concepts
- Use shortest-path wikilinks per obsidian skill

## Frontmatter

Standard obsidian schema with `id`, `daily_note`, `category`. Timestamp-prefixed filename for Notes/Thoughts/Concepts; title-only for Beliefs/References-style if canonical.
