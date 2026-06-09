---
name: obsidian-manage-categories
description: Add or delete entity categories in Justin's Obsidian vault under the June 2026 taxonomy. Covers creating/removing category notes, folder-routing Type properties, and keeping vault notes consistent.
platforms: [linux]
metadata:
  hermes:
    related_skills: [obsidian]
---

# Obsidian: Manage Categories

## When to use this skill

**Only when Justin explicitly says to add or delete a category.** Do not infer this from context, do not suggest it proactively, and do not add or delete categories as a side effect of other vault work. These are deliberate, high-impact changes.

---

## Vault paths

- Vault root: `/home/justin.guest/vault`
- Category notes: `<vault>/Utilities/Categories/<CategoryName>.md`

---

## Adding a category

### Step 1 — Create the category note

File: `<vault>/Utilities/Categories/<CategoryName>.md`

Format:
```markdown
---
id: "YYYYMMDDHHmmss"
daily_note: "[[YYYY-MM-DD dddd]]"
category: "[[Categories]]"
---
# <CategoryName>
Type: <Folder>

<Brief description of what goes in this category>
```

- Use the current wall-clock time for `id` and `daily_note`.
- Always set the `Type: <Folder>` property on line 6 (e.g. `Type: Contacts`, `Type: Notes`, or `Type: Logs`), where `<Folder>` is the capitalized root-level folder where notes of this category belong.
- No other body content unless Justin provides some.

### Step 2 — Offer a vault scan

After creating the category file, ask Justin:

> Want me to scan the vault for notes that might belong in [[<CategoryName>]]?

If yes, search for candidate notes that lack a `category:` field or have a different one and semantically match the new category. Present as candidates — do not modify anything without explicit approval.

---

## Deleting a category

### Step 1 — Remove the category note

```bash
rm "/home/justin.guest/vault/Utilities/Categories/<CategoryName>.md"
```

### Step 2 — Strip the category value from vault notes

Search for all notes that reference the deleted category:

```bash
grep -rl 'category:.*\[\[<CategoryName>\]\]' /home/justin.guest/vault --include="*.md"
```

For each match, remove **only** the deleted category from the `category:` field. Rules:

- If `category:` is a single value (`category: "[[<CategoryName>]]"`), remove the entire `category:` line.
- If `category:` holds multiple values (list or comma-separated), remove only the deleted category entry. Leave the rest untouched.
- Do not touch any other frontmatter fields or body content.

Use `patch` for targeted edits. Review the full list of affected notes before making changes — present them to Justin first if the count is large or surprising.

---

## Pitfalls

- Do NOT use Templater syntax in category notes — resolve timestamps and dates to literal values.
- Do NOT create category-specific templates anymore. Justin has consolidated and simplified templates to: `daily_note.md`, `new_note.md`, and `new_meeting.md` in `Utilities/Templates/`. New manual notes utilize the generic `new_note.md` template.
- Category notes always belong to the `[[Categories]]` category (with `Type: Utilities`), which makes the `Categories.md` note itself self-referential.
- Category note filename is just the category name (e.g. `People.md`, `Daily Notes.md`), spaced-capitalized and matching the category wikilink.
- Do not run git commands on the vault; `bes-vault-sync` auto-commits.
