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
- Category notes: `<vault>/Utilities/Categories/<CategoryName>.md`
- Templates: `<vault>/Utilities/Templates/`

---

## Adding a category

### Step 1 — Create the category note

File: `<vault>/Utilities/Categories/<CategoryName>.md`

```yaml
---
id: "YYYYMMDDHHmmss"
daily_note: "[[YYYY-MM-DD dddd]]"
---
# <CategoryName>
Type: <Folder>

<Description>
```

Use the current wall-clock time for `id` and `daily_note`. The body must contain the H1 title of the category, followed by `Type: <Folder>` (where `<Folder>` is Contacts, Notes, Logs, or Utilities), and the category description.
<Description>
```

Use the current wall-clock time for `id` and `daily_note`. Indicate the hierarchy if there is a parent or subcategories.

### Step 2 — Create the template (if applicable)

If a specialized template is needed for notes in this category, copy the closest baseline template in `Utilities/Templates/` (such as `new_note.md` or `daily_note.md`) using programmatic file-copying tools rather than shell redirection to avoid Templater syntax escaping issues:

```bash
rm "/home/justin.guest/vault/Utilities/Categories/<CategoryName>.md"
rm "/home/justin.guest/vault/Utilities/Templates/new_<category_name>.md"
```

> Want me to scan the vault for notes that might belong in [[<CategoryName>]]?

If yes, surface candidate notes that lack a `category:` field or have a different one and semantically match the new category. Present as candidates — do not modify anything without explicit approval.

---

### Step 2 — Create the template (if applicable)

If a specialized template is needed for notes in this category, copy the closest baseline template in `Utilities/Templates/` (such as `new_note.md` or `daily_note.md`) using programmatic file-copying tools rather than shell redirection to avoid Templater syntax escaping issues:

```bash
rm "/home/justin.guest/vault/Utilities/Categories/<CategoryName>.md"
rm "/home/justin.guest/vault/Utilities/Templates/new_<category_name>.md"
```

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
