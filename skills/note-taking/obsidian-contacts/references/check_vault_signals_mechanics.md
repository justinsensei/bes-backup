# Mechanics of the check_vault_signals Background Script

The `check_vault_signals.py` script is a background process that runs in Justin's vault environment. Its purpose is to scan modified files, automatically build contact timelines, and flag unresolved links as candidate contacts for the morning briefing. Understanding its exact mechanics is essential for preventing timeline pollution and duplicate notes.

---

## Technical Specifications

- **Active Path**: `~/.hermes/scripts/check_vault_signals.py` (and duplicated under `~/.hermes/skills/daily-rituals/morning-briefing/scripts/check_vault_signals.py` for execution context).
- **State File**: `~/.hermes/state/vault_signals_watermark.json` (stores the timestamp of the last successful run; only files modified after this watermark are scanned).
- **Output Report**: `~/.hermes/morning-briefing/vault_signals_last_run.json` (parsed by the morning briefing generator to display discovered contacts).

---

## Core Operations

### 1. Entity Indexing (`get_existing_entities`)
The script builds an index of all existing entities across three folders:
1.  `vault/Contacts/` (Permanent directory)
2.  `vault/Inbox/` (Bes default landing folder)
3.  `vault/Notes/Projects/` (Project notes)

A markdown file is registered as a contact if it has `category: "[[People]]"`, `category: "[[Organizations]]"`, or `type: ...` in its YAML frontmatter. The script extracts the file name (lowercased) as the primary lookup key, and also registers any strings listed in the frontmatter `aliases:` block.

### 2. Timeline Enrichment (`scan_file_for_signals`)
For every file modified since the watermark, the script searches for references to registered contacts using three strategies in order:
1.  **Direct Wikilinks**: Checks for lowercased links pointing to the file (e.g. `[[mac lawrence]]` or `[[mac lawrence]]`).
2.  **Exact Text Matches**: Checks for the lowercased filename as a word-bounded phrase (e.g., `\bmac lawrence\b`).
3.  **Alias Matches**: Checks for any of the contact's aliases as a word-bounded phrase (e.g., `\bmac\b`).

If a match is found, the script automatically prepends a reverse-chronological timeline bullet to the target contact note using case-preserved shortest-path wikilinks:
` - YYYY-MM-DD | Mentioned in [[source_title]]` (or `[[link_target|source_title]]` if a name collision exists like `Cracking the Pm Career`).

### 3. Unresolved Link Discovery (`scan_file_for_unresolved_links`)
The script parses all wikilinks of the form `[[Link]]` or `[[Link|display_text]]` in scanned files. It filters out system names, daily notes, image attachments, and slashes.
- If a link's target name is **not** on disk as a filename, **and** does not match any alias of any registered contact, it is flagged as an **unresolved link candidate** of type `person` or `organization` (based on typical suffix keywords).

---

## Primary Failure Modes & Root Causes

### Failure Mode A: First-Name Alias Hijacking
- **The Bug**: When a contact (like `Mac Lawrence` or `Linda Massie`) registers a highly generic first name (like `Mac`, `Linda`, or `Georgia`) as an alias, the word-boundary search (`\bmac\b`) will match completely unrelated technical phrases (such as `macOS`, `MacMini`, `Mac Studio`, `Georgia Tech`, or `Linda` representing an unnamed friend of a friend).
- **The Result**: Unrelated technical logs, business meetings, or regional notes automatically write fake timeline entries onto your family members' contact notes, causing severe timeline pollution.

### Failure Mode B: Phantom Ghost Links
- **The Bug**: If a generic first-name file does not exist (e.g., `sam.md` or `andy.md`) but was linked in a draft, the background script or prior processes may automatically append `- YYYY-MM-DD | Mentioned in [[sam]]` into other contact or organization notes (like `signlab.md` or `smartpass.md`).
- **The Result**: These files accumulate unresolvable "ghost" timeline references that never link to a real contact card, creating clutter and generating constant unresolved link warnings.

---

## Triage & Resolution Protocol

When cleaning up duplicate or polluted contacts, follow this sequence:

1.  **Strip Broad Aliases**: Edit the target contact note's frontmatter and remove any highly common/generic first-name aliases (e.g. remove `Mac` from `Mac Lawrence.md`).
2.  **Clean Target Timelines**: Open the polluted contact's note and manually delete any incorrect timeline bullets (e.g. remove macOS or Mac Mini entries from Mac Lawrence's card).
3.  **Global Ghost Link Cleanup**: Run a global search across the vault for the phantom links (e.g. search for `[[Contacts/sam` or `[[Contacts/Sam`).
    -   *If self-referential or erroneous*: Delete the timeline bullet entirely (common in shared contact sheets or cards of other people sharing a similar first name).
    -   *If genuine family mention*: Update the wikilink to point explicitly to the capitalized, full-name card (e.g., change `[[sam]]` to `[[Sam Goff|sam]]`).
4.  **Delete Generic Notes**: Delete any remaining lowercase or first-name-only contact files (e.g. remove `Contacts/ryan.md` or `Contacts/sam.md`).
