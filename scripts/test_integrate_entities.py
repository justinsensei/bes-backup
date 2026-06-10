#!/usr/bin/env python3
"""Tests for integrate_entities.py and vault_entities.py."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import vault_entities as ve
from integrate_entities import append_meeting_related, integrate_ingest, section_exists_with_link
from vault_entities import load_channel_map, match_contacts, match_projects


class IntegrateEntitiesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = self.tmp.name
        self.state_dir = os.path.join(self.tmp.name, "state")
        os.makedirs(self.state_dir, exist_ok=True)
        self.channel_map_path = os.path.join(self.state_dir, "channel-project-map.json")
        self.unmatched_path = os.path.join(self.state_dir, "integrate_entities_unmatched.json")
        with open(self.channel_map_path, "w", encoding="utf-8") as f:
            json.dump({"product-leads": "K12 GTM"}, f)

        os.environ["CHANNEL_PROJECT_MAP_PATH"] = self.channel_map_path

        os.makedirs(os.path.join(self.vault, "Notes", "Projects"), exist_ok=True)
        os.makedirs(os.path.join(self.vault, "Contacts"), exist_ok=True)
        os.makedirs(os.path.join(self.vault, "inbox"), exist_ok=True)
        os.makedirs(os.path.join(self.vault, "Inputs", "Meetings"), exist_ok=True)

        Path(os.path.join(self.vault, "Notes", "Projects", "K12 GTM.md")).write_text(
            "> Executive summary: K12 go-to-market.\n\nStatus: Active\n\n## State\n\n## Timeline\n\n## Related inputs\n",
            encoding="utf-8",
        )
        Path(os.path.join(self.vault, "Contacts", "Endre.md")).write_text(
            "> Executive summary: Briefing for Endre.\n\n## State\n\n## Timeline\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("CHANNEL_PROJECT_MAP_PATH", None)

    def _integrate(self, rel_path, gist=None):
        return integrate_ingest(
            self.vault, rel_path, gist_override=gist, unmatched_path=self.unmatched_path
        )

    def test_slack_log_updates_project_and_contact(self):
        ingest = os.path.join(self.vault, "inbox", "2026-06-10 - Slack - K12 GTM sync.md")
        Path(ingest).write_text(
            """---
id: '20260610120000'
daily_note: "[[Daily Notes/2026-06-10 Tuesday|2026-06-10 Tuesday]]"
category: "[[Slack]]"
channel: "product-leads"
participants:
  - "Endre"
---
# Slack Thread: K12 GTM sync

Discussed K12 GTM rollout with Endre.
""",
            encoding="utf-8",
        )
        report = self._integrate("inbox/2026-06-10 - Slack - K12 GTM sync.md", "K12 GTM sync discussion")
        self.assertIn("K12 GTM", report["updated"]["projects"])
        self.assertIn("Endre", report["updated"]["contacts"])

        proj = Path(self.vault, "Notes", "Projects", "K12 GTM.md").read_text(encoding="utf-8")
        self.assertIn("## Related inputs", proj)
        self.assertIn("2026-06-10 | [[inbox/2026-06-10 - Slack - K12 GTM sync|", proj)

        contact = Path(self.vault, "Contacts", "Endre.md").read_text(encoding="utf-8")
        self.assertIn("2026-06-10 | [[inbox/2026-06-10 - Slack - K12 GTM sync|", contact)

    def test_decision_updates_project_state(self):
        ingest = os.path.join(self.vault, "inbox", "2026-06-10 - Decision - K12 GTM.md")
        Path(ingest).write_text(
            """---
id: '20260610130000'
daily_note: "[[Daily Notes/2026-06-10 Tuesday|2026-06-10 Tuesday]]"
category: "[[Decisions]]"
channel: "product-leads"
---
# Decision: K12 GTM pricing

## Resolution
Ship tiered pricing for K12 districts in Q3.
""",
            encoding="utf-8",
        )
        report = self._integrate("inbox/2026-06-10 - Decision - K12 GTM.md")
        self.assertIn("K12 GTM", report["updated"]["projects"])

        proj = Path(self.vault, "Notes", "Projects", "K12 GTM.md").read_text(encoding="utf-8")
        self.assertIn("Decision —", proj)
        self.assertIn("Ship tiered pricing", proj)

    def test_meeting_related_and_fanout(self):
        body = "Discussed K12 GTM milestones.\n"
        related = append_meeting_related(body, "K12 GTM")
        self.assertIn("### Related", related)
        self.assertIn("[[K12 GTM]]", related)

        meeting = os.path.join(self.vault, "Inputs", "Meetings", "2026-06-10 - K12 GTM standup.md")
        Path(meeting).write_text(
            f"""---
