import os
import json
import subprocess
import re
import urllib.request
from datetime import datetime, timedelta

def load_env():
    env = {}
    env_path = os.path.expanduser('~/.hermes/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#') and '=' in line:
                    k, v = line.strip().split('=', 1)
                    env[k.strip()] = v.strip()
    return env

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                return json.loads(res.stdout)
            except:
                return res.stdout
        else:
            return {"error": res.stderr}
    except Exception as e:
        return {"error": str(e)}

def get_target_date():
    # If TARGET_DATE is in env, use it; otherwise get from work_day.py
    target_date = os.environ.get('TARGET_DATE')
    if not target_date:
        res = subprocess.run(['python3.12', os.path.expanduser('~/.hermes/scripts/work_day.py'), 'logs_to_summarize'], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            target_date = res.stdout.strip().split('\n')[0]
        else:
            yesterday = datetime.now() - timedelta(days=1)
            target_date = yesterday.strftime('%Y-%m-%d')
    return target_date

def find_daily_note(vault_path, target_date):
    t_dt = datetime.strptime(target_date, '%Y-%m-%d')
    weekday = t_dt.strftime('%A').lower()
    
    # Format 1: Daily Notes/2026-06-04-thursday.md or daily/2026-06-04-thursday.md
    p1_new = os.path.join(vault_path, 'Notes', 'Daily Notes', f"{target_date}-{weekday}.md")
    if os.path.exists(p1_new):
        return p1_new
    p1 = os.path.join(vault_path, 'daily', f"{target_date}-{weekday}.md")
    if os.path.exists(p1):
        return p1
        
    # Format 2: YYYY-MM-DD dddd.md
    day_name_cap = t_dt.strftime('%A')
    p2 = os.path.join(vault_path, f"{target_date} {day_name_cap}.md")
    if os.path.exists(p2):
        return p2
        
    # Format 3: Daily Notes/YYYY-MM-DD dddd.md
    p3 = os.path.join(vault_path, 'Notes', 'Daily Notes', f"{target_date} {day_name_cap}.md")
    if os.path.exists(p3):
        return p3
        
    p4 = os.path.join(vault_path, 'Daily Notes', f"{target_date} {day_name_cap}.md")
    if os.path.exists(p4):
        return p4
        
    return None

def parse_footer_counts(daily_note_path):
    if not daily_note_path or not os.path.exists(daily_note_path):
        return None
        
    with open(daily_note_path, 'r') as f:
        content = f.read()
        
    # Check if a work log section exists
    if '## 🚀 Highlights & Decisions' not in content and '## 🏆 Accomplishments' not in content:
        return None
        
    # Find Sources footer
    # Example: *Sources: Slack (12 msgs / 4 channels) | Linear (5 issues) | Gmail work (8 threads), personal-main (1) | Calendar (4 events / 3 accts) | Todoist (3 completed, 10 open) | daily note + chat.*
    footer_match = re.search(r'Sources:\s*(.*?)(?:\*|$)', content, re.MULTILINE)
    if not footer_match:
        return None
        
    footer_text = footer_match.group(1)
    
    counts = {
        "slack": 0,
        "linear": 0,
        "gmail_work": 0,
        "gmail_personal": 0,
        "calendar": 0,
        "todoist_completed": 0,
        "todoist_open": 0
    }
    
    # Slack counts
    m_slack = re.search(r'Slack\s*\((\d+)\s+msgs', footer_text)
    if m_slack:
        counts["slack"] = int(m_slack.group(1))
        
    # Linear counts
    m_linear = re.search(r'Linear\s*\((\d+)\s+issues', footer_text)
    if m_linear:
        counts["linear"] = int(m_linear.group(1))
        
    # Gmail work counts
    m_work_mail = re.search(r'Gmail work\s*\((\d+)\s+threads', footer_text)
    if m_work_mail:
        counts["gmail_work"] = int(m_work_mail.group(1))
        
    # Gmail personal-main counts
    m_personal_mail = re.search(r'personal-main\s*\((\d+)\)', footer_text)
    if m_personal_mail:
        counts["gmail_personal"] = int(m_personal_mail.group(1))
        
    # Calendar counts
    m_cal = re.search(r'Calendar\s*\((\d+)\s+events', footer_text)
    if m_cal:
        counts["calendar"] = int(m_cal.group(1))
        
    # Todoist counts
    m_todo = re.search(r'Todoist\s*\((\d+)\s+completed,\s*(\d+)\s+open', footer_text)
    if m_todo:
        counts["todoist_completed"] = int(m_todo.group(1))
        counts["todoist_open"] = int(m_todo.group(2))
        
    return counts

def fetch_slack_count(target_date):
    t_dt = datetime.strptime(target_date, '%Y-%m-%d')
    after_date = (t_dt - timedelta(days=1)).strftime('%Y-%m-%d')
    before_date = (t_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    
    slack_script = os.path.expanduser('~/.hermes/skills/social-media/slack/scripts/slack.py')
    
    # from msg
    cmd_from = f"python3 {slack_script} search 'from:@justin after:{after_date} before:{before_date}' --limit 50"
    from_res = run_cmd(cmd_from)
    from_count = len(from_res) if isinstance(from_res, list) else 0
    
    # to msg
    cmd_to = f"python3 {slack_script} search 'to:@justin after:{after_date} before:{before_date}' --limit 50"
    to_res = run_cmd(cmd_to)
    to_count = len(to_res) if isinstance(to_res, list) else 0
    
    return from_count + to_count

def fetch_linear_count(target_date, env):
    api_key = env.get('LINEAR_API_KEY')
    user_id = env.get('LINEAR_USER_ID', '211987db-f790-4bfa-8c8e-518e1f704901')
    if not api_key:
        return 0
        
    t_dt = datetime.strptime(target_date, '%Y-%m-%d')
    tomorrow = (t_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    
    query = """
    {
      issues(filter: {
        and: [
          { updatedAt: { gte: "%sT00:00:00.000Z", lt: "%sT00:00:00.000Z" } },
          { or: [
            { assignee: { id: { eq: "%s" } } },
            { creator:  { id: { eq: "%s" } } },
            { subscribers: { id: { eq: "%s" } } }
          ] }
        ]
      }, first: 50) {
        nodes { identifier }
      }
    }
    """ % (target_date, tomorrow, user_id, user_id, user_id)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }
    
    req = urllib.request.Request(
        "https://api.linear.app/graphql", 
        data=json.dumps({"query": query}).encode('utf-8'), 
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(req) as r:
            res_data = json.loads(r.read().decode('utf-8'))
            return len(res_data.get('data', {}).get('issues', {}).get('nodes', []))
    except Exception as e:
        return 0

def fetch_gws_counts(target_date):
    gws_script = os.path.expanduser('~/.hermes/skills/productivity/google-workspace/scripts/gws_multi.py')
    t_dt = datetime.strptime(target_date, '%Y-%m-%d')
    tomorrow = (t_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    
    local_offset = datetime.now().astimezone().strftime('%z')
    formatted_offset = f"{local_offset[:-2]}:{local_offset[-2:]}" if local_offset else "Z"
    
    # Calendar count
    cal_cmd = f"python3 {gws_script} --account all calendar list --start {target_date}T00:00:00{formatted_offset} --end {tomorrow}T00:00:00{formatted_offset} --max 50"
    cal_res = run_cmd(cal_cmd)
    cal_count = len(cal_res) if isinstance(cal_res, list) else 0
    
    # Gmail counts (requires slashes)
    date_slash = t_dt.strftime('%Y/%m/%d')
    tomorrow_slash = (t_dt + timedelta(days=1)).strftime('%Y/%m/%d')
    
    work_mail_cmd = f"python3 {gws_script} --account work gmail search 'after:{date_slash} before:{tomorrow_slash}' --max 50"
    work_res = run_cmd(work_mail_cmd)
    work_count = len(work_res) if isinstance(work_res, list) else 0
    
    personal_mail_cmd = f"python3 {gws_script} --account personal-main gmail search 'after:{date_slash} before:{tomorrow_slash}' --max 50"
    personal_res = run_cmd(personal_mail_cmd)
    personal_count = len(personal_res) if isinstance(personal_res, list) else 0
    
    return {
        "calendar": cal_count,
        "gmail_work": work_count,
        "gmail_personal": personal_count
    }

def get_vault_activity(vault_path, last_briefing_dt):
    total_updated = 0
    type_counts = {}
    added_entities = {"person": [], "company": [], "concept": []}
    
    # Folders to skip
    skip_dirs = {".git", ".trash", ".cursor", ".claude", "_templates", "utilities", "Readwise"}
    
    for root, dirs, files in os.walk(vault_path):
        # In-place modify dirs to skip unwanted directories
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in files:
            if not f.endswith(".md") or f == "RESOLVER.md":
                continue
                
            file_path = os.path.join(root, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mtime < last_briefing_dt:
                    continue
            except Exception:
                continue
                
            # Get relative path as slug (no extension, forward slashes)
            rel_path = os.path.relpath(file_path, vault_path)
            slug = rel_path[:-3].replace(os.path.sep, '/')
            
            # Parse title & type from frontmatter or heading
            title = f[:-3] # default to filename without extension
            ptype = "note"  # default to note catch-all
            content = ""
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as file_obj:
                    content = file_obj.read()
                
                # Check frontmatter
                if content.startswith("---"):
                    end_idx = content.find("\n---", 3)
                    if end_idx > 0:
                        fm = content[3:end_idx]
                        type_match = re.search(r"^type:\s*[\"']?([a-zA-Z0-9_-]+)[\"']?", fm, re.MULTILINE)
                        if type_match:
                            ptype = type_match.group(1).strip()
                            
                        title_match = re.search(r"^title:\s*[\"']?([^\"'\n]+)[\"']?", fm, re.MULTILINE)
                        if title_match:
                            title = title_match.group(1).strip()
                
                # If title is still filename, try first H1 header in file
                if title == f[:-3]:
                    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if h1_match:
                        title = h1_match.group(1).strip()
            except Exception:
                pass
            
            # Map specific directory patterns to types if untyped or default
            if ptype == "note":
                if (slug.startswith("Inputs/Meetings/") or slug.startswith("Logs/Meetings/")
                        or slug.startswith("logs/meetings/") or slug.startswith("meetings/")):
                    ptype = "meeting"
                elif slug.startswith("Notes/Daily Notes/") or slug.startswith("Daily Notes/") or slug.startswith("Logs/Daily/") or slug.startswith("logs/daily/") or slug.startswith("daily/"):
                    ptype = "daily"
                elif slug.startswith("Notes/Contacts/") or slug.startswith("Contacts/") or slug.startswith("contacts/"):
                    ptype = "person"
                elif (slug.startswith("Inputs/Readings/") or slug.startswith("Logs/Sources/")
                        or slug.startswith("Logs/Readings/") or slug.startswith("sources/")):
                    ptype = "reading"
                elif slug.startswith("archive/"):
                    ptype = "archive"
            
            total_updated += 1
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
            
            if ptype in added_entities:
                created_dt = None
                try:
                    # Parse id from frontmatter
                    id_match = re.search(r"^id:\s*[\"']?(\d{14})[\"']?", content, re.MULTILINE)
                    if id_match:
                        id_str = id_match.group(1)
                        created_dt = datetime.strptime(id_str, "%Y%m%d%H%M%S")
                except Exception:
                    pass
                    
                if created_dt and created_dt >= last_briefing_dt:
                    added_entities[ptype].append({"slug": slug, "title": title})
                    
    return {
        "total_updated": total_updated,
        "type_counts": type_counts,
        "added_entities": added_entities
    }

def main():
    env = load_env()
    for k, v in env.items():
        os.environ[k] = v
        
    vault_path = os.environ.get('OBSIDIAN_VAULT_PATH', '/home/justin.guest/Developer/obsidian-vault')
    target_date = get_target_date()
    
    # Calculate previous morning briefing cutoff (yesterday 7:00 AM)
    # Since this runs at 7 AM, yesterday 7 AM is exactly 24 hours ago
    last_briefing_dt = datetime.now() - timedelta(hours=24)
    
    # Read daily note and parse footer
    note_path = find_daily_note(vault_path, target_date)
    footer_counts = parse_footer_counts(note_path)
    
    # Fetch live counts for Slack, Linear, GWS
    slack_count = fetch_slack_count(target_date)
    linear_count = fetch_linear_count(target_date, env)
    gws_counts = fetch_gws_counts(target_date)
    
    # Get Vault activity
    vault_act = get_vault_activity(vault_path, last_briefing_dt)
    
    out = {
        "target_date": target_date,
        "daily_note_path": note_path,
        "daily_note_exists": note_path is not None,
        "work_log_exists": footer_counts is not None,
        "footer_counts": footer_counts,
        "live_counts_except_todoist": {
            "slack": slack_count,
            "linear": linear_count,
            "gmail_work": gws_counts["gmail_work"],
            "gmail_personal": gws_counts["gmail_personal"],
            "calendar": gws_counts["calendar"]
        },
        "vault_activity": vault_act
    }
    
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
