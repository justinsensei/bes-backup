#!/usr/bin/env python3
"""
vault_hygiene.py — Obsidian vault hygiene check + auto-fix.

Auto-fixes:
  1. Move misplaced daily notes (YYYY-MM-DD Weekday.md) from Notebook/ to Daily Notes/
  2. Convert inline category tags (#meetings, #people, etc.) to category: frontmatter
     and remove the tag — but ONLY for People and Organizations (low-ambiguity types).
     Projects and Meetings require the note to have a date-prefix filename (YYYY-MM-DD)
     to qualify, because #project/#meeting tags are often used loosely on non-object notes.
  3. Add category: "[[Meetings]]" to Granola/ meeting notes (type: note or no type field)
     that are missing it. Transcripts (type: transcript) are skipped.

Reports (stdout):
  - Wrong-folder notes (typed notes not in Notebook/ or vault root)
  - ID conflicts
  - Notes missing an id
  - Notes missing a daily_note wikilink

Ignored folders (general walks): Readwise, Templates, Daily Notes, Categories,
                 Granola (scanned separately), .git, .trash, .cursor, .claude

Exits 0 (clean) or 1 (fixes applied / issues found).
Dry-run: DRY_RUN=1
"""

import os
import re
import sys
import shutil
from collections import defaultdict
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/justin.guest/vault"))
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

IGNORE_DIRS = {
    "Readwise", "Templates", "Daily Notes",
    "Categories", ".git", ".trash", ".cursor", ".claude", "ustin.guest",
}

# Meetings is scanned separately for category checks; skip it in general walks
IGNORE_DIRS_WITH_MEETINGS = IGNORE_DIRS | {"Meetings", "Granola"}

MEETINGS_DIR = VAULT / "Meetings"

WEEKDAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
DAILY_NOTE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2} (" + "|".join(WEEKDAYS) + r")\.md$"
)

# Tags that unambiguously identify a note type regardless of filename
ALWAYS_CONVERT = {
    "people":        '[[People]]',
    "person":        '[[People]]',
    "organizations": '[[Organizations]]',
    "organisation":  '[[Organizations]]',
    "organization":  '[[Organizations]]',
}

# Tags that only convert if filename has a YYYY-MM-DD prefix (meeting/project notes
# are more likely to have these tags with a date-stamped name)
DATE_PREFIX_CONVERT = {
    "meetings": '[[Meetings]]',
    "meeting":  '[[Meetings]]',
    "projects": '[[Projects]]',
    "project":  '[[Projects]]',
}

DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2} ")

NOTEBOOK_DIR   = VAULT / "Notebook"
DAILY_DIR      = VAULT / "Daily Notes"
CATEGORIES_DIR = VAULT / "Categories"

MEETINGS_CATEGORY = '"[[Meetings]]"'


# ─── Helpers ─────────────────────────────────────────────────────────────────

