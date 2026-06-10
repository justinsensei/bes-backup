# Resolving ID Conflicts in Justin's Vault

When personal notes were merged from `notes/personal/` into `Notes/`, many historical ID conflicts became visible. These notes were previously skipped by `vault_hygiene.py`, but are now analyzed.

## Classification of ID Conflicts

ID conflicts typically fall into three categories:

1. **Accidental Duplicate / Template Copies (Multi-Year & Consecutive Notes)**
   - **Multi-Year Copies:** Files representing the same thing with different years in the filename (e.g., `Belize 2026.md` vs `Belize 2027.md` or `Nana's birthday 2025.md` vs `Nana's birthday 2026.md`), where one is an accidental duplicate of the other.
   - **Consecutive Notes:** Notes created on back-to-back days as copies (e.g., `Jamie lawn 20260607.md` vs `Jamie lawn 20260608.md`), which are identical accidental copies.
   - **Rule:** The earlier note is the correct one. Keep the earlier note, and **delete the later/newer note** entirely. Do not keep both or regenerate IDs for these.

2. **Identical Sources (Duplicate Imports)**
   - Files with a trailing `-1` (e.g., `beyond-agile-why-facebook-et-al-didn-t-need-scrum-1.md` vs `beyond-agile-why-facebook-et-al-didn-t-need-scrum.md`).
   - **Rule:** If the files are identical, **delete the `-1` duplicate file**.
   - **Healing Links:** Check the entire vault for any internal wikilinks pointing to the `-1` file name and replace them with the non-suffixed name (e.g., `[[beyond-agile-why-facebook-et-al-didn-t-need-scrum-1]]` $\rightarrow$ `[[beyond-agile-why-facebook-et-al-didn-t-need-scrum]]`).

3. **Distinct Content sharing an ID (Clippings & Summaries)**
   - Distinct files that share an ID (e.g., a raw clipping source file and its custom summary/wrap note).
   - **Rule:** Keep both files. Assign a fresh, unique 14-digit timestamp ID to the newer note or the source file (usually the source note can be changed if the custom summary's filename contains the original ID).

4. **Batch-Generated Entities (Sequential ID Collisions)**
   - Distinct files (such as newly synchronized contacts, people, or organization notes) created in rapid succession or batches that end up with overlapping timestamp IDs (e.g., `20260610120100` shared by two different people due to simultaneous or loop-based sequential timestamp assignment).
   - **Rule:** Keep all distinct files. Assign a unique, incremented 14-digit timestamp ID to the duplicates to resolve the conflict (e.g. changing one `20260610120100` to `20260610120101` after verifying that the target ID is not already used).

---

## Resolution Recipe

Follow these steps to clean up duplicate IDs and preserve vault integrity:

### Step 1 — Identify the Clashing Notes
Review the hygiene report output or run `vault_hygiene.py` to get the duplicate list:
```bash
python3 ~/.hermes/scripts/vault_hygiene.py
```
This prints the files sharing a specific ID.

### Step 2 — Determine the Conflict Class
Classify each clash using the definitions above:
- If **Multi-Year / Consecutive Duplicate**: Determine which is the earlier note. Delete the later one.
- If **Identical Source Duplicate (`-1` file)**: Delete the `-1` file and globally heal any internal wikilinks in the vault that target it.
- If **Distinct Content**: Choose one note (usually the raw source file) to receive a fresh unique ID.

### Step 3 — Regenerating IDs (Distinct Content Only)
For distinct content, determine a new unique ID based on the creation or modification date. Format it as a 14-digit `YYYYMMDDHHmmss` timestamp.
- Find a unique 14-digit timestamp that is not currently in use anywhere in the vault.
- Update the frontmatter using `patch`:
  ```yaml
  ---
  id: 20250604081546
  ...
  ```

### Step 4 — Verify
Re-run the hygiene check to confirm all conflicts have cleared:
```bash
python3 ~/.hermes/scripts/vault_hygiene.py
```
