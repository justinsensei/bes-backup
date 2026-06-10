# Semantic Lint (on-demand)

Structural checks belong to `obsidian-hygiene` / `vault_hygiene.py`. This reference covers semantic health.

## Trigger phrases

- "run wiki lint"
- "check for contradictions"
- "are my Sources stale?"

## Checks

### Stale compiled summaries

Source note `## Summary` last updated before its linked Reading was modified → flag for integrate-full refresh.

### Contradictions

- Source A vs Source B on same topic with incompatible claims
- Concept links to Source but body contradicts Source summary
- Belief conflicts with linked Concept (surface for Justin — never auto-edit Beliefs)

### Orphan compile opportunities

Readings with substantial highlights but no linked Source note → suggest integrate-full promotion.

### Missing link chain

Concept links directly to Reading when Source note exists → suggest relink through Source.

## Output format

```markdown
## Wiki semantic lint — YYYY-MM-DD

### Stale summaries
- [[Source Title]]: Reading updated <date>, summary not refreshed

### Contradictions
- [[Concept X]] vs [[Source Y]]: <one-line conflict>

### Promotion opportunities
- [[Reading Title]]: no compiled Source yet
```

## Delegation

Run `python3 ~/.hermes/scripts/vault_hygiene.py` first for structural baseline. Semantic lint builds on that report.