def read_note(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return text, {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return text, {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    fm = {}
    for line in fm_raw.splitlines():
        m = re.match(r'^(\w+):\s*(.*)', line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"\'')
    return text, fm, body


def frontmatter_set(text: str, key: str, value: str) -> str:
    """Set key=value in frontmatter. Adds key if missing."""
    if not text.startswith("---"):
        return f'---\n{key}: {value}\n---\n\n{text}'
    end = text.find("\n---", 3)
    if end == -1:
        return text
    fm_block = text[3:end]
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


def remove_tag(text: str, tag: str) -> str:
    """Remove #tag from note, then collapse extra blank lines."""
    # Standalone line
    text = re.sub(rf'^[ \t]*#{re.escape(tag)}[ \t]*$', '', text, flags=re.MULTILINE)
    # Inline (between words / at end of line)
    text = re.sub(rf'(?<=\s)#{re.escape(tag)}(?=\s|$)', '', text)
    text = re.sub(rf'^#{re.escape(tag)}(?=\s|$)', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + '\n'


def write_note(path: Path, text: str):
    if DRY_RUN:
        print(f"  [DRY RUN] would write: {path}")
        return
    path.write_text(text, encoding="utf-8")


def move_file(src: Path, dst: Path):
    if DRY_RUN:
        print(f"  [DRY RUN] would move: {src} → {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))


def all_notes(skip_dirs=None):
    skip = (skip_dirs or set()) | {"Copilot", "Granola"}
    for root, dirs, files in os.walk(VAULT):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip]
        for f in sorted(files):
            if f.endswith(".md"):
                yield root_path / f


# ─── Main ────────────────────────────────────────────────────────────────────

fixes_applied = []
issues = defaultdict(list)

# ── 1. Misplaced daily notes: Notebook/ → Daily Notes/ ───────────────────────
for path in sorted(NOTEBOOK_DIR.glob("*.md")):
    if DAILY_NOTE_PATTERN.match(path.name):
        dst = DAILY_DIR / path.name
        if dst.exists():
            issues["move_conflict"].append(
                (path, f"target already exists: {dst}")
            )
        else:
            move_file(path, dst)
            fixes_applied.append(
                f"Moved misplaced daily note: Notebook/{path.name} → Daily Notes/{path.name}"
            )

# ── 2. Category tag → frontmatter ────────────────────────────────────────────
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS_WITH_MEETINGS)):
    text, fm, _ = read_note(path)

    existing_cat = fm.get("category", "").strip().strip('"\'')
    if existing_cat and existing_cat not in ("", "[[]]"):
        continue  # already has a real category

    found_tag = None
    found_wikilink = None

    # Check always-convert tags
    for tag, wikilink in ALWAYS_CONVERT.items():
        if re.search(rf'(?m)(?:^|(?<=\s))#{re.escape(tag)}(?=\s|$)', text):
            found_tag, found_wikilink = tag, wikilink
            break

    # Check date-prefix-only tags
    if not found_tag and DATE_PREFIX_RE.match(path.name):
        for tag, wikilink in DATE_PREFIX_CONVERT.items():
            if re.search(rf'(?m)(?:^|(?<=\s))#{re.escape(tag)}(?=\s|$)', text):
                found_tag, found_wikilink = tag, wikilink
                break

    if not found_tag:
        continue

    new_text = frontmatter_remove_blank_category(text)
    new_text = frontmatter_set(new_text, "category", f'"{found_wikilink}"')
    new_text = remove_tag(new_text, found_tag)

    if new_text != text:
        write_note(path, new_text)
        fixes_applied.append(
            f"Converted tag #{found_tag} → category: \"{found_wikilink}\": "
            f"{path.relative_to(VAULT)}"
        )

# ── 3. Wrong-folder: typed notes outside Notebook/ ───────────────────────────
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS_WITH_MEETINGS)):
    _, fm, _ = read_note(path)
    cat = fm.get("category", "").strip().strip('"\'')
    if not cat or not cat.startswith("[["):
        continue
    in_notebook = path.parent == NOTEBOOK_DIR
    in_root     = path.parent == VAULT
    if not in_notebook and not in_root:
        issues["wrong_folder"].append(
            (path, f"category {cat} but lives in {path.parent.relative_to(VAULT)}/")
        )

# ── 4. Meeting notes missing category: "[[Meetings]]" ────────────────────────
# Meetings folder holds meeting summaries and a Transcripts/ subfolder.
# Only summaries should carry the Meetings category.
if MEETINGS_DIR.exists():
    for path in sorted(MEETINGS_DIR.glob("*.md")):
        text, fm, _ = read_note(path)
        note_type = fm.get("type", "note").strip().strip('"\'').lower()
        if note_type == "transcript":
            continue  # transcripts don't get a category
        existing_cat = fm.get("category", "").strip().strip('"\'')
        if existing_cat == "[[Meetings]]":
            continue  # already correct
        # Auto-fix: add the Meetings category
        new_text = frontmatter_set(text, "category", MEETINGS_CATEGORY)
        if new_text != text:
            write_note(path, new_text)
            fixes_applied.append(
                f"Added category [[Meetings]] to meeting note: Meetings/{path.name}"
            )

# ── 5. ID conflicts ───────────────────────────────────────────────────────────
id_to_paths = defaultdict(list)
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS_WITH_MEETINGS | {"Daily Notes"})):
    _, fm, _ = read_note(path)
    note_id = fm.get("id", "").strip()
    if note_id:
        id_to_paths[note_id].append(path)

for note_id, paths in sorted(id_to_paths.items()):
    if len(paths) > 1:
        for p in paths:
            issues["id_conflict"].append(
                (p, f"id={note_id!r} shared by {len(paths)} notes")
            )

# ── 6. Missing ID ─────────────────────────────────────────────────────────────
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS_WITH_MEETINGS | {"Daily Notes"})):
    _, fm, _ = read_note(path)
    note_id = fm.get("id", "").strip()
    if not note_id:
        issues["missing_id"].append((path, ""))

# ── 7. Missing daily_note ─────────────────────────────────────────────────────
# Also exclude vault-root daily notes (YYYY-MM-DD Weekday.md in root)
for path in sorted(all_notes(skip_dirs=IGNORE_DIRS_WITH_MEETINGS | {"Daily Notes"})):
    if path.parent == VAULT and DAILY_NOTE_PATTERN.match(path.name):
        continue  # current daily note in root — self-referential, skip
    _, fm, _ = read_note(path)
    dn = fm.get("daily_note", "").strip()
    if not dn:
        issues["missing_daily_note"].append((path, "no daily_note field"))
    elif "[[" not in dn:
        issues["missing_daily_note"].append(
            (path, f"daily_note not a wikilink: {dn!r}")
        )


# ─── Output ──────────────────────────────────────────────────────────────────

def rel(p: Path) -> str:
    return str(p.relative_to(VAULT))


lines = []

if fixes_applied:
    lines.append("## ✅ Auto-fixes applied" + (" (DRY RUN)" if DRY_RUN else ""))
    for f in fixes_applied:
        lines.append(f"  - {f}")

if issues["move_conflict"]:
    lines.append("\n## ⚠️  Move conflicts (needs manual attention)")
    for p, detail in issues["move_conflict"]:
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
    for p, _ in issues["missing_id"]:
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
