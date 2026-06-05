---
name: obsidian
description: Read, search, create, and edit notes in Justin's Obsidian vault. Covers vault path resolution, filesystem-first conventions, note-creation rules (filenames, frontmatter, Templater), and links to a full Obsidian-Flavored-Markdown reference.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

For Obsidian-Flavored-Markdown syntax details (callouts, embeds, block IDs, dataview queries, math, mermaid, etc.), load `references/obsidian-flavored-markdown.md` from this skill when you need it. Don't load it eagerly — it's a reference, not a rule-set.

For a full structural audit of the vault (folder sizes, category distribution, known issues as of 2026-05-22), see `references/vault-audit-2026-05-22.md`.

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

### Brainstorming and Note-Creation Workflow
When the user is brainstorming or brain-dumping thoughts (e.g., about strategic ideas or planning):
- **Do not jump the gun:** Never rush to write or finalize the note files while the user is still mid-thought. 
- **Let them finish:** Actively listen, capture, and acknowledge their dump, and explicitly wait until they confirm they are completely done brainstorming before generating and writing the final note files.
- **Structure for Product/Concept Notes:** When compiling a conceptual brain dump or new product idea, organize the final note with clear headings:
  - **The Core Idea (Verbatim):** Highlight the user's raw, verbatim product description.
  - **Risk Assessment:** Categorize notes by standard risks (e.g., Value Risk, Usability Risk, Feasibility Risk, Scale/Economic Risk) to make the strategic analysis scannable.
  - **Next Steps:** End with the immediate next action, decision, or design/engineering challenges to address.

#### Pattern: Adding to a Thematic Series of Strategy Notes
When adding a new note to an existing series of conceptual or strategic notes (e.g., K12 Special Ed strategy):
1. **Search and Analyze First:** Use file searches to find the existing notes in the series. Review their naming conventions, structures, and frontmatter styles.
2. **Interlink Bidirectionally:** Make sure the new note references and links back to the earlier notes in the series (e.g., `Building on the critique... (from [[Note A]] and [[Note B]])`).
3. **Preserve Naming & ID Conventions:** Use the same title + timestamp pattern and ID structures as the existing notes in the series to maintain vault consistency.
4. **Synchronize Task Trackers:** Check for any active Todoist tasks referencing the series (e.g., "Discuss strategy with X") and append the new note's link to the task description so the context remains fully unified.

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

