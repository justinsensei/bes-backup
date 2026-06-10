#!/usr/bin/env python3
"""
vault_hygiene_cron.py — Cron wrapper for vault_hygiene.py.

Runs the hygiene script and prints output when there are red-level issues
or taxonomy-relevant warnings. Auto-fixes run silently unless surfaced below.

Empty stdout → no Telegram message (watchdog pattern).
"""

import subprocess
import sys
import os

script = os.path.join(os.path.dirname(__file__), "vault_hygiene.py")

result = subprocess.run(
    [sys.executable, script],
    capture_output=True,
    text=True,
)

output = result.stdout.strip()

ALERT_MARKERS = [
    "## 🔴 ID conflicts",
    "## 🔴 Non-unique aliases",
    "## 🔴 Missing ID",
    "## 🔴 Missing daily_note",
    "## 🔴 Wrong folder",
    "## ⚠️  Move conflicts",
    "## ⚠️ Ghost Links",
    "## ⚠️ Orphan Notes",
    "## ⚠️ Source linkage",
    "## ⚠️ Citation & Reading URL Issues",
    "## ⚠️ Legacy path links",
]

alert_lines = []
in_alert_section = False

for line in output.splitlines():
    is_header = any(line.startswith(m) for m in ALERT_MARKERS)
    is_any_section = line.startswith("## ")

    if is_header:
        in_alert_section = True
        alert_lines.append(line)
    elif in_alert_section:
        if is_any_section and not is_header:
            in_alert_section = False
        else:
            alert_lines.append(line)

if alert_lines:
    print("**Vault hygiene issues found:**\n")
    print("\n".join(alert_lines))
