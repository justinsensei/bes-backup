#!/usr/bin/env python3
import os
import sys
import json
import re
import datetime as dt

# Add slack scripts and google-workspace scripts directories to sys.path
sys.path.insert(0, "/home/justin.guest/.hermes/scripts")
sys.path.insert(0, "/home/justin.guest/.hermes/skills/productivity/google-workspace/scripts")

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Try importing Slack candidate functions
try:
    from fetch_slack_brains import get_client as get_slack_client, fetch_note_candidates
except ImportError:
    fetch_note_candidates = None

CACHE_FILE_EMAIL = os.path.expanduser("~/.hermes/processed_emails.json")

def load_processed_emails():
    if os.path.exists(CACHE_FILE_EMAIL):
        try:
            with open(CACHE_FILE_EMAIL, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_processed_emails(processed):
    os.makedirs(os.path.dirname(CACHE_FILE_EMAIL), exist_ok=True)
    with open(CACHE_FILE_EMAIL, "w") as f:
        json.dump(processed, f, indent=2)

def is_bot_sender(sender_raw):
    sender = (sender_raw or "").lower()
    bot_keywords = [
        "noreply", "no-reply", "notification", "billing", "support", "info", 
        "team", "bounce", "mailer-daemon", "newsletter", "alert", "update",
        "feedback", "marketing", "promo", "receipt", "invoice", "stripe", "customer.io"
    ]
    for kw in bot_keywords:
        if kw in sender:
            return True
    return False

def is_unsub_present(headers):
    # Check if List-Unsubscribe or similar exists
    for h in headers:
        if h["name"].lower() in ["list-unsubscribe", "x-unsub", "list-unsubscribe-post"]:
            return True
    return False

def get_email_body(payload):
    # Helper to recursively extract plain text body
    if "parts" in payload:
        for part in payload["parts"]:
            body = get_email_body(part)
            if body:
                return body
    else:
        mime_type = payload.get("mimeType", "")
        if mime_type == "text/plain":
            body_data = payload.get("body", {}).get("data", "")
            if body_data:
                import base64
                try:
                    return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
                except Exception:
                    pass
    return ""

def fetch_gmail_candidates():
    try:
        import google_api
    except ImportError:
        return []
        
    processed_emails = load_processed_emails()
    processed_set = set(processed_emails)
    
    start_date = (dt.date.today() - dt.timedelta(days=2)).strftime("%Y/%m/%d")
    accounts = ["work", "personal-main"]
    candidates = []
    
    for idx, account in enumerate(accounts):
        os.environ["GOOGLE_ACCOUNT"] = account
        try:
            service = google_api.build_service("gmail", "v1")
        except Exception as e:
            # Skip if auth fails
            continue
            
        try:
            # Search category:primary which targets human conversations
            res = service.users().messages().list(
                userId="me", 
                q=f"category:primary after:{start_date}", 
                maxResults=40
            ).execute()
        except Exception:
            continue
            
        messages_list = res.get("messages", [])
        # Unique threads to fetch
        thread_ids = set()
        for msg in messages_list:
            tid = msg.get("threadId")
            if tid and tid not in processed_set:
                thread_ids.add(tid)
                
        for tid in thread_ids:
            try:
                thread = service.users().threads().get(userId="me", id=tid).execute()
            except Exception:
                continue
                
            messages = thread.get("messages", [])
            if not messages:
                continue
                
            first_msg = messages[0]
            headers = first_msg.get("payload", {}).get("headers", [])
            headers_dict = {h["name"].lower(): h["value"] for h in headers}
            
            sender = headers_dict.get("from", "")
            subject = headers_dict.get("subject", "(No Subject)")
            
            # Filters:
            # 1. Skip if sender is bot-like
            if is_bot_sender(sender):
                continue
                
            # 2. Skip if List-Unsubscribe is present (newsletters)
            if is_unsub_present(headers):
                continue
                
            # 3. Check if candidate
            # Thread is a candidate if it has replies (len >= 2), or is a single message from important domains
            is_candidate = len(messages) >= 2
            
            if not is_candidate and len(messages) == 1:
                # Single message is candidate if from school, family, financial advisors or contains important keywords
                body_text = get_email_body(first_msg.get("payload", {}))
                important_keywords = ["deadline", "signing", "commencement", "contract", "school", "agreement", "decision", "meeting"]
                important_senders = ["waldorf", "winchester", "thurston", "advisor", "nana", "massie"]
                
                body_lower = body_text.lower()
                sender_lower = sender.lower()
                
                has_kw = any(kw in body_lower for kw in important_keywords)
                has_sender = any(snd in sender_lower for snd in important_senders)
                
                if has_kw or has_sender:
                    is_candidate = True
                    
            if not is_candidate:
                continue
                
            # Prepare cleaned messages list
            cleaned_msgs = []
            participants = set()
            
            for msg in messages:
                m_headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
                m_from = m_headers.get("from", "")
                m_date = m_headers.get("date", "")
                m_subject = m_headers.get("subject", "")
                
                # Resolve a pretty sender name
                sender_clean = m_from
                m_match = re.search(r"([^<]+)", m_from)
                if m_match:
                    sender_clean = m_match.group(1).strip().strip('"').strip("'")
                participants.add(sender_clean)
                
                body = get_email_body(msg.get("payload", {})) or msg.get("snippet", "")
                
                cleaned_msgs.append({
                    "id": msg.get("id"),
                    "from": m_from,
                    "from_clean": sender_clean,
                    "date": m_date,
                    "subject": m_subject,
                    "text": body
                })
                
            # Create Gmail permalink
            # Account index for work is typically 0, personal-main is typically 1
            acct_index = 0 if account == "work" else 1
            permalink = f"https://mail.google.com/mail/u/{acct_index}/#inbox/{tid}"
            
            candidates.append({
                "account": account,
                "thread_id": tid,
                "subject": subject,
                "participants": list(participants),
                "permalink": permalink,
                "message_count": len(cleaned_msgs),
                "messages": cleaned_msgs,
                "preview": cleaned_msgs[0]["text"][:150] + "..." if len(cleaned_msgs[0]["text"]) > 150 else cleaned_msgs[0]["text"]
            })
            
    return candidates

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-all", action="store_true", help="List candidates from Slack and Email")
    parser.add_argument("--mark-email-processed", metavar="THREAD_ID", help="Mark email thread as processed")
    args = parser.parse_args()
    
    if args.mark_email_processed:
        tid = args.mark_email_processed
        processed = load_processed_emails()
        if tid not in processed:
            processed.append(tid)
            save_processed_emails(processed)
            print(json.dumps({"ok": True, "marked": tid}))
        else:
            print(json.dumps({"ok": True, "already_processed": tid}))
        sys.exit(0)
        
    slack_candidates = []
    if fetch_note_candidates:
        try:
            slack_client = get_slack_client()
            slack_candidates = fetch_note_candidates(slack_client)
        except Exception as e:
            # Print error to stderr but don't fail the whole script
            print(f"Error fetching Slack candidates: {e}", file=sys.stderr)
            
    email_candidates = []
    try:
        email_candidates = fetch_gmail_candidates()
    except Exception as e:
        print(f"Error fetching Email candidates: {e}", file=sys.stderr)
        
    print(json.dumps({
        "slack": slack_candidates,
        "email": email_candidates
    }, indent=2))

if __name__ == "__main__":
    main()
