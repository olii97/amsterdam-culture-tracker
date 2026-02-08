"""
Amsterdam Culture Event Extractor

Fetches newsletter emails via Gmail API, extracts events using Claude Haiku,
and writes results to Google Sheets and optionally Supabase.
"""

import base64
import json
import os
import sys
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import anthropic
import gspread

import config


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

def get_google_creds() -> Credentials:
    """Return valid Google OAuth credentials, refreshing or prompting as needed."""
    creds = None
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GMAIL_CREDENTIALS_FILE, config.SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(config.TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


# ---------------------------------------------------------------------------
# Gmail: fetch emails
# ---------------------------------------------------------------------------

def fetch_emails(service, days: int) -> list[dict]:
    """Fetch emails from the last `days` days. Returns list of message dicts."""
    after = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f"in:inbox after:{after}"
    log(f"Searching Gmail with query: {query}")

    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    log(f"Found {len(messages)} message(s)")

    emails = []
    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_meta["id"], format="full"
        ).execute()
        emails.append(msg)
    return emails


# ---------------------------------------------------------------------------
# MIME: extract text from email
# ---------------------------------------------------------------------------

def extract_text_from_email(msg: dict) -> str:
    """Walk MIME parts, decode base64, convert HTML to plain text."""
    parts_to_check = []
    payload = msg.get("payload", {})

    if "parts" in payload:
        parts_to_check = payload["parts"]
    else:
        parts_to_check = [payload]

    html_parts = []
    text_parts = []

    def walk_parts(parts: list) -> None:
        for part in parts:
            mime = part.get("mimeType", "")
            if "parts" in part:
                walk_parts(part["parts"])
            elif mime == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html_parts.append(base64.urlsafe_b64decode(data).decode("utf-8", errors="replace"))
            elif mime == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    text_parts.append(base64.urlsafe_b64decode(data).decode("utf-8", errors="replace"))

    walk_parts(parts_to_check)

    # Prefer HTML → cleaned text; fall back to plain text
    if html_parts:
        full_html = "\n".join(html_parts)
        soup = BeautifulSoup(full_html, "html.parser")
        # Remove script/style
        for tag in soup(["script", "style"]):
            tag.decompose()
        # Inline href URLs so they survive text extraction
        for a in soup.find_all("a", href=True):
            href = a["href"]
            link_text = a.get_text(strip=True)
            if href and href.startswith("http"):
                a.replace_with(f"{link_text} ({href})")
        text = soup.get_text(separator="\n", strip=True)
        return text
    return "\n".join(text_parts)


def get_email_subject(msg: dict) -> str:
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == "subject":
            return h["value"]
    return "(no subject)"


def get_email_sender(msg: dict) -> str:
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == "from":
            return h["value"]
    return ""


# ---------------------------------------------------------------------------
# Deduplication: processed IDs
# ---------------------------------------------------------------------------

