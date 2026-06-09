---
name: obsidian-manage-categories
description: Add or delete entity categories in Justin's Obsidian vault. Covers creating/removing category notes and templates, and keeping vault notes consistent.
platforms: [linux]
---

# Obsidian: Manage Categories

## When to use this skill

**Only when Justin explicitly says to add or delete a category.** Do not infer this from context, do not suggest it proactively, and do not add or delete categories as a side effect of other vault work. These are deliberate, high-impact changes.

---

## Vault paths

- Vault root: `/home/justin.guest/vault`
- Category notes: `<vault>/utilities/categories/<CategoryName>.md`
- Templates: `<vault>/utilities/templates/<TemplateName>.md`

---

## Adding a category

### Step 1 — Create the category note

File: `<vault>/utilities/categories/<CategoryName>.md`

```yaml
---
id: "YYYYMMDDHHmmss"
daily_note: "[[YYYY-MM-DD dddd]]"
---
# <CategoryName>

[Parent category: [[<ParentName>]]]

<Description>
```

Use the current wall-clock time for `id` and `daily_note`. Indicate the hierarchy if there is a parent or subcategories.

### Step 2 — Create the template (if needed)

If the category requires a new specific template, clone the baseline standard note template `new_note.md` in `<vault>/utilities/templates/`:

```bash
cp "/home/justin.guest/vault/utilities/templates/new_note.md" \
   "/home/justin.guest/vault/utilities/templates/new_<categoryname>.md"
```

### Step 3 — Offer a vault scan

After creating both files, ask Justin:

> Want me to scan the vault for notes that might belong in [[<CategoryName>]]?

If yes, surface candidate notes that lack a `category:` field or have a different one and semantically match the new category. Present as candidates — do not modify anything without explicit approval.

---

## Deleting a category

### Step 1 — Remove the category note and template

```bash
rm "/home/justin.guest/vault/utilities/categories/<CategoryName>.md"
rm "/home/justin.guest/vault/utilities/templates/new_<categoryname>.md"
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

- Do NOT use Templater syntax in category notes — resolve timestamps to literal values.
- Template files DO use Templater syntax — copy from an existing template rather than writing from scratch.
- Category note filename is just the category name (e.g., `Resources.md`), no timestamp.
- Do not run git commands on the vault; `bes-vault-sync` auto-commits.
