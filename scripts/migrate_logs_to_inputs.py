#!/usr/bin/env python3
"""
migrate_logs_to_inputs.py — One-time vault taxonomy migration: Logs/ → Inputs/.

Dry-run by default. Pass --apply to execute moves and category fixes.

Pause bes-vault-sync during bulk rename; restart after.
"""

import argparse
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path


FOLDER_MAP = {
    "Logs/Sources": "Inputs/Readings",
    "Logs/Readings": "Inputs/Readings",
    "Logs/Meetings": "Inputs/Meetings",
    "Logs/Emails": "Inputs/Emails",
    "Logs/Slack": "Inputs/Slack",
    "Logs/Granola": "Inputs/Meetings",
}

SUBFOLDER_MERGE = {
    "Sources": "Readings",
    "Readings": "Readings",
    "Meetings": "Meetings",
    "Emails": "Emails",
    "Slack": "Slack",
    "Granola": "Meetings",
}


def vault_path():
    return Path(os.environ.get("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/Developer/obsidian-vault")))


def heal_wikilink_text(text):
    return re.sub(r"\[\[Logs/", "[[Inputs/", text)


def collect_md_files(vault, rel_dir):
    base = vault / rel_dir
    if not base.exists():
        return []
    return sorted(base.rglob("*.md"))


def plan_folder_moves(vault):
    moves = []
    collisions = []
    logs = vault / "Logs"
    inputs = vault / "Inputs"

    if not logs.exists():
        return moves, collisions

    for old_rel, new_rel in FOLDER_MAP.items():
        old_parts = old_rel.split("/")
        new_parts = new_rel.split("/")
        src = vault.joinpath(*old_parts)
        if not src.exists():
            continue
        dest = vault.joinpath(*new_parts)
        for src_file in src.rglob("*"):
            if not src_file.is_file():
                continue
            rel_under = src_file.relative_to(src)
            dest_file = dest / rel_under
            if dest_file.exists() and src_file.resolve() != dest_file.resolve():
                collisions.append((str(src_file.relative_to(vault)), str(dest_file.relative_to(vault))))
            else:
                moves.append((src_file, dest_file))

    if inputs.exists() and logs.exists():
        for sub, target_sub in SUBFOLDER_MERGE.items():
            legacy = logs / sub
            if not legacy.exists() or sub in ("Sources", "Readings") and (inputs / "Readings").exists():
                pass

    return moves, collisions


def scan_category_fixes(vault):
    fixes = []
    for path in vault.rglob("*.md"):
        rel = str(path.relative_to(vault)).replace("\\", "/")
        if not rel.startswith(("Inputs/Readings/", "Logs/Readings/", "Logs/Sources/")):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        if end <= 0:
            continue
        fm = text[3:end]
        if re.search(r'^category:\s*["\']?\[\[Sources\]\]["\']?', fm, re.MULTILINE):
            fixes.append(rel)
    return fixes


def scan_legacy_links(vault):
    issues = defaultdict(list)
    for path in vault.rglob("*.md"):
        rel = str(path.relative_to(vault)).replace("\\", "/")
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for link in re.findall(r"\[\[(Logs/[^\]|#]+)", text):
            issues[rel].append(link)
    return issues


def apply_folder_migration(vault, apply):
    logs = vault / "Logs"
    inputs = vault / "Inputs"
    moved = []

    if not logs.exists():
        print("No Logs/ folder — nothing to migrate.")
        return moved

    inputs.mkdir(exist_ok=True)

    for sub in sorted(logs.iterdir()):
        if not sub.is_dir():
            continue
        target_sub = SUBFOLDER_MERGE.get(sub.name)
        if not target_sub:
            print(f"  SKIP unmapped Logs/{sub.name}/")
            continue
        dest = inputs / target_sub
        dest.mkdir(parents=True, exist_ok=True)
        for item in sorted(sub.iterdir()):
            dest_item = dest / item.name
            if dest_item.exists():
                print(f"  COLLISION: {item.relative_to(vault)} → {dest_item.relative_to(vault)} (manual resolve)")
                continue
            if apply:
                shutil.move(str(item), str(dest_item))
            moved.append((str(item.relative_to(vault)), str(dest_item.relative_to(vault))))
            print(f"  {'MOVE' if apply else 'DRY-RUN'}: {item.relative_to(vault)} → {dest_item.relative_to(vault)}")

    if apply and logs.exists():
        remaining = list(logs.iterdir())
        if not remaining:
            logs.rmdir()
            print("  Removed empty Logs/")

    return moved


def apply_category_fixes(vault, apply):
    fixed = []
    for path in vault.rglob("*.md"):
        rel = str(path.relative_to(vault)).replace("\\", "/")
        if not rel.startswith(("Inputs/Readings/", "Logs/Readings/", "Logs/Sources/")):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        if end <= 0:
            continue
        fm = text[3:end]
        new_fm = re.sub(
            r'^category:\s*["\']?\[\[Sources\]\]["\']?',
            'category: "[[Readings]]"',
            fm,
            count=1,
            flags=re.MULTILINE,
        )
        if new_fm == fm:
            continue
        fixed.append(rel)
        if apply:
            new_text = f"---\n{new_fm}\n---\n" + text[end + 4:]
            path.write_text(new_text, encoding="utf-8")

    return fixed


def apply_wikilink_heal(vault, apply):
    healed = []
    for path in vault.rglob("*.md"):
        rel = str(path.relative_to(vault)).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="replace")
        new_text = heal_wikilink_text(text)
        if new_text != text:
            healed.append(rel)
            if apply:
                path.write_text(new_text, encoding="utf-8")
    return healed


def main():
    parser = argparse.ArgumentParser(description="Migrate vault Logs/ → Inputs/")
    parser.add_argument("--apply", action="store_true", help="Execute changes (default: dry-run)")
    args = parser.parse_args()

    vault = vault_path()
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== migrate_logs_to_inputs ({mode}) ===")
    print(f"Vault: {vault}\n")

    if not vault.exists():
        print(f"ERROR: vault not found at {vault}")
        return 1

    moved = apply_folder_migration(vault, args.apply)
    print(f"\nFolder moves: {len(moved)}")

    cat_fixes = apply_category_fixes(vault, args.apply)
    print(f"Category fixes ([[Sources]]→[[Readings]] on inputs): {len(cat_fixes)}")
    for f in cat_fixes[:20]:
        print(f"  - {f}")
    if len(cat_fixes) > 20:
        print(f"  ... and {len(cat_fixes) - 20} more")

    link_heals = apply_wikilink_heal(vault, args.apply)
    print(f"Wikilink heals (Logs/→Inputs/): {len(link_heals)}")

    legacy = scan_legacy_links(vault)
    if legacy:
        print(f"\nUnresolved legacy Logs/ links: {len(legacy)} files")
        for rel, links in sorted(legacy.items())[:10]:
            print(f"  - {rel}: {links[:3]}")

    print("\nPost-migration VM steps:")
    print("  1. Update ~/sync_readwise.py export path → vault/Inputs/Readings/")
    print("  2. python3 ~/.hermes/scripts/semantic_pointer.py index")
    print("  3. Restart bes-vault-sync")
    print("  4. python3 ~/.hermes/scripts/vault_hygiene.py")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
