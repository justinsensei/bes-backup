#!/usr/bin/env python3
"""
vault_hygiene.py — Obsidian vault hygiene check + auto-fix.

Auto-fixes:
  1. Move misplaced daily notes (YYYY-MM-DD Weekday.md) from Notebook/ to Daily Notes/
  2. Convert inline category tags (#meetings, #people, etc.) to category: frontmatter,
     remove the tag, and move the note to Notebook/ if not already there.

Reports (stdout, one section per issue type):
  - Wrong-folder notes (non-daily typed notes outside Notebook/)
  - ID conflicts (two notes share the same id)
  - Notes missing an id (excluding Granola, Readwise, Templates, Daily Notes)
  - Notes missing a daily_note link (excluding Granola, Readwise, Templates, Daily Notes)

Exits 0 (no issues) or 1 (issues found / fixes applied).
Dry-run mode: set DRY_RUN=1 env var.
"""

import os
import re
import sys
import shutil
from collections import defaultdict
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/justin.guest/vault"))
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# Folders to ignore for most checks
IGNORE_DIRS = {"Granola", "Readwise", "Templates", "Daily Notes", ".git", ".trash", ".cursor", ".claude", "ustin.guest"}

# Valid category names and their canonical wikilink form
CATEGORY_MAP = {
    "meetings":      "[[Meetings]]",
    "meeting":       "[[Meetings]]",
    "people":        "[[People]]",
    "person":        "[[People]]",
    "organizations": "[[Organizations]]",
    "organisation":  "[[Organizations]]",
    "organization":  "[[Organizations]]",
    "projects":      "[[Projects]]",
    "project":       "[[Projects]]",
}

WEEKDAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

# Pattern: YYYY-MM-DD Weekday.md  (misplaced daily note)
DAILY_NOTE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2} (" + "|".join(WEEKDAYS) + r")\.md$"
)

def read_note(path: Path):
    """Return (raw_text, frontmatter_dict, body_after_fm)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return text, {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return text, {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    # Very lightweight YAML parse: key: value, handles quoted values
    fm = {}
    for line in fm_raw.splitlines():
        m = re.match(r'^(\w+):\s*(.*)', line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"\'')
    return text, fm, body

def write_note(path: Path, text: str, dry_run=False):
    if dry_run:
        print(f"  [DRY RUN] would write: {path}")
        return
    path.write_text(text, encoding="utf-8")

def move_note(src: Path, dst: Path, dry_run=False):
    if dry_run:
        print(f"  [DRY RUN] would move: {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

def all_notes(skip_dirs=None):
    """Yield all .md paths under vault, skipping specified top-level dirs."""
    skip = skip_dirs or set()
    for root, dirs, files in os.walk(VAULT):
        root_path = Path(root)
        # Prune ignored dirs (only at top level for IGNORE_DIRS)
        if root_path == VAULT:
            dirs[:] = [d for d in dirs if d not in skip]
        else:
            dirs[:] = [d for d in dirs if d not in {".git", ".trash"}]
        for f in files:
            if f.endswith(".md"):
                yield root_path / f

def frontmatter_set(text: str, key: str, value: str) -> str:
    """Set a frontmatter key=value in raw note text. Adds if missing."""
    if not text.startswith("---"):
        return f'---\n{key}: {value}\n---\n\n{text}'
    end = text.find("\n---", 3)
    if end == -1:
        return text
    fm_block = text[3:end]
    # Replace existing key
    pattern = re.compile(rf'^{re.escape(key)}:.*$', re.MULTILINE)
    if pattern.search(fm_block):
        new_fm = pattern.sub(f'{key}: {value}', fm_block)
    else:
        new_fm = fm_block.rstrip() + f'\n{key}: {value}'
    return "---" + new_fm + text[end:]

def frontmatter_remove_blank_category(text: str) -> str:
    """Remove a bare 'category:' line with no value."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    fm_block = text[3:end]
    new_fm = re.sub(r'\ncategory:\s*$', '', fm_block, flags=re.MULTILINE)
    return "---" + new_fm + text[end:]