def load_processed_ids() -> set:
    if os.path.exists(config.PROCESSED_IDS_FILE):
        with open(config.PROCESSED_IDS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_processed_ids(ids: set) -> None:
    with open(config.PROCESSED_IDS_FILE, "w") as f:
        json.dump(sorted(ids), f)


# ---------------------------------------------------------------------------
# Claude Haiku: extract events as JSON
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT_TEMPLATE = """\
You are an event extraction assistant. Given the text of a newsletter email \
from an Amsterdam cultural venue, extract all events mentioned.

Return ONLY valid JSON (no markdown fences) in this exact format:
{{
  "source_name": "Name of the venue or newsletter sender",
  "source_type": "newsletter",
  "events": [
    {{
      "event_title": "Name of the event / performer",
      "event_type": "concert | cabaret | debate | lecture | film | theater | other",
      "dates_iso": ["2026-01-19", "2026-01-20"],
      "description": "Short description of the event (1-2 sentences)",
      "url": "URL for tickets or event page, if available (otherwise null)"
    }}
  ]
}}

Rules:
- dates_iso must be ISO 8601 date strings (YYYY-MM-DD). Resolve relative dates \
using today's date which is {today}.
- If a date range is given (e.g. "19 t/m 22 jan"), list each individual date.
- If no year is stated, assume the upcoming occurrence of that date.
- If you cannot determine any events, return {{"source_name": "Unknown", "source_type": "newsletter", "events": []}}.
"""


def extract_events_with_llm(text: str, subject: str) -> dict:
    """Send email text to Claude Haiku and parse the JSON response."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    today = datetime.now().strftime("%Y-%m-%d")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Email subject: {subject}\n\n"
                    f"Email body:\n{text[:30000]}\n\n"
                    + EXTRACTION_PROMPT_TEMPLATE.format(today=today)
                ),
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    return json.loads(raw)


# ---------------------------------------------------------------------------
# Google Sheets: write events
# ---------------------------------------------------------------------------

def write_to_sheets(creds: Credentials, all_events: list[dict]) -> None:
    """Append events to Google Sheets, skipping duplicates by event_title."""
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(config.GOOGLE_SHEET_ID)

    # Use first worksheet
    ws = sh.sheet1

    # Ensure header row exists
    existing = ws.get_all_values()
    if not existing:
        ws.append_row(["source_name", "source_type", "event_title", "event_type", "event_date", "description", "url"])
        existing_titles = set()
    else:
        # Column C (index 2) is event_title
        existing_titles = {row[2] for row in existing[1:] if len(row) > 2}

    rows_to_add = []
    for ev in all_events:
        if ev["event_title"] in existing_titles:
            continue
        for date in ev.get("dates_iso", [""]):
            rows_to_add.append([
                ev.get("source_name", ""),
                ev.get("source_type", ""),
                ev["event_title"],
                ev.get("event_type", ""),
                date,
                ev.get("description", ""),
                ev.get("url", ""),
            ])
        existing_titles.add(ev["event_title"])

    if rows_to_add:
        ws.append_rows(rows_to_add, value_input_option="USER_ENTERED")
        log(f"Wrote {len(rows_to_add)} row(s) to Google Sheets")
    else:
        log("No new rows to write to Google Sheets")


# ---------------------------------------------------------------------------
# Supabase: write events
# ---------------------------------------------------------------------------

def get_supabase_client():
    """Return a Supabase client, or None if not configured."""
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        return None
    from supabase import create_client
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def write_to_supabase(all_events: list[dict]) -> None:
    """Upsert events to Supabase, one row per event-date."""
    sb = get_supabase_client()
    if not sb:
        log("Supabase not configured — skipping")
        return

    rows = []
    for ev in all_events:
        for date in ev.get("dates_iso", [None]):
            rows.append({
                "source_name": ev.get("source_name", ""),
                "source_type": ev.get("source_type", ""),
                "event_title": ev["event_title"],
                "event_type": ev.get("event_type", ""),
                "event_date": date,
                "description": ev.get("description", ""),
                "url": ev.get("url", ""),
            })

    if not rows:
        log("No events to write to Supabase")
        return

    try:
        sb.table("events").upsert(
            rows, on_conflict="event_title,event_date"
        ).execute()
        log(f"Upserted {len(rows)} row(s) to Supabase")
    except Exception as e:
        log(f"ERROR writing events to Supabase: {type(e).__name__}: {e}")
        raise


def load_processed_ids_supabase() -> set:
    """Load processed Gmail IDs from Supabase processed_emails table."""
    sb = get_supabase_client()
    if not sb:
        return set()
    try:
        result = sb.table("processed_emails").select("gmail_id").execute()
        return {row["gmail_id"] for row in result.data}
    except Exception as e:
        log(f"WARNING: Could not load processed IDs from Supabase: {e}")
        return set()


def save_processed_email(sb, msg_id: str, subject: str, sender: str) -> None:
    """Record a processed email in Supabase."""
    try:
        sb.table("processed_emails").upsert(
            {"gmail_id": msg_id, "subject": subject, "sender": sender},
            on_conflict="gmail_id",
        ).execute()
    except Exception as e:
        log(f"WARNING: Could not save processed email {msg_id}: {e}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    log("=== Amsterdam Culture Event Extractor ===")

    if not config.ANTHROPIC_API_KEY:
        log("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    # 1. Authenticate
    log("Authenticating with Google...")
    creds = get_google_creds()
    gmail = build("gmail", "v1", credentials=creds)

    # 2. Fetch emails
    emails = fetch_emails(gmail, config.DAYS_LOOKBACK)
    if not emails:
        log("No emails found — done")
        return

    # 3. Load processed IDs (Supabase + local fallback)
    processed_local = load_processed_ids()
    processed_supa = load_processed_ids_supabase()
    processed = processed_local | processed_supa

    sb = get_supabase_client()

    # 4. Process each email
    all_events = []
    newly_processed = []  # list of (msg_id, subject, sender)

    for msg in emails:
        msg_id = msg["id"]
        if msg_id in processed:
            log(f"Skipping already-processed message {msg_id}")
            continue

        subject = get_email_subject(msg)
        sender = get_email_sender(msg)
        log(f"Processing: {subject} (from {sender})")

        try:
            text = extract_text_from_email(msg)
            if not text.strip():
                log(f"  No text extracted — skipping")
                continue
            log(f"  Extracted {len(text)} chars of text")

            # 5. LLM extraction
            result = extract_events_with_llm(text, subject)
            events = result.get("events", [])
            source_name = result.get("source_name", "Unknown")
            source_type = result.get("source_type", "newsletter")

            # Attach source info to each event
            for ev in events:
                ev["source_name"] = source_name
                ev["source_type"] = source_type

            log(f"  Extracted {len(events)} event(s) from {source_name}")
            all_events.extend(events)
            newly_processed.append((msg_id, subject, sender))

        except json.JSONDecodeError as e:
            log(f"  ERROR: Failed to parse LLM response as JSON: {e}")
        except Exception as e:
            log(f"  ERROR processing email: {type(e).__name__}: {e}")

    if not all_events:
        log("No new events extracted")
        # Still mark emails as processed even if no events found
        if newly_processed:
            ids_set = {mid for mid, _, _ in newly_processed}
            processed_local.update(ids_set)
            save_processed_ids(processed_local)
            if sb:
                for mid, subj, sndr in newly_processed:
                    save_processed_email(sb, mid, subj, sndr)
        return

    log(f"Total new events: {len(all_events)}")

    # 6. Write to Google Sheets
    try:
        write_to_sheets(creds, all_events)
    except Exception as e:
        log(f"ERROR writing to Google Sheets: {e}")

    # 7. Write to Supabase
    try:
        write_to_supabase(all_events)
    except Exception as e:
        log(f"ERROR writing to Supabase: {e}")

    # 8. Mark as processed (both local + Supabase)
    ids_set = {mid for mid, _, _ in newly_processed}
    processed_local.update(ids_set)
    save_processed_ids(processed_local)
    if sb:
        for mid, subj, sndr in newly_processed:
            save_processed_email(sb, mid, subj, sndr)

    log("Done!")


if __name__ == "__main__":
    main()