id: '20260610140000'
daily_note: "[[Daily Notes/2026-06-10 Tuesday|2026-06-10 Tuesday]]"
category: "[[Meetings]]"
participants:
  - "Endre"
---
{related}""",
            encoding="utf-8",
        )
        report = self._integrate("Inputs/Meetings/2026-06-10 - K12 GTM standup.md", "K12 GTM standup")
        self.assertIn("K12 GTM", report["updated"]["projects"])

    def test_idempotency(self):
        ingest = os.path.join(self.vault, "inbox", "2026-06-10 - Slack - K12 GTM sync.md")
        Path(ingest).write_text(
            """---
id: '20260610120000'
daily_note: "[[Daily Notes/2026-06-10 Tuesday|2026-06-10 Tuesday]]"
category: "[[Slack]]"
channel: "product-leads"
participants:
  - "Endre"
---
# Slack Thread
K12 GTM discussion.
""",
            encoding="utf-8",
        )
        self._integrate("inbox/2026-06-10 - Slack - K12 GTM sync.md")
        proj_before = Path(self.vault, "Notes", "Projects", "K12 GTM.md").read_text(encoding="utf-8")
        report2 = self._integrate("inbox/2026-06-10 - Slack - K12 GTM sync.md")
        proj_after = Path(self.vault, "Notes", "Projects", "K12 GTM.md").read_text(encoding="utf-8")
        self.assertEqual(proj_before, proj_after)
        self.assertEqual(report2["updated"]["projects"], [])
        self.assertTrue(any("Timeline" in s for s in report2["skipped"]))

    def test_unknown_entities_no_create(self):
        ingest = os.path.join(self.vault, "inbox", "2026-06-10 - Slack - Unknown Topic.md")
        Path(ingest).write_text(
            """---
id: '20260610150000'
daily_note: "[[Daily Notes/2026-06-10 Tuesday|2026-06-10 Tuesday]]"
category: "[[Slack]]"
channel: "random-channel"
participants:
  - "Mystery Person"
---
# Slack Thread
Some unrelated topic.
""",
            encoding="utf-8",
        )
        before = set(os.listdir(os.path.join(self.vault, "Contacts")))
        report = self._integrate("inbox/2026-06-10 - Slack - Unknown Topic.md")
        after = set(os.listdir(os.path.join(self.vault, "Contacts")))
        self.assertEqual(before, after)
        self.assertEqual(report["updated"]["projects"], [])
        self.assertEqual(report["updated"]["contacts"], [])
        self.assertIn("Mystery Person", report["unmatched"]["contact_candidates"])

    def test_channel_map_resolves_project(self):
        entities = ve.get_existing_entities(self.vault)
        cmap = load_channel_map(self.channel_map_path)
        self.assertEqual(cmap.get("product-leads"), "K12 GTM")
        matched, _ = match_projects(
            "generic slack thread", entities, channel="product-leads", channel_map_path=self.channel_map_path
        )
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["title"], "K12 GTM")

    def test_single_project_match_sets_frontmatter(self):
        ingest = os.path.join(self.vault, "inbox", "2026-06-10 - Slack - K12 GTM sync.md")
        Path(ingest).write_text(
            """---
id: '20260610120000'
daily_note: "[[Daily Notes/2026-06-10 Tuesday|2026-06-10 Tuesday]]"
category: "[[Slack]]"
channel: "product-leads"
---
# Slack Thread
K12 GTM discussion.
""",
            encoding="utf-8",
        )
        self._integrate("inbox/2026-06-10 - Slack - K12 GTM sync.md")
        content = Path(ingest).read_text(encoding="utf-8")
        self.assertIn('project: "[[K12 GTM]]"', content)

    def test_section_exists_with_link(self):
        content = "## Timeline\n- 2026-06-10 | [[inbox/foo|Title]] — gist\n"
        self.assertTrue(section_exists_with_link(content, "## Timeline", "inbox/foo"))
        self.assertFalse(section_exists_with_link(content, "## Timeline", "inbox/bar"))

    def test_match_contacts_exact(self):
        entities = ve.get_existing_entities(self.vault)
        matched, unmatched = match_contacts(["Endre", "Nobody"], entities)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["title"], "Endre")
        self.assertEqual(unmatched, ["Nobody"])


if __name__ == "__main__":
    unittest.main()
