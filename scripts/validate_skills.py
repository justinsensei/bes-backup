#!/usr/bin/env python3
"""Validate Bes SKILL.md files in the bes-backup repo."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

MAX_DESCRIPTION = 1024
MAX_SKILL_CHARS = 100_000
MAX_NAME = 64

TIRITH_PATTERNS = [
    (re.compile(r"\|\s*python3\s+-c\b"), "pipe_to_interpreter: | python3 -c"),
    (re.compile(r"\|\s*bash\b"), "pipe_to_interpreter: | bash"),
    (re.compile(r"\|\s*node\s+-e\b"), "pipe_to_interpreter: | node -e"),
    (re.compile(r"curl\s+[^\n|]+\|\s*sh\b"), "unverified_download: curl | sh"),
]

HARDCODED_VM = re.compile(r"/home/justin\.guest/")
ENV_NEARBY = re.compile(
    r"OBSIDIAN_VAULT_PATH|HERMES_HOME|\$\{HERMES_HOME|\$\{OBSIDIAN_VAULT_PATH|\$VAULT|\$HERMES"
)


@dataclass
class Issue:
    severity: str  # error, warn, info
    skill: str
    message: str
    path: str = ""


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def add(self, severity: str, skill: str, message: str, path: str = "") -> None:
        self.issues.append(Issue(severity, skill, message, path))

    def counts(self) -> dict[str, int]:
        c = {"error": 0, "warn": 0, "info": 0}
        for i in self.issues:
            c[i.severity] = c.get(i.severity, 0) + 1
        return c


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_skill_files(root: Path) -> list[Path]:
    return sorted((root / "skills").rglob("SKILL.md"))


def parse_frontmatter(content: str) -> tuple[dict | None, str | None]:
    if not content.startswith("---"):
        return None, "must start with ---"
    end = content.find("\n---", 3)
    if end == -1:
        return None, "missing closing ---"
    body_start = end + 4
    if body_start < len(content) and content[body_start] == "\n":
        body_start += 1
    raw = content[3:end]
    if yaml is None:
        return None, "PyYAML not installed"
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    if not isinstance(data, dict):
        return None, "frontmatter must be a mapping"
    if not content[body_start:].strip():
        return None, "empty body after frontmatter"
    return data, None


def collect_script_basenames(root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    repo_scripts: dict[str, Path] = {}
    skill_scripts: dict[str, Path] = {}
    scripts_dir = root / "scripts"
    if scripts_dir.is_dir():
        for p in scripts_dir.iterdir():
            if p.is_file():
                repo_scripts[p.name] = p
    for p in (root / "skills").rglob("scripts/*"):
        if p.is_file():
            skill_scripts[p.name] = p
    return repo_scripts, skill_scripts


def skill_names_from_files(files: list[Path]) -> dict[str, Path]:
    names: dict[str, Path] = {}
    for path in files:
        content = path.read_text(encoding="utf-8", errors="replace")
        fm, err = parse_frontmatter(content)
        if err or not fm:
            continue
        name = fm.get("name")
        if isinstance(name, str):
            names[name] = path
    return names


def validate_skill(
    path: Path,
    content: str,
    fm: dict,
    all_names: dict[str, Path],
    deprecated: set[str],
    report: Report,
) -> None:
    skill = fm.get("name", path.parent.name)
    spath = str(path.relative_to(repo_root()))

    if "name" not in fm:
        report.add("error", skill, "missing name", spath)
    elif not isinstance(fm["name"], str):
        report.add("error", skill, "name must be string", spath)
    elif len(fm["name"]) > MAX_NAME:
        report.add("error", skill, f"name exceeds {MAX_NAME} chars", spath)
    elif fm["name"] in all_names and all_names[fm["name"]] != path:
        report.add("error", skill, f"duplicate name: {fm['name']}", spath)

    desc = fm.get("description")
    if not desc:
        report.add("error", skill, "missing description", spath)
    elif not isinstance(desc, str):
        report.add("error", skill, "description must be string", spath)
    else:
        if len(desc) > MAX_DESCRIPTION:
            report.add("error", skill, f"description exceeds {MAX_DESCRIPTION} chars", spath)
        if not desc.startswith("Use when"):
            report.add("warn", skill, 'description should start with "Use when"', spath)

    if len(content) > MAX_SKILL_CHARS:
        report.add("error", skill, f"file exceeds {MAX_SKILL_CHARS} chars", spath)

    if "related_skills" in fm and "metadata" not in fm:
        report.add("error", skill, "related_skills at YAML root — move to metadata.hermes", spath)

    meta = fm.get("metadata") or {}
    hermes = meta.get("hermes") or {} if isinstance(meta, dict) else {}
    related = hermes.get("related_skills") or []
    external = set(hermes.get("external_related_skills") or [])

    if isinstance(related, list):
        for ref in related:
            if not isinstance(ref, str):
                continue
            if ref not in all_names and ref not in external:
                report.add("error", skill, f"related_skills unresolved: {ref}", spath)
            if ref in deprecated:
                report.add("warn", skill, f"related_skills references deprecated skill: {ref}", spath)

    for field in ("version", "author", "license"):
        if field not in fm:
            report.add("warn", skill, f"missing recommended field: {field}", spath)

    if not hermes.get("tags"):
        report.add("warn", skill, "missing metadata.hermes.tags", spath)

    tirith_doc = re.compile(r"(?i)(do not|not pipe|,\s*not\s*`|avoid|forbid|never|banned|unsafe|instead of)")
    for pattern, label in TIRITH_PATTERNS:
        for line in content.splitlines():
            if pattern.search(line) and not tirith_doc.search(line):
                report.add("warn", skill, f"Tirith-banned pattern: {label}", spath)
                break

    for i, line in enumerate(content.splitlines(), 1):
        if HARDCODED_VM.search(line):
            if ENV_NEARBY.search(line):
                continue
            window = "\n".join(content.splitlines()[max(0, i - 3) : i + 2])
            if not ENV_NEARBY.search(window):
                report.add("warn", skill, f"hardcoded VM path without env var nearby (line {i})", spath)

    body = content.split("---", 2)[-1] if content.count("---") >= 2 else content
    if "# " in body and not re.search(r"^## Common Pitfalls", body, re.MULTILINE):
        report.add("warn", skill, "missing ## Common Pitfalls section", spath)
    if "# " in body and not re.search(r"^## Verification Checklist", body, re.MULTILINE):
        report.add("warn", skill, "missing ## Verification Checklist section", spath)


def check_script_duplicates(root: Path, report: Report) -> None:
    repo_scripts, skill_scripts = collect_script_basenames(root)
    overlap = set(repo_scripts) & set(skill_scripts)
    for name in sorted(overlap):
        report.add(
            "error",
            "(scripts)",
            f"duplicate script basename: {name} in scripts/ and {skill_scripts[name].relative_to(root)}",
            str(skill_scripts[name]),
        )


def check_bundled_manifest(root: Path, all_names: dict[str, Path], report: Report) -> None:
    manifest = root / "skills" / ".bundled_manifest"
    if not manifest.is_file():
        return
    for line in manifest.read_text().splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        name = line.split(":", 1)[0].strip()
        if name not in all_names:
            report.add("info", name, "in .bundled_manifest but no local SKILL.md")


def emit_index(root: Path, files: list[Path]) -> None:
    rows = []
    for path in files:
        content = path.read_text(encoding="utf-8", errors="replace")
        fm, err = parse_frontmatter(content)
        if err or not fm:
            continue
        meta = (fm.get("metadata") or {}).get("hermes") or {}
        cat = path.relative_to(root / "skills").parts[0]
        rows.append(
            (
                fm.get("name", "?"),
                cat,
                "yes" if meta.get("deprecated") else "",
                len(meta.get("related_skills") or []),
            )
        )
    lines = [
        "# Skills Index",
        "",
        "Auto-generated by `python3 scripts/validate_skills.py --index`. Do not edit by hand.",
        "",
        "| name | category | deprecated | related_skills |",
        "| --- | --- | --- | --- |",
    ]
    for name, cat, dep, rc in sorted(rows):
        lines.append(f"| {name} | {cat} | {dep} | {rc} |")
    (root / "skills" / "SKILLS-INDEX.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Bes SKILL.md files")
    parser.add_argument("--skill", help="Validate single skill by name")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--index", action="store_true", help="Emit skills/SKILLS-INDEX.md")
    args = parser.parse_args()

    root = repo_root()
    files = find_skill_files(root)
    report = Report()

    if yaml is None:
        print("error: PyYAML required (pip install pyyaml)", file=sys.stderr)
        return 2

    # First pass: collect names
    parsed: list[tuple[Path, str, dict | None, str | None]] = []
    all_names: dict[str, Path] = {}
    for path in files:
        content = path.read_text(encoding="utf-8", errors="replace")
        fm, err = parse_frontmatter(content)
        parsed.append((path, content, fm, err))
        if fm and isinstance(fm.get("name"), str):
            all_names[fm["name"]] = path

    deprecated: set[str] = set()
    for path, content, fm, err in parsed:
        if not fm:
            continue
        meta = (fm.get("metadata") or {}).get("hermes") or {}
        if meta.get("deprecated"):
            deprecated.add(fm.get("name", ""))

    check_script_duplicates(root, report)

    for path, content, fm, err in parsed:
        skill_label = path.parent.name
        spath = str(path.relative_to(root))
        if err:
            report.add("error", skill_label, f"frontmatter: {err}", spath)
            continue
        if args.skill and fm.get("name") != args.skill:
            continue
        validate_skill(path, content, fm, all_names, deprecated, report)

    check_bundled_manifest(root, all_names, report)

    if args.index:
        emit_index(root, files)

    for issue in report.issues:
        loc = f" ({issue.path})" if issue.path else ""
        print(f"{issue.severity}: [{issue.skill}]{loc} {issue.message}")

    counts = report.counts()
    print(
        f"\n{counts.get('error', 0)} errors, {counts.get('warn', 0)} warnings, {counts.get('info', 0)} info",
        file=sys.stderr,
    )

    if counts.get("error", 0):
        return 1
    if args.strict and counts.get("warn", 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
