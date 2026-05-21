---
name: obsidian
description: Read, search, create, and edit notes in Justin's Obsidian vault. Covers vault path resolution, filesystem-first conventions, note-creation rules (filenames, frontmatter, Templater), and links to a full Obsidian-Flavored-Markdown reference.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

For Obsidian-Flavored-Markdown syntax details (callouts, embeds, block IDs, dataview queries, math, mermaid, etc.), load `references/obsidian-flavored-markdown.md` from this skill when you need it. Don't load it eagerly — it's a reference, not a rule-set.

## Vault path

Use a known or resolved vault path before calling file tools.

The vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, set in `~/.hermes/.env`. Inside `bes-vm` it is `/home/justin.guest/vault`. If unset, fall back to `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content. For wikilink edge cases (block refs, embeds, link-to-heading, display text, search links), see `references/obsidian-flavored-markdown.md`.

---

# Justin's vault conventions

These rules govern how Justin organizes *his* vault. Follow them when creating or modifying notes.

## Typed notes (People, Organizations)

For creating People or Organization notes, load `obsidian-people-notes`. It covers: `Notebook/` destination, name-based filenames, category frontmatter, aliases, family wikilinks, and real vault examples.

## Where to put new notes

- Create new notes in the **vault root** unless explicitly told otherwise.
- The vault has a flat-ish structure with category folders (`Attachments/`, `Daily Notes/`, `Notebook/`, `References/`, `Templates/`) but new notes default to root.

## Templates

- Templates live at `<vault>/Templates/` (not `Utilities/Templates/` — that's a stale path from the Cursor-era setup).
- Daily Notes use `<vault>/Templates/Daily Note.md` (filename may vary; check the directory).

## Templater syntax — DO NOT MODIFY

Template files use the **Templater plugin**, NOT core Obsidian templates. Templater syntax MUST be preserved exactly when editing template files.

### Syntax types

| Syntax | Purpose |
|--------|---------|
| `<% expression %>` | Output tag — prints the result inline |
| `<%* code %>` | Execution tag — runs JavaScript without output |
| `<% tp.file.cursor() %>` | Sets cursor position after template insertion |

### Common commands in this vault

| Syntax | Purpose |
|--------|---------|
| `<% tp.date.now("YYYYMMDDHHmmss") %>` | Generate timestamp ID |
| `<% tp.date.now("[[YYYY-MM-DD dddd]]") %>` | Generate daily note link |
| `<%* title = tp.date.now("..."); await tp.file.rename(title); %>` | Rename file programmatically |

### Rules for editing templates

1. **NEVER remove or modify `<% ... %>` or `<%* ... %>` tags** unless explicitly asked.
2. **Treat Templater syntax as executable code**, not placeholder text.
3. When simplifying templates, preserve ALL Templater tags exactly as-is.
4. Always review the full diff before committing template changes.

### Creating new templates via copy

**Do NOT use `write_file` to create a new template based on an existing one.** `write_file` will corrupt nested quotes inside Templater expressions (e.g. `[[[]YYYY-MM-DD dddd[]]]\")` gains a stray backslash). 

Instead, use `cp` + `sed` to clone and modify:

```bash
cp "<vault>/Templates/New Organization.md" "<vault>/Templates/New Category.md"
sed -i 's/Organizations/Categories/' "<vault>/Templates/New Category.md"
```

Always `diff` the result against the source template afterward to confirm only the intended lines differ.

## Entities and category notes

An **entity** is any note with a `category:` frontmatter field. The canonical list of entity types lives in `<vault>/Categories/`. Each category note is itself an entity (`category: "[[Categories]]"`), including `Categories/Categories.md` which is self-referential.

Current entity types (each has a file in `Categories/` and a template in `Templates/`):

| Entity type | Category note | Template |
|---|---|---|
| Meetings | `Categories/Meetings.md` | `Templates/New Meeting.md` |
| Organizations | `Categories/Organizations.md` | `Templates/New Organization.md` |
| People | `Categories/People.md` | `Templates/New Person.md` |
| Projects | `Categories/Projects.md` | `Templates/New Project.md` |
| Categories | `Categories/Categories.md` | `Templates/New Category.md` |

When creating a note of a given type, follow that type's template. When searching for notes by category, filter by `category: "[[CategoryName]]"`.

**Note:** The existing four category notes (Meetings, Organizations, People, Projects) were created before the entity model and currently lack a `category:` field. They should eventually get `category: "[[Categories]]"` added.

### Templates (from `<vault>/Templates/`)

All four share the same frontmatter skeleton:
```yaml
---
id: "<% tp.date.now("YYYYMMDDHHmmss") %>"
daily_note: "<% tp.date.now("[[YYYY-MM-DD dddd]]") %>"
category: "[[<CategoryName>]]"
---
```

Differences by type:
- **New Meeting.md** — `category: "[[Meetings]]"`. Adds `#meeting` tag inline. Renames file to `YYYY-MM-DD` (date only, no title — title added manually after creation).
- **New Person.md** — `category: "[[People]]"`. Renames file to timestamp.
- **New Organization.md** — `category: "[[Organizations]]"`. Renames file to timestamp.
- **New Project.md** — `category: "[[Projects]]"`. Renames file to timestamp.

When Bes creates these notes (bypassing Templater), substitute the Templater expressions with real values and follow the rename convention for the filename.

## Filename conventions

Different note types follow different filename rules, defined by the template for that type:

- **Default** (most notes): `[Descriptive title] YYYYMMDDHHmmss` — descriptive title followed by file-created timestamp.
- **Daily Notes**: `YYYY-MM-DD dddd` (e.g. `2026-05-20 Wednesday`). **Current** daily notes live in the vault root; **archived** ones get moved to `Daily Notes/` after the day is done.
- **Weekly Reviews**: `YYYY-MM-DD Weekly Review` (using the Friday date).
- **Meeting notes**: `YYYY-MM-DD [Descriptive title]` — date prefix, then a short descriptive title.
- **People / Organizations / Projects**: simple descriptive title, no timestamp (Templater renames to timestamp, but Bes should use a meaningful name instead). Example: `Bes Setup.md`, not `20260521094904.md`.

## YAML frontmatter

Every note in this vault should have these fields:

- **`id`** — numerical string based on the file-created timestamp (`YYYYMMDDHHmmss`).
- **`daily_note`** — wikilink to the daily note for when the file was created, in the format `[[YYYY-MM-DD dddd]]`.
- **`project`** *(optional)* — quoted wikilink to the project this note belongs to, in the format `"[[Project Name]]"`. This field should appear **last** in the frontmatter. Use this to mark the note as a *child* of the project (as opposed to merely mentioning the project in passing).
- **`aliases`** *(optional)* — alternate names that make the note easier to find and link to. Use a YAML list:
  ```yaml
  aliases:
    - Short Name
    - Abbreviation
  ```
  Common for organization notes (e.g. Winchester-Thurston School → Winchester-Thurston, Winchester, WT).

## Structuring new notes

- Always set `id` and `daily_note` correctly in the frontmatter.
- If a note type is specified (daily, weekly, meeting, project), follow that type's filename + template convention.
- If no type is specified, follow the default convention (descriptive title + timestamp) and use the New Note template if one exists.

## Don't manually commit

Justin's `bes-vault-sync` watcher auto-commits and pushes the vault to GitHub within seconds of any write. Do **not** run `git add` / `git commit` / `git push` on the vault from within Bes — it races the watcher and creates noisy commits.
