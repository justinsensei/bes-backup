#!/usr/bin/env python3
"""One-shot normalizer for Bes SKILL.md frontmatter and required sections."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

STUB_PITFALLS = """
## Common Pitfalls

1. Skipping the skill and improvising paths or conventions.
2. Hardcoding `/home/justin.guest/` instead of `$OBSIDIAN_VAULT_PATH` / `${HERMES_HOME}`.
"""

STUB_CHECKLIST = """
## Verification Checklist

- [ ] Followed this skill's steps without contradicting `obsidian` core conventions
- [ ] Used env-var path patterns where writing to vault or calling scripts
- [ ] Did not manually `git commit` inside the vault
"""

RELATED_FIXES: dict[str, dict] = {
    "kanban-codex-lane": {
        "related_skills": [],
        "external_related_skills": ["kanban-worker", "codex", "hermes-agent"],
    },
    "comfyui": {"related_skills": [], "external_related_skills": []},
    "native-mcp": {"related_skills": [], "external_related_skills": ["mcporter"]},
    "spotify": {"related_skills": [], "external_related_skills": ["gif-search"]},
    "bes-email-dispatch": {"related_skills": ["google-workspace", "obsidian", "bes-email-ingest"]},
    "bes-email-ingest": {"related_skills": ["bes-email-dispatch", "google-workspace", "obsidian"]},
    "google-workspace": {
        "related_skills": ["obsidian"],
        "external_related_skills": ["himalaya"],
    },
    "arxiv": {"related_skills": [], "external_related_skills": ["ocr-and-documents"]},
    "debugging-hermes-tui-commands": {
        "related_skills": [],
        "external_related_skills": ["python-debugpy", "node-inspect-debugger", "systematic-debugging"],
    },
    "subagent-driven-development": {
        "related_skills": ["writing-plans"],
        "external_related_skills": ["requesting-code-review", "test-driven-development"],
    },
    "writing-plans": {
        "related_skills": ["subagent-driven-development"],
        "external_related_skills": ["test-driven-development", "requesting-code-review"],
    },
    "obsidian": {
        "related_skills": [
            "obsidian-people",
            "obsidian-organizations",
            "obsidian-notes",
            "obsidian-logs",
            "obsidian-utilities",
            "obsidian-hygiene",
        ],
    },
    "manage-projects": {
        "related_skills": ["todoist", "obsidian"],
        "deprecated": True,
    },
    "morning-briefing": {
        "related_skills": ["work-log", "todoist-inbox-fill", "obsidian-hygiene", "todoist"],
    },
}


def parse_fm(content: str) -> tuple[dict, str, str]:
    end = content.find("\n---", 3)
    raw = content[3:end]
    body = content[end + 4 :]
    if body.startswith("\n"):
        body = body[1:]
    return yaml.safe_load(raw), raw, body


def dump_fm(fm: dict) -> str:
    return yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()


def ensure_use_when(desc: str, name: str) -> str:
    if desc.startswith("Use when"):
        return desc
    d = desc.strip().strip('"')
    if d.upper().startswith("DEPRECATED"):
        return f'Use when reviewing historical context only. {d}'
    return f"Use when working with {name.replace('-', ' ')}. {d}"


def normalize_file(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False
    fm, _, body = parse_fm(content)
    name = fm.get("name", path.parent.name)
    changed = False

    if "related_skills" in fm and "metadata" not in fm:
        rs = fm.pop("related_skills")
        fm.setdefault("metadata", {}).setdefault("hermes", {})["related_skills"] = rs
        changed = True
    if "tags" in fm:
        tags = fm.pop("tags")
        fm.setdefault("metadata", {}).setdefault("hermes", {})["tags"] = tags
        changed = True

    fm.setdefault("version", "1.0.0")
    fm.setdefault("author", "Bes")
    fm.setdefault("license", "MIT")
    fm.setdefault("platforms", ["linux"])
    meta = fm.setdefault("metadata", {})
    hermes = meta.setdefault("hermes", {})
    hermes.setdefault("tags", [name.split("-")[0]])

    if name in RELATED_FIXES:
        fix = RELATED_FIXES[name]
        for k, v in fix.items():
            if hermes.get(k) != v:
                hermes[k] = v
                changed = True

    if isinstance(fm.get("description"), str):
        new_desc = ensure_use_when(fm["description"], name)
        if new_desc != fm["description"]:
            fm["description"] = new_desc
            changed = True

    if "## Common Pitfalls" not in body:
        body = body.rstrip() + STUB_PITFALLS
        changed = True
    if "## Verification Checklist" not in body:
        body = body.rstrip() + STUB_CHECKLIST
        changed = True

    if changed:
        new_content = f"---\n{dump_fm(fm)}\n---\n{body}"
        path.write_text(new_content, encoding="utf-8")
    return changed


def main() -> int:
    n = 0
    for path in sorted(SKILLS.rglob("SKILL.md")):
        if normalize_file(path):
            print(path.relative_to(ROOT))
            n += 1
    print(f"normalized {n} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