def remove_tag_from_body(text: str, tag: str) -> str:
    """Remove #tag from note body. Handles standalone or inline."""
    # Remove standalone tag line
    text = re.sub(rf'^\s*#{re.escape(tag)}\s*$', '', text, flags=re.MULTILINE)
    # Remove inline tag (surrounded by whitespace or EOL)
    text = re.sub(rf'\s+#{re.escape(tag)}(?=\s|$)', ' ', text)
    text = re.sub(rf'^#{re.escape(tag)}\s+', '', text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + '\n'

# ─── main ────────────────────────────────────────────────────────────────────

fixes_applied = []
issues = defaultdict(list)  # issue_type -> list of (path, detail)

# ── 1. Misplaced daily notes (Notebook/ → Daily Notes/) ───────────────────
notebook_dir = VAULT / "Notebook"
daily_notes_dir = VAULT / "Daily Notes"

for path in sorted(notebook_dir.glob("*.md")):
    if DAILY_NOTE_PATTERN.match(path.name):
        dst = daily_notes_dir / path.name
        if dst.exists():
            issues["wrong_folder_conflict"].append((path, f"target already exists: {dst}"))
        else:
            move_note(path, dst, dry_run=DRY_RUN)
            fixes_applied.append(f"Moved misplaced daily note: Notebook/{path.name} → Daily Notes/{path.name}")

# ── 2. Category tag → frontmatter conversion ─────────────────────────────
# Scan all notes (skip ignored dirs) for #tag that matches a known category
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS)):
    text = path.read_text(encoding="utf-8", errors="replace")
    _, fm, _ = read_note(path)

    existing_category = fm.get("category", "").strip()
    # Skip notes that already have a valid category
    if existing_category and existing_category not in ("", "[[]]"):
        continue

    # Find matching category tags
    tag_matches = []
    for tag, wikilink in CATEGORY_MAP.items():
        # Match #tag as standalone line or inline (word boundary)
        if re.search(rf'(?m)(?:^|\s)#{re.escape(tag)}(?:\s|$)', text):
            tag_matches.append((tag, wikilink))

    if not tag_matches:
        continue

    # Use first match (most notes will only have one)
    tag, wikilink = tag_matches[0]
    category_value = f'"{wikilink}"'

    # Remove blank category: line if present, then set proper value
    new_text = frontmatter_remove_blank_category(text)
    new_text = frontmatter_set(new_text, "category", category_value)
    new_text = remove_tag_from_body(new_text, tag)

    # Also move to Notebook/ if not already there and not in vault root
    in_notebook = path.parent == notebook_dir
    in_root = path.parent == VAULT

    if new_text != text or not in_notebook:
        write_note(path, new_text, dry_run=DRY_RUN)

        # If not in Notebook/ and not in root, flag it (we don't auto-move arbitrary notes)
        if not in_notebook and not in_root:
            issues["wrong_folder"].append(
                (path, f"has category {wikilink} but lives in {path.parent.name}/")
            )
        fixes_applied.append(
            f"Converted tag #{tag} → category: {category_value}: {path.relative_to(VAULT)}"
        )

# ── 3. Wrong-folder check: typed notes outside Notebook/ ─────────────────
# (Any note with a category wikilink that isn't in Notebook/ or root)
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS)):
    _, fm, _ = read_note(path)
    category = fm.get("category", "")
    if not category:
        continue
    # Normalise
    cat_clean = category.strip().strip('"\'')
    if not cat_clean.startswith("[["):
        continue
    in_notebook = path.parent == notebook_dir
    in_root = path.parent == VAULT
    if not in_notebook and not in_root:
        # Report but don't auto-move (user said they want to handle root manually)
        issues["wrong_folder"].append(
            (path, f"category {cat_clean} but lives in {path.parent.relative_to(VAULT)}/")
        )

# Deduplicate wrong_folder (tag-conversion step may have already added some)
seen = set()
deduped = []
for item in issues["wrong_folder"]:
    if item[0] not in seen:
        seen.add(item[0])
        deduped.append(item)
issues["wrong_folder"] = deduped

# ── 4. ID conflict check ──────────────────────────────────────────────────
id_to_paths = defaultdict(list)
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS | {"Daily Notes"})):
    _, fm, _ = read_note(path)
    note_id = fm.get("id", "").strip()
    if note_id:
        id_to_paths[note_id].append(path)

for note_id, paths in id_to_paths.items():
    if len(paths) > 1:
        for p in paths:
            issues["id_conflict"].append((p, f"id={note_id} shared with {len(paths)-1} other note(s)"))

# ── 5. Missing ID ─────────────────────────────────────────────────────────
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS | {"Daily Notes"})):
    _, fm, _ = read_note(path)
    note_id = fm.get("id", "").strip()
    if not note_id:
        issues["missing_id"].append((path, "no id field"))

# ── 6. Missing daily_note link ────────────────────────────────────────────
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS | {"Daily Notes"})):
    _, fm, _ = read_note(path)
    dn = fm.get("daily_note", "").strip()
    if not dn:
        issues["missing_daily_note"].append((path, "no daily_note field"))
    elif "[[" not in dn:
        issues["missing_daily_note"].append((path, f"daily_note not a wikilink: {dn!r}"))

# ─── Output ──────────────────────────────────────────────────────────────────

def rel(p):
    return str(p.relative_to(VAULT))

lines = []

if fixes_applied:
    lines.append("## ✅ Auto-fixes applied" + (" (DRY RUN)" if DRY_RUN else ""))
    for f in fixes_applied:
        lines.append(f"  - {f}")

if issues["wrong_folder_conflict"]:
    lines.append("\n## ⚠️  Move conflicts (needs manual attention)")
    for p, detail in issues["wrong_folder_conflict"]:
        lines.append(f"  - {rel(p)}: {detail}")

if issues["wrong_folder"]:
    lines.append("\n## ⚠️  Notes in wrong folder")
    for p, detail in issues["wrong_folder"]:
        lines.append(f"  - {rel(p)}: {detail}")

if issues["id_conflict"]:
    lines.append("\n## 🔴 ID conflicts")
    for p, detail in issues["id_conflict"]:
        lines.append(f"  - {rel(p)}: {detail}")

if issues["missing_id"]:
    lines.append("\n## 🔴 Missing ID")
    for p, detail in issues["missing_id"]:
        lines.append(f"  - {rel(p)}")

if issues["missing_daily_note"]:
    lines.append("\n## 🔴 Missing daily_note")
    for p, detail in issues["missing_daily_note"]:
        lines.append(f"  - {rel(p)}: {detail}")

if not lines:
    print("✅ Vault looks clean — no issues found.")
    sys.exit(0)
else:
    print("\n".join(lines))
    sys.exit(1)
