#!/usr/bin/env python3
import subprocess
import json
import sys
import os

HERMES_HOME = os.path.expanduser("~/.hermes")
VENV_PY = os.path.join(HERMES_HOME, "hermes-agent", "venv", "bin", "python3")
SCRIPTS_DIR = os.path.join(HERMES_HOME, "scripts")

def run_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    try:
        res = subprocess.run(
            [VENV_PY, script_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        if res.returncode != 0:
            sys.stderr.write(f"Error running {script_name} (rc={res.returncode}): {res.stderr}\n")
            return []
        
        out = res.stdout.strip()
        if not out:
            return []
        try:
            return json.loads(out)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error decoding JSON from {script_name}: {e}\nRaw output: {out}\n")
            return []
    except Exception as e:
        sys.stderr.write(f"Exception running {script_name}: {e}\n")
        return []

def main():
    # Fetch Slack brains
    slack_brains = run_script("fetch_slack_brains.py")
    
    # Fetch Linear brains
    linear_brains = run_script("fetch_linear_brains.py")
    
    # Fetch Telegram brains
    telegram_brains = run_script("fetch_telegram_brains.py")
    
    # Output unified dict
    unified = {
        "slack": slack_brains,
        "linear": linear_brains,
        "telegram": telegram_brains
    }
    print(json.dumps(unified, indent=2))

if __name__ == "__main__":
    main()
