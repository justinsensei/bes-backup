#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import subprocess
import re

def get_env_vars():
    env = {}
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    parts = line.split("=", 1)
                    env[parts[0].strip()] = parts[1].strip()
    return env

ENV = get_env_vars()

def get_todoist_loops():
    loops = []
    token = ENV.get("TODOIST_API_KEY")
    if not token:
        return ["Todoist: TODOIST_API_KEY not found in .env"]
    
    url = "https://api.todoist.com/api/v1/sync"
    data = urllib.parse.urlencode({
        "resource_types": json.dumps(["items"]),
        "sync_token": "*"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            res_data = json.loads(r.read().decode("utf-8"))
        items = res_data.get("items", [])
        today_str = datetime.now().strftime("%Y-%m-%d")
        for item in items:
            if not item.get("checked") and not item.get("is_deleted"):
                due = item.get("due")
                if due:
                    due_date = due.get("date")
                    if due_date and due_date <= today_str:
                        due_label = "overdue" if due_date < today_str else "today"
                        loops.append(f"Todoist ({due_label}): {item["content"]}")
    except Exception as e:
        loops.append(f"Todoist Error: {e}")
    return loops

def get_linear_loops():
    loops = []
    token = ENV.get("LINEAR_API_KEY")
    if not token:
        return ["Linear: LINEAR_API_KEY not found in .env"]
        
    query = """
    {
      viewer {
        assignedIssues(filter: { state: { type: { neq: "completed" } } }) {
          nodes {
            identifier
            title
            state {
              name
              type
            }
          }
        }
      }
    }
    """
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        headers={"Authorization": token, "Content-Type": "application/json"},
        data=json.dumps({"query": query}).encode("utf-8")
    )
    try:
        with urllib.request.urlopen(req) as r:
            res_data = json.loads(r.read().decode("utf-8"))
        nodes = res_data.get("data", {}).get("viewer", {}).get("assignedIssues", {}).get("nodes", [])
        for node in nodes:
            state_type = node.get("state", {}).get("type", "")
            state_name = node.get("state", {}).get("name", "")
            if state_type not in ["completed", "canceled"] and state_name not in ["Completed", "Done", "Canceled", "Cancelled"]:
                loops.append(f"Linear [{node["identifier"]} - {state_name}]: {node["title"]}")
    except Exception as e:
        loops.append(f"Linear Error: {e}")
    return loops

def get_vault_loops():
    loops = []
    vault_path = os.path.expanduser("~/vault")
    if not os.path.exists(vault_path):
        return []
        
    try:
        cmd = f"find {vault_path}/Notes {vault_path}/inbox -type f -name '*.md' -mtime -3 2>/dev/null"
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = p.communicate()
        files = out.decode("utf-8").splitlines()
        
        for filepath in files:
            if not os.path.exists(filepath):
                continue
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", errors="ignore") as f:
                    in_loops_section = False
                    for line in f:
                        line_stripped = line.strip()
                        if line_stripped.lower() == "## open loops":
                            in_loops_section = True
                            continue
                        elif line_stripped.startswith("##"):
                            in_loops_section = False
                            
                        if in_loops_section and line_stripped.startswith("- "):
                            val = line_stripped[2:].strip()
                            if val and val != "-":
                                loops.append(f"Vault Loop ({filename}): {val}")
                        elif "TODO" in line_stripped and not line_stripped.startswith("#") and ("[ ]" in line_stripped or "TODO" in line_stripped):
                            match = re.search(r"TODO:?\s*(.*)", line_stripped, re.IGNORECASE)
                            if match:
                                loops.append(f"Vault TODO ({filename}): {match.group(1).strip()}")
                            elif "[ ]" in line_stripped:
                                idx = line_stripped.find("[ ]")
                                loops.append(f"Vault TODO ({filename}): {line_stripped[idx+3:].strip()}")
            except Exception:
                pass
    except Exception as e:
        loops.append(f"Vault Error: {e}")
    return loops

def get_calendar_loops():
    loops = []
    gws_script = os.path.expanduser("~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py")
    if not os.path.exists(gws_script):
        return []
        
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    
    cmd = f"python3 {gws_script} --account all calendar list --start {start_date}T00:00:00 --end {end_date}T23:59:59 --max 20"
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = p.communicate()
        out_str = out.decode("utf-8").strip()
        if out_str.startswith("["):
            events = json.loads(out_str)
            for event in events:
                summary = event.get("summary", "")
                if summary.lower() not in ["jamie music", "sam drums", "home", "dog meds"]:
                    loops.append(f"Calendar (Prepare for): {summary} ({event.get('start', )})")
    except Exception as e:
        loops.append(f"Calendar Error: {e}")
    return loops

def get_comms_loops():
    loops = []
    src_script = os.path.expanduser("~/.hermes/scripts/fetch_source_candidates.py")
    if not os.path.exists(src_script):
        return []
        
    cmd = f"python3 {src_script}"
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = p.communicate()
        out_str = out.decode("utf-8").strip()
        if out_str.startswith("{"):
            data = json.loads(out_str)
            for email in data.get("email", []):
                loops.append(f"Email Candidate: {email.get('subject')} (from {email.get('participants', [os.getenv('USER')])[0]})")
            for msg in data.get("slack", []):
                loops.append(f"Slack Candidate: {msg.get('channel')} - {msg.get('preview')}")
    except Exception:
        pass
    return loops

def main():
    print("Gathering open loops from your digital workspace...")
    
    todoist = get_todoist_loops()
    linear = get_linear_loops()
    vault = get_vault_loops()
    calendar = get_calendar_loops()
    comms = get_comms_loops()
    
    all_loops = []
    
    if todoist:
        print("\n📋 **Todoist Tasks (Today/Overdue)**")
        for loop in todoist:
            print(f"- {loop}")
            all_loops.append(loop)
            
    if linear:
        print("\n🚀 **Linear Assigned Issues**")
        for loop in linear:
            print(f"- {loop}")
            all_loops.append(loop)
            
    if vault:
        print("\n📁 **Vault Open Loops & TODOs**")
        for loop in vault:
            print(f"- {loop}")
            all_loops.append(loop)
            
    if calendar:
        print("\n📅 **Upcoming Calendar Events**")
        for loop in calendar:
            print(f"- {loop}")
            all_loops.append(loop)
            
    if comms:
        print("\n✉️ **Communications Candidates (Unsaved)**")
        for loop in comms:
            print(f"- {loop}")
            all_loops.append(loop)
            
    if not all_loops:
        print("\n🎉 No open loops found!")

if __name__ == "__main__":
    main()
