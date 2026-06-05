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

Notes are organized into specific lowercase directories in the vault, which align with gbrain-personal's page-type definitions:
- **meetings/**: Contains manual/curated meeting summaries. (Raw transcripts live under `sources/meetings/transcripts/`; raw auto-summaries live under `sources/meetings/meeting_notes/`).
- **people/**: Contains People notes.
- **daily/**: Contains both current and archived daily notes.

### Core Policy on Raw Streams
- **No Auto-Notes from Raw Streams:** Do not automatically create or add notes to the vault from raw emails, text messages, or Slack conversations. Rely strictly on daily work logs and explicit user requests to capture daily activities. This preserves vault hygiene and prevents taxonomy clutter.
- **projects/**: Contains Project notes.
- **companies/**: Contains Organization/Company notes.
- **concepts/**: Contains structured concept/definition notes.
- **personal/**: Contains personal reflections and notes.
- **notes/**: Contains quick fleeting scratchpads and brain dumps.
- **daily/**: Contains both current and archived daily notes.

## Third-party managed folders — do not touch

These folders are managed by external apps with their own schemas. Never add or modify `id`, `daily_note`, or `category` fields in these (except when performing deduplication/merges on duplicates):

- `sources/` — holds transcripts, Readwise clips, and other third-party managed integrations with separate schemas. Skipped entirely by standard required-frontmatter hygiene rules.
- `Readwise/` — article highlights imported by the Readwise plugin. Schema: `id` (non-standard timestamp format), `daily_note` (plain string, not wikilink). Do not patch these — they get overwritten on the next sync.

## Meeting Notes & Transcripts (Granola & Auto-data)

To prevent vault dilution (low-signal machine data overriding curated personal knowledge), meeting files are partitioned into three distinct tiers:

1. **Canonical Meeting Notes** (lives in `meetings/`): Curated, human-written, or polished meeting notes that represent verified personal knowledge. Only these files carry `category: "[[Meetings]]"` and are fully checked by standard vault hygiene.
2. **Raw Transcripts** (lives in `sources/meetings/transcripts/`): Auto-generated full transcripts from Granola. These carry `type: transcript` and **never** get a category property.
3. **Automated Notes / Summaries** (lives in `sources/meetings/meeting_notes/`): Raw, unmodified AI-generated summaries synced directly from Granola or other tools. These carry `type: note` and live inside `sources/` to avoid polluting the canonical `meetings/` folder. They do not undergo standard vault hygiene checks.

## Misplaced daily notes

Daily notes are sometimes accidentally saved to folders like `inbox/` or root instead of `daily/`. `gbrain lint --fix` automatically detects files matching `YYYY-MM-DD Weekday.md` and re-routes/moves them into `daily/`.

## Templates

Templates live under `<vault>/utilities/templates/` and have been massively simplified to align with gbrain-personal's prefix-driven classification. Since folder paths map automatically to page types, explicit `category: "[[CategoryName]]"` lines and tags are redundant and have been removed.

The active templates are:
1. **`daily_note.md`**: Structures the notepad, mantras, and work logs. Sets `id`.
2. **`new_note.md`**: Baseline template for manual entries (concepts, people, projects, companies, etc.). Sets `id` and `daily_note`, and auto-renames to timestamp.
3. **`new_meeting.md`**: Specialized template for meeting summaries. Sets `id` and `daily_note`, and auto-renames to date-prefix `YYYY-MM-DD`.

All other category-specific templates (person, organization, project) are obsolete and have been deleted.

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
cp "<vault>/utilities/templates/new_organization.md" "<vault>/utilities/templates/new_category.md"
sed -i 's/Organizations/Categories/' "<vault>/utilities/templates/new_category.md"
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

A consolidated hygiene script runs daily at 6AM (via the `vault-hygiene` cron job) at `~/.hermes/scripts/vault_hygiene.py`. Its cron wrapper `vault_hygiene_cron.py` filters to red-level issues only for Telegram delivery.

**How it works:**
1. It runs `gbrain lint --fix` directly to perform content sanitization and automatically move misplaced daily notes into the `daily/` directory.
2. It executes a high-speed Python check across non-archived user folders to check for duplicate IDs, missing IDs, and missing `daily_note` fields.
3. It ignores `Readwise/`, `utilities/` (including templates), `sources/` (including transcripts), `daily/` (daily notes), `.git/`, `.trash/`, and system dirs.

For the full vault structural audit (folder sizes, issue catalogue, what was found and fixed), see `references/vault-audit-2026-05-22.md`. For the hygiene script architecture and design decisions, see `references/vault-hygiene-design.md`.

## Entities and category notes

An **entity** is any note with a `category:` frontmatter field. The canonical list of entity types lives in `<vault>/Categories/`. Each category note is itself an entity (`category: "[[Categories]]"`), including `Categories/Categories.md` which is self-referential.

Current entity types (each has a file in `Categories/` and a template in `utilities/templates/`):

| Entity type | Category note | Template |
|---|---|---|
| Meetings | `Categories/Meetings.md` | `utilities/templates/new_meeting.md` |
| Organizations | `Categories/Organizations.md` | `utilities/templates/new_organization.md` |
| People | `Categories/People.md` | `utilities/templates/new_person.md` |
| Projects | `Categories/Projects.md` | `utilities/templates/new_project.md` |
| Categories | `Categories/Categories.md` | `utilities/templates/new_category.md` |

When creating a note of a given type, follow that type's template. When searching for notes by category, filter by `category: "[[CategoryName]]"`.

**Note:** As of a May 2026 vault audit, the category notes in `Categories/` have been confirmed to already carry `category: "[[Categories]]"` (e.g. `Categories/Meetings.md` has it). The stale claim that they lacked this field is no longer accurate.

### Templates (from `<vault>/utilities/templates/`)

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

## Horizontal rules

- **Standard horizontal line:** Always use exactly three hyphens `---` on a line by itself to represent a horizontal rule (horizontal line). Never use two hyphens `--` or em dashes `—` (which can be introduced by automatic smart-punctuation conversions on macOS/iOS devices).

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

## GBrain Integration

GBrain (`gbrain`) is the personal knowledge brain CLI tool indexing and searching Justin's Obsidian vault.

### Core Config

Configuration resides in `~/.gbrain/config.json` (file-plane) and inside the PGLite database plane.

### API Keys and Credentials

- **File-plane Keys:** Configured directly in `~/.gbrain/config.json`:
  - `openai_api_key`
  - `anthropic_api_key`
  - `zeroentropy_api_key`
- **Env-only Keys:** Other keys such as `OPENROUTER_API_KEY` and `GOOGLE_GENERATIVE_AI_API_KEY` (Gemini) are read directly from `process.env`. To run gbrain with these keys, ensure the environment variables are loaded (e.g. from `~/.hermes/.env` via `set -a && source ~/.hermes/.env && gbrain ...`).

### Activating or Switching Embedding Providers (PGLite)

Since pgvector (WASM) cannot alter vector columns in place, the canonical path for switching embedding models on a PGLite brain is `gbrain reinit-pglite`.

```bash
gbrain reinit-pglite --embedding-model <provider:model> --embedding-dimensions <dims>
```

- This command preserves the active database as `<path>.bak`, wipes the active DB, and runs `gbrain sync` to re-import and re-embed the vault.
- **OpenRouter Embedding:** Model is `openrouter:openai/text-embedding-3-small` with `1536` dimensions.
- **Google Gemini Embedding:** Model is `google:gemini-embedding-001` with `768` dimensions. Requires `GOOGLE_GENERATIVE_AI_API_KEY` in the environment.

### Multi-Source Management and Constraints

When adding additional directories (e.g. historical archives or secondary vaults) as separate sources to GBrain, respect these constraints:

1. **Overlap Guard (No Nested Sources):** GBrain does not allow registering nested/overlapping source directories. If your main vault is `default` at `~/vault`, you cannot add a subfolder like `~/vault/sources/old-vault` as a separate source.
   - *Workaround:* Move or clone the target folder outside of the active vault directory entirely (e.g. to `~/archive/old-vault`), then add it as a source from there.
2. **Git Requirement:** GBrain's sync pipeline (`gbrain sync --source <id>`) requires the source path to be a git-initialized repository. Raw folders will fail during `sync.validate_repo_state`.
   - *Workaround:* Always run `git init && git add . && git commit -m "Initial commit"` inside any newly registered raw folder before syncing.
3. **Destructive Guard on Removal:** Running `gbrain sources remove <id>` on a source with existing data triggers a Destructive Operation Impact Preview safety block.
   - *Workaround:* To bypass the guard and permanently cascaded-delete the source's indexed database entries, append the `--confirm-destructive` flag:
     ```bash
     gbrain sources remove <id> --yes --confirm-destructive
     ```


### Multi-Source Management and Constraints

When adding additional content repositories (sources) to GBrain, be aware of these hard rules and workarounds:

- **Overlap Guard (Nested Paths Blocked):** GBrain does not allow overlapping paths. Because the default source is registered at `~/vault`, you **cannot** register a subfolder (like `~/vault/sources/old-notes`) as a separate GBrain source. It will fail with `overlapping_path`.
- **Git Requirement:** Any directory registered as a source **must** be a git-initialized repository (has `.git/` folder and at least one commit). If it is a raw folder, run `git init && git add . && git commit -m "Initial commit"` before syncing, otherwise `gbrain sync` will fail with `Not a git repository`.
- **Sync Walker Exclusions:** The `gbrain sync` crawler (`collectSyncableFiles`) does not respect `.gitignore` folder recursion. It scans every directory recursively unless the folder starts with a dot (`.`), is named `node_modules`, or is named `ops`.
- **The Dot-Folder Workaround:** If you want to keep backup or archive note directories inside your active vault without having `gbrain sync` index them under your `default` source (and without triggering the overlap guard), prefix the folder name with a dot (e.g., `~/vault/.sources/`) and add it to `~/vault/.gitignore`.
- **Federation Settings:** When adding a new source, it defaults to `federated: false` (only searchable with `--source <id>`). To include it in unified, cross-source queries, run:
  ```bash
  gbrain sources federate <source-id>
  ```

### Integrating or Migrating Historical Vaults/Graphs

When migrating historical note archives (e.g., old Obsidian vaults, old Logseq graphs), we can either keep them separate via GBrain multi-source routing or perform a unified in-place merge:

#### Multi-Source Separation (Recommended)
Keep your current vault clean by placing backups in a separate directory and registering them as separate federated sources inside your GBrain instance:
```bash
gbrain sources add old-obsidian --path ~/archive/old-obsidian --name "Old Obsidian"
gbrain sources add old-logseq --path ~/archive/old-logseq --name "Old Logseq"
gbrain sync
```
This enables unified semantic querying across all sources without polluting your active Obsidian workspace.

#### In-Place Merge Pre-Processing
If merging historical notes directly into your active vault (`~/vault`), they must be sanitized first via scripts to comply with vault rules:
- **Migration & Sanitization Script:** A pre-made utility is available at `scripts/migrate_notes.py` within this skill. It automatically handles filename normalization, frontmatter cleanup (unquoting IDs, stripping null aliases), stripping of redundant inline typing tags (like `#zettel` or `#meeting`), and complete **Wikilink Healing**.
  - *Wikilink Healing:* Converts all internal links (e.g. `[[Old Title#Section]]`) pointing to migrated files into their lowercase kebab-case targets (`[[old-title#Section|Old Title]]`), preserving the exact visual display text while ensuring no broken links.
  - Run it using:
    ```bash
    python3 ~/.hermes/skills/note-taking/obsidian/scripts/migrate_notes.py --src <source_dir> --dest <dest_dir> [--strip-meeting]
    ```
- **Filename Normalization & Duplicate Detection:** Old vaults and graphs often use different naming conventions (e.g., Spaced Title Case like `Contacts/Aly Lalji.md`) compared to the new vault (lowercase kebab-case like `people/aly-lalji.md`).
  - To prevent duplicate files with different cases/separators, always normalize filenames to lowercase alphanumeric-hyphen (kebab-case) before comparison. A naive exact match will miss hundreds of duplicates.
  - Compute SHA-256 content hashes, but do not rely on exact matches to declare files identical; cleanup scripts (tag stripping, frontmatter updates, template enrichment) will alter content hashes. Instead, flag overlapping normalized filenames as content conflicts (Yellow) if they differ in content, and unique (Green) if the normalized name is entirely absent.
- **Logseq Graphs:** Convert outline-formatted Markdown. For converting Logseq JSON exports directly, a specialized script is available at `scripts/migrate_logseq_json.py` within this skill. It parses pages, strips block-level properties (`collapsed:: true`, etc.), resolves block-level reference IDs (`((uuid))`), normalizes filenames, and merges daily notes into the vault's active daily `## 🗒 Notepad` sections instead of overwriting them.
  - Run it using:
    ```bash
    python3 ~/.hermes/skills/note-taking/obsidian/scripts/migrate_logseq_json.py <path_to_json> <vault_root_path>
    ```