Notes are organized by type into specific locations in the vault:
- **Notebook/**: Contains **free-form notes, essays, journals, personal reflections, braindumps**, and **typed notes** (People, Organizations, Meetings). Example files: `Notebook/Sledding with Rosie 20260101153654.md`, `Notebook/Why ship in small batches 20250603173937.md`.
- **Vault Root**: **Project notes** (category `[[Projects]]`) and **current daily notes** live in the vault root by convention (see `manage-projects` skill).
- **Daily Notes/**: **Archived daily notes** are moved here after the day is done.

## Third-party managed folders — do not touch

These folders are managed by external apps with their own schemas. Never add or modify `id`, `daily_note`, or `category` fields in these:

- `Granola/` — meeting summaries and transcripts from the Granola app. Schema: `granola_id`, `title`, `type`, `created`, `updated`, `attendees`, `transcript`/`note`. Only carry `category: "[[Meetings]]"` on summaries (not transcripts); other standard frontmatter (like numeric `id` or `daily_note`) is omitted.
- `Readwise/` — article highlights imported by the Readwise plugin. Schema: `id` (non-standard timestamp format), `daily_note` (plain string, not wikilink). Do not patch these — they get overwritten on the next sync.

## Misplaced daily notes

Daily notes are sometimes accidentally saved to `Notebook/` instead of `Daily Notes/`. Detect them by: filename matches `YYYY-MM-DD Weekday.md` (no extra words after the day name) AND contains `#daily_note` tag. Correct location is `Daily Notes/`.

## Templates

- Templates live at `<vault>/Templates/` (not `Utilities/Templates/` — that's a stale path from the Cursor-era setup).
- Daily Notes use `<vault>/Templates/Daily Note.md` (filename may vary; check the directory).
- Default new notes use `<vault>/Templates/New Note.md` (has a blank `category:` field, which is correct for non-entity notes).

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

## Category field — not required on every note

Only **entity/object notes** need a `category:` field — notes that represent a real-world thing (a person, meeting, project, organization). Free-form notes (essays, journals, braindumps, reference snippets, trip notes) do not need a category and should not be forced into one. Do not flag or "fix" notes that simply lack a `category:` field.

## Tag-to-category conversion

Justin's old habit is to indicate a note's type with an inline tag (e.g. `#meetings`, `#people`, `#project`) instead of a `category:` frontmatter field. When you see this, it should be auto-corrected: set the `category:` frontmatter and remove the tag from the body.

**Rules:**
- Tags that unambiguously identify a type (convert always): `#people`, `#person`, `#organizations`, `#organization`
- Tags that are frequently used loosely (only convert if filename starts with `YYYY-MM-DD`): `#meetings`, `#meeting`, `#projects`, `#project`
- The `#project` tag in particular is often applied to notes about work topics that are NOT GTD project-object notes (e.g. `Dianne AI Workshop` had `#project` but was a workshop pre-work document, not a project). When the filename has no date prefix, leave it alone.
- After conversion, remove the matched tag from the body.

**Canonical tag-to-wikilink mapping:**

| Tag | Category wikilink |
|-----|-------------------|
| `#people`, `#person` | `[[People]]` |
| `#organizations`, `#organization` | `[[Organizations]]` |
| `#meetings`, `#meeting` | `[[Meetings]]` (date-prefix filenames only) |
| `#projects`, `#project` | `[[Projects]]` (date-prefix filenames only) |

## Vault hygiene automation

A hygiene script runs daily at 8am and auto-fixes structural issues. Location: `~/.hermes/scripts/vault_hygiene.py` (or `run_tier1_hygiene.py`). Wrapper (filters to red-level issues only for Telegram delivery): `~/.hermes/scripts/vault_hygiene_cron.py`.

**What it auto-fixes:**
- Misplaced daily notes: `YYYY-MM-DD Weekday.md` in `Notebook/` → moves to `Daily Notes/`
- Tag-to-category conversions (per rules above)

**What it reports (no auto-fix):**
- Typed notes outside `Notebook/` or vault root (wrong-folder)
- ID conflicts (two notes share the same `id`)
- Notes missing an `id` field
- Notes missing a `daily_note` field (as a wikilink)

**Folders the script skips entirely:** `Readwise/`, `Templates/`, `Daily Notes/`, `Categories/`, `.git`, `.trash`, `.cursor`, `.claude`, and any folder named `Granola` (e.g. `Logs/Granola/`) or `Copilot` (e.g. `Logs/Copilot/`) at any level of directory walk.

*Implementation detail:* To prevent descending into ignored subdirectories during a directory traversal, the vault hygiene scripts filter `dirs[:]` in-place inside `os.walk` at any nested level:
```python
dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip]
```

For the full vault structural audit (folder sizes, issue catalogue, what was found and fixed), see `references/vault-audit-2026-05-22.md`. For the hygiene script architecture and design decisions, see `references/vault-hygiene-design.md`.

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

**Note:** As of a May 2026 vault audit, the category notes in `Categories/` have been confirmed to already carry `category: "[[Categories]]"` (e.g. `Categories/Meetings.md` has it). The stale claim that they lacked this field is no longer accurate.

### Templates (from `<vault>/Templates/`)

Entity templates (Meetings, People, Organizations, Projects) share the same frontmatter skeleton:
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

Free-form and brain-dump notes use the standard note template:
- **New Note.md** — `category:` is left blank. Follows the default filename convention: `[Descriptive Title] YYYYMMDDHHmmss.md`. Ideal for essays, strategy brain dumps, journals, and raw conceptual thoughts that do not fit a specific entity category.

When Bes creates any of these notes (bypassing Templater), substitute the Templater expressions with real values and follow the filename/naming conventions precisely.

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

Justin's `bes-vault-sync` watcher auto-commits and pushes the vault to GitHub within seconds of any write. Do not run `git add` / `git commit` / `git push` on the vault from within Bes — it races the watcher and creates noisy commits.

## Git environment variable leakage in hooks and background scripts

When writing hooks (e.g. `pre-turn.sh`) or background sync scripts (like `bes-vault-sync`) that execute Git commands on the user's vault, the script inherits the parent agent's environment variables. If the agent is tracking its own checkpoints, it sets environment variables like `GIT_DIR`, `GIT_WORK_TREE`, and `GIT_INDEX_FILE`. 

These leaked environment variables redirect all Git commands in the hook/script to the agent's internal store, causing command failures such as `Cannot rebase onto multiple branches`.

**Fix:** Always unset Git-specific environment variables at the top of your hooks or background scripts before performing repository operations:
```bash
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_NAMESPACE GIT_ALTERNATE_OBJECT_DIRECTORIES
```
