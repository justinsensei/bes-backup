#!/usr/bin/env python3
"""
vault_hygiene_cron.py — Cron wrapper for vault_hygiene.py.

Runs the hygiene script and prints output ONLY if there are red-level issues
(ID conflicts, missing IDs, missing daily_note links). Auto-fixes (misplaced
daily notes, tag conversions) run silently.

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

# Only surface red-level sections
RED_MARKERS = [
    "## 🔴 ID conflicts",
    "## 🔴 Missing ID",
    "## 🔴 Missing daily_note",
    "## ⚠️  Move conflicts",
]

red_lines = []
in_red_section = False

for line in output.splitlines():
    is_header = any(line.startswith(m) for m in RED_MARKERS)
    is_green  = line.startswith("## ✅")
    is_any_section = line.startswith("## ")

    if is_header:
        in_red_section = True
        red_lines.append(line)
    elif in_red_section:
        if is_any_section and not is_header:
            in_red_section = False
        else:
            red_lines.append(line)

if red_lines:
    print("**Vault hygiene issues found:**\n")
    print("\n".join(red_lines))
# else: silent — no message sent
