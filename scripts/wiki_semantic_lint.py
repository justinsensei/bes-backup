#!/usr/bin/env python3
"""
wiki_semantic_lint.py — Tier-3 semantic vault lint (report-only).

Deterministic checks: maturity orphans, stale Source summaries, Reading promotion
gaps, missing Concept→Source link chains, and contradiction review candidates
(Beliefs/Thoughts vs recent Decisions/Meetings with shared wikilink overlap).

Structural checks remain in vault_hygiene.py (obsidian-hygiene).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/home/justin.guest/Developer/obsidian-vault"))
STATE_PATH = Path(os.path.expanduser("~/.hermes/state/semantic_lint_last.json"))

SKIP_DIRS = {
    "Readwise",
    "Utilities",
    ".git",
    ".trash",
    ".cursor",
    ".claude",
    "Templates",
    "meetings",
}

MATURITY_CATEGORIES = {
    "Notes",
    "Thoughts",
    "Concepts",
    "Beliefs",
    "References",
    "Decisions",
    "Memories",
    "Projects",
    "Sources",
}

ORPHAN_EXCLUDE_PREFIXES = (
    "inbox/",
    "Inputs/",
    "Logs/",
    "Daily Notes/",
    "Contacts/",
    "Notes/Daily Notes/",
    "Notes/Contacts/",
    "Readwise/",
    "meetings/",
    "Utilities/",
)

BELIEF_THOUGHT_CATEGORIES = {"Beliefs", "Thoughts"}
RECENT_DECISION_CATEGORIES = {"Decisions", "Meetings", "Slack"}
RECENT_DAYS_DEFAULT = 30
READING_BODY_MIN_CHARS = 400


def parse_category(fm_raw: str) -> str:
    m = re.search(r'^category:\s*["\']?\[\[([^\]]+)\]\]["\']?', fm_raw, re.MULTILINE)
    return m.group(1).strip() if m else ""


def parse_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end < 0:
        return "", text
    return text[3:end], text[end + 4 :]


def normalize_link_target(link: str) -> str:
    target = link.split("|")[0].strip()
    return target.split("#")[0].strip()


def resolve_wikilink(file_target: str, existing_rel_paths: dict, existing_basenames: dict) -> str | None:
    norm = file_target.replace("\\", "/").lower().strip()
    if not norm:
        return None
    if norm in existing_rel_paths:
        return existing_rel_paths[norm]
    if (norm + ".md") in existing_rel_paths:
        return existing_rel_paths[norm + ".md"]
    if norm in existing_basenames:
        return existing_basenames[norm][0]
    if (norm + ".md") in existing_basenames:
        return existing_basenames[norm + ".md"][0]
    return None


def resolve_reading_wikilink(
    file_target: str, existing_rel_paths: dict, existing_basenames: dict
) -> str | None:
    """Resolve a wikilink preferring Inputs/Readings paths over same-titled Sources."""
    norm = file_target.replace("\\", "/").lower().strip()
    if not norm:
        return None
    if norm in existing_rel_paths:
        candidate = existing_rel_paths[norm]
        return candidate if is_reading_path(candidate) else None
    if (norm + ".md") in existing_rel_paths:
        candidate = existing_rel_paths[norm + ".md"]
        return candidate if is_reading_path(candidate) else None

    candidates: list[str] = []
    if norm in existing_basenames:
        candidates = existing_basenames[norm]
    elif (norm + ".md") in existing_basenames:
        candidates = existing_basenames[norm + ".md"]

    reading_matches = [c for c in candidates if is_reading_path(c)]
    if reading_matches:
        return reading_matches[0]
    return None


def build_catalog(vault: Path) -> tuple[dict, dict]:
    existing_rel_paths: dict[str, str] = {}
    existing_basenames: dict[str, list[str]] = defaultdict(list)
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        for d in dirs:
            rel = Path(root, d).relative_to(vault)
            rel_str = str(rel).replace("\\", "/")
            existing_rel_paths[rel_str.lower()] = rel_str
        for f in files:
            full = Path(root) / f
            rel = full.relative_to(vault)
            rel_str = str(rel).replace("\\", "/")
            existing_rel_paths[rel_str.lower()] = rel_str
            lower = f.lower()
            existing_basenames[lower].append(rel_str)
            if lower.endswith(".md"):
                existing_basenames[lower[:-3]].append(rel_str)
    return existing_rel_paths, existing_basenames


def walk_notes(vault: Path):
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith(".md") or f == "RESOLVER.md":
                continue
            path = Path(root) / f
            rel = str(path.relative_to(vault)).replace("\\", "/")
            text = path.read_text(encoding="utf-8", errors="replace")
            fm_raw, body = parse_frontmatter(text)
            category = parse_category(fm_raw) if fm_raw else ""
            yield path, rel, text, fm_raw, body, category


def build_graph(vault: Path):
    existing_rel_paths, existing_basenames = build_catalog(vault)
    incoming: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, set[str]] = defaultdict(set)
    notes: dict[str, dict] = {}

    for path, rel, text, fm_raw, body, category in walk_notes(vault):
        notes[rel] = {
            "path": rel,
            "category": category,
            "mtime": path.stat().st_mtime,
            "body": body,
            "text": text,
        }
        for link in re.findall(r"\[\[([^\]]+)\]\]", text):
            file_target = normalize_link_target(link)
            if not file_target:
                continue
            resolved = resolve_wikilink(file_target, existing_rel_paths, existing_basenames)
            if resolved:
                outgoing[rel].add(resolved)
                incoming[resolved].add(rel)

    return notes, incoming, outgoing, existing_rel_paths, existing_basenames


def is_reading_path(rel: str) -> bool:
    return rel.startswith(("Inputs/Readings/", "Logs/Readings/", "Logs/Sources/"))


def parse_log_activity(vault: Path, since: datetime) -> list[str]:
    log_path = vault / "Utilities" / "log.md"
    if not log_path.exists():
        return []
    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines: list[str] = []
    current_date: datetime | None = None
    for line in text.splitlines():
        heading = re.match(r"^## (\d{4}-\d{2}-\d{2})\s*$", line.strip())
        if heading:
            try:
                current_date = datetime.strptime(heading.group(1), "%Y-%m-%d")
            except ValueError:
                current_date = None
            continue
        if not line.strip().startswith("- ") or current_date is None:
            continue
        if current_date >= since:
            lines.append(line.strip()[2:])
    return lines


def extract_section_links(text: str, heading: str) -> list[str]:
    m = re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return []
    section = text[m.end() :]
    next_h = re.search(r"^## ", section, re.MULTILINE)
    if next_h:
        section = section[: next_h.start()]
    return [normalize_link_target(x) for x in re.findall(r"\[\[([^\]]+)\]\]", section)]


def source_reading_map(
    notes: dict,
    existing_rel_paths: dict,
    existing_basenames: dict,
) -> dict[str, str]:
    """Map reading rel path (lowercase) -> source rel path."""
    mapping: dict[str, str] = {}
    for rel, meta in notes.items():
        if meta["category"] != "Sources":
            continue
        for target in extract_section_links(meta["text"], "## Raw inputs"):
            resolved = resolve_reading_wikilink(target, existing_rel_paths, existing_basenames)
            if resolved:
                mapping[resolved.lower()] = rel
    return mapping


def reading_has_substance(body: str) -> bool:
    if len(body.strip()) >= READING_BODY_MIN_CHARS:
        return True
    return bool(re.search(r"^##\s+Highlights\s*$", body, re.MULTILINE | re.IGNORECASE))


def note_age_days(mtime: float, now: float) -> int:
    return int((now - mtime) / 86400)


def format_date(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def run_lint(
    vault: Path | None = None,
    recent_days: int = RECENT_DAYS_DEFAULT,
    since_last: bool = True,
) -> dict:
    vault = vault or VAULT
    now = datetime.now()
    now_ts = now.timestamp()

    last_run: datetime | None = None
    if since_last and STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            last_run = datetime.fromisoformat(data["run_at"])
        except Exception:
            last_run = None

    activity_since = last_run or (now - timedelta(days=recent_days))
    log_lines = parse_log_activity(vault, activity_since)

    notes, incoming, outgoing, existing_rel_paths, existing_basenames = build_graph(vault)
    reading_to_source = source_reading_map(notes, existing_rel_paths, existing_basenames)

    findings: dict[str, list] = {
        "maturity_orphans": [],
        "stale_summaries": [],
        "promotion_opportunities": [],
        "missing_link_chains": [],
        "contradiction_candidates": [],
    }

    for rel, meta in notes.items():
        if meta["category"] not in MATURITY_CATEGORIES:
            continue
        if not rel.startswith("Notes/"):
            continue
        if any(rel.startswith(p) for p in ORPHAN_EXCLUDE_PREFIXES):
            continue
        if len(incoming.get(rel, set())) == 0:
            findings["maturity_orphans"].append(
                {
                    "path": rel,
                    "category": meta["category"],
                    "outgoing": len(outgoing.get(rel, set())),
                }
            )

    for rel, meta in notes.items():
        if meta["category"] != "Sources":
            continue
        for target in extract_section_links(meta["text"], "## Raw inputs"):
            resolved = resolve_reading_wikilink(target, existing_rel_paths, existing_basenames)
            if not resolved:
                continue
            reading_mtime = notes[resolved]["mtime"]
            if reading_mtime > meta["mtime"]:
                findings["stale_summaries"].append(
                    {
                        "source": rel,
                        "reading": resolved,
                        "reading_updated": format_date(reading_mtime),
                        "summary_updated": format_date(meta["mtime"]),
                    }
                )

    for rel, meta in notes.items():
        if not is_reading_path(rel):
            continue
        if meta["category"] not in ("Readings", ""):
            continue
        if rel.lower() in reading_to_source:
            continue
        if not reading_has_substance(meta["body"]):
            continue
        findings["promotion_opportunities"].append({"reading": rel})

    concept_categories = {"Concepts", "Beliefs", "Thoughts", "References"}
    for rel, meta in notes.items():
        if meta["category"] not in concept_categories:
            continue
        for link in re.findall(r"\[\[([^\]]+)\]\]", meta["text"]):
            target = normalize_link_target(link)
            resolved = resolve_reading_wikilink(target, existing_rel_paths, existing_basenames)
            if not resolved:
                continue
            source = reading_to_source.get(resolved.lower())
            if source:
                findings["missing_link_chains"].append(
                    {
                        "note": rel,
                        "category": meta["category"],
                        "reading": resolved,
                        "source": source,
                    }
                )

    belief_thought: list[tuple[str, set[str]]] = []
    recent_items: list[tuple[str, set[str], str]] = []
    cutoff = now_ts - recent_days * 86400

    for rel, meta in notes.items():
        links = {normalize_link_target(x).lower() for x in re.findall(r"\[\[([^\]]+)\]\]", meta["text"])}
        links = {x for x in links if x}
        if meta["category"] in BELIEF_THOUGHT_CATEGORIES and rel.startswith("Notes/"):
            belief_thought.append((rel, links))
        if meta["category"] in RECENT_DECISION_CATEGORIES and meta["mtime"] >= cutoff:
            recent_items.append((rel, links, meta["category"]))

    for bt_rel, bt_links in belief_thought:
        for recent_rel, recent_links, recent_cat in recent_items:
            overlap = bt_links & recent_links
            overlap = {x for x in overlap if len(x) > 2}
            if len(overlap) >= 1:
                findings["contradiction_candidates"].append(
                    {
                        "belief_or_thought": bt_rel,
                        "recent_note": recent_rel,
                        "recent_category": recent_cat,
                        "shared_links": sorted(overlap)[:5],
                    }
                )

    issue_count = sum(len(v) for v in findings.values())
    tier3_issues = issues_to_strings(findings)

    return {
        "run_at": now.isoformat(),
        "vault": str(vault),
        "activity_since": activity_since.isoformat(),
        "log_lines_since_last": len(log_lines),
        "recent_log_sample": log_lines[-10:],
        "findings": findings,
        "issue_count": issue_count,
        "tier3_issues": tier3_issues,
    }


def issues_to_strings(findings: dict) -> list[str]:
    lines: list[str] = []
    for item in findings.get("maturity_orphans", [])[:15]:
        lines.append(f"{item['path']} — maturity orphan ({item['category']}, {item['outgoing']} outbound)")
    for item in findings.get("stale_summaries", [])[:15]:
        lines.append(
            f"{item['source']} — summary stale (reading updated {item['reading_updated']})"
        )
    for item in findings.get("promotion_opportunities", [])[:15]:
        lines.append(f"{item['reading']} — no compiled Source yet")
    for item in findings.get("missing_link_chains", [])[:15]:
        lines.append(
            f"{item['note']} — links Reading directly; use [[{Path(item['source']).stem if item.get('source') else 'Source'}]]"
        )
    for item in findings.get("contradiction_candidates", [])[:10]:
        shared = ", ".join(item["shared_links"][:3])
        lines.append(
            f"{item['belief_or_thought']} vs {item['recent_note']} — review ({shared})"
        )
    return lines


def format_markdown_report(result: dict) -> str:
    run_date = result["run_at"][:10]
    lines = [f"## Wiki semantic lint — {run_date}", ""]
    if result.get("log_lines_since_last"):
        lines.append(f"*Scoped using {result['log_lines_since_last']} log.md entries since {result['activity_since'][:10]}.*")
        lines.append("")

    sections = [
        ("maturity_orphans", "### Maturity orphans (no inbound links)", lambda i: f"- `{i['path']}` ({i['category']})"),
        (
            "stale_summaries",
            "### Stale summaries",
            lambda i: f"- [[{Path(i['source']).stem}]]: reading updated {i['reading_updated']}, summary {i['summary_updated']}",
        ),
        (
            "promotion_opportunities",
            "### Promotion opportunities",
            lambda i: f"- [[{Path(i['reading']).stem}]]: no compiled Source yet",
        ),
        (
            "missing_link_chains",
            "### Missing link chains",
            lambda i: f"- `{i['note']}` → Reading `{i['reading']}` (Source: `{i.get('source', 'unknown')}`)",
        ),
        (
            "contradiction_candidates",
            "### Contradiction review candidates",
            lambda i: f"- `{i['belief_or_thought']}` vs `{i['recent_note']}` — shared: {', '.join(i['shared_links'])}",
        ),
    ]

    any_section = False
    for key, heading, fmt in sections:
        items = result["findings"].get(key, [])
        if not items:
            continue
        any_section = True
        lines.append(heading)
        for item in items:
            lines.append(fmt(item))
        lines.append("")

    if not any_section:
        lines.append("No tier-3 semantic issues found.")
        lines.append("")

    lines.append("---")
    lines.append("*Report-only. Resolve via integrate-full or manual edits. Structural issues → vault_hygiene.py.*")
    return "\n".join(lines)


def write_report(vault: Path, result: dict) -> Path:
    reports_dir = vault / "Utilities" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    run_date = result["run_at"][:10]
    report_path = reports_dir / f"semantic-lint-{run_date}.md"
    report_path.write_text(format_markdown_report(result) + "\n", encoding="utf-8")
    return report_path


def write_state(result: dict, report_rel: str) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_at": result["run_at"],
        "issue_count": result["issue_count"],
        "report_path": report_rel,
        "tier3_issues": result["tier3_issues"],
        "surfaced": False,
    }
    STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def append_log_line(vault: Path, run_date: str, issue_count: int, report_rel: str) -> None:
    log_path = vault / "Utilities" / "log.md"
    if not log_path.exists():
        return
    text = log_path.read_text(encoding="utf-8", errors="replace")
    section = f"## {run_date}"
    entry = f"- 08:00 | lint | [[semantic-lint-{run_date}]] | {report_rel} | tier-3 ({issue_count} issues)"
    if section in text:
        text = text.rstrip() + f"\n{entry}\n"
    else:
        text = text.rstrip() + f"\n\n{section}\n{entry}\n"
    log_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Tier-3 semantic vault lint (report-only)")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--no-state", action="store_true", help="Do not write state file")
    parser.add_argument("--no-report", action="store_true", help="Do not write vault report")
    parser.add_argument("--no-log", action="store_true", help="Do not append Utilities/log.md")
    parser.add_argument("--recent-days", type=int, default=RECENT_DAYS_DEFAULT)
    parser.add_argument("--vault", type=str, default=None)
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else VAULT
    if not vault.exists():
        print(f"Vault not found: {vault}", file=os.sys.stderr)
        return 1

    result = run_lint(vault=vault, recent_days=args.recent_days)
    report_rel = ""

    if not args.no_report:
        report_path = write_report(vault, result)
        report_rel = str(report_path.relative_to(vault)).replace("\\", "/")
        result["report_path"] = report_rel

    if not args.no_state and report_rel:
        write_state(result, report_rel)

    if not args.no_log and report_rel:
        append_log_line(vault, result["run_at"][:10], result["issue_count"], report_rel)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_markdown_report(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
