"""
Amsterdam Culture Event Extractor — Streamlit UI

Interactive pipeline: Import Emails → Extract Events → Preview → Write
"""

import json
import traceback
from datetime import datetime

import streamlit as st
import pandas as pd

import config
from extract_events import (
    get_google_creds,
    fetch_emails,
    extract_text_from_email,
    get_email_subject,
    get_email_sender,
    extract_events_with_llm,
    write_to_sheets,
    write_to_supabase,
    load_processed_ids,
    save_processed_ids,
    get_supabase_client,
    load_processed_ids_supabase,
    save_processed_email,
)
from googleapiclient.discovery import build


st.set_page_config(page_title="Amsterdam Culture Tracker", page_icon="🎭", layout="wide")
st.title("🎭 Amsterdam Culture Event Extractor")


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

def init_state():
    defaults = {
        "creds": None,
        "emails": [],
        "email_texts": {},       # msg_id -> {subject, sender, text, date}
        "extracted_events": [],   # flat list of event dicts
        "extraction_done": False,
        "step": 1,
        "log_messages": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


def add_log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append(f"[{ts}] {msg}")


# ---------------------------------------------------------------------------
# Sidebar: config info + log
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Configuration")
    st.text(f"Sheet ID: ...{config.GOOGLE_SHEET_ID[-8:]}")
    st.text(f"Days lookback: {config.DAYS_LOOKBACK}")
    st.text(f"Anthropic key: {'✅ set' if config.ANTHROPIC_API_KEY else '❌ missing'}")
    st.text(f"Supabase: {'✅ set' if config.SUPABASE_URL else '⏭️ skipped'}")

    st.divider()
    st.header("Log")
    for msg in st.session_state.log_messages[-20:]:
        st.text(msg)


# ---------------------------------------------------------------------------
# Step 1: Authenticate & Import Emails
# ---------------------------------------------------------------------------

st.header("Step 1: Import Emails")

if st.button("📥 Fetch Emails from Gmail", type="primary"):
    with st.spinner("Authenticating with Google..."):
        try:
            creds = get_google_creds()
            st.session_state.creds = creds
            add_log("Google auth OK")
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            st.stop()

    with st.spinner(f"Fetching emails from last {config.DAYS_LOOKBACK} days..."):
        try:
            gmail = build("gmail", "v1", credentials=creds)
            emails = fetch_emails(gmail, config.DAYS_LOOKBACK)
            st.session_state.emails = emails
            add_log(f"Fetched {len(emails)} email(s)")
        except Exception as e:
            st.error(f"Failed to fetch emails: {e}")
            st.stop()

    # Extract text from each email
    processed_ids = load_processed_ids() | load_processed_ids_supabase()
    email_texts = {}
    for msg in emails:
        msg_id = msg["id"]
        subject = get_email_subject(msg)
        sender = get_email_sender(msg)
        text = extract_text_from_email(msg)
        already = msg_id in processed_ids

        # Get date from headers
        headers = msg.get("payload", {}).get("headers", [])
        date_str = ""
        for h in headers:
            if h["name"].lower() == "date":
                date_str = h["value"]
                break

        email_texts[msg_id] = {
            "subject": subject,
            "sender": sender,
            "text": text,
            "date": date_str,
            "already_processed": already,
            "char_count": len(text),
        }
    st.session_state.email_texts = email_texts
    st.session_state.extracted_events = []
    st.session_state.extraction_done = False
    st.rerun()

# Display fetched emails
if st.session_state.email_texts:
    email_data = []
    for msg_id, info in st.session_state.email_texts.items():
        email_data.append({
            "ID": msg_id[:8] + "...",
            "Subject": info["subject"],
            "From": info["sender"],
            "Date": info["date"],
            "Text (chars)": info["char_count"],
            "Already processed": "✅" if info["already_processed"] else "",
        })
    st.dataframe(pd.DataFrame(email_data), use_container_width=True, hide_index=True)

    # Expandable text previews
    with st.expander("📄 View extracted text per email"):
        for msg_id, info in st.session_state.email_texts.items():
            st.subheader(info["subject"])
            st.text(info["text"][:2000] + ("..." if len(info["text"]) > 2000 else ""))
            st.divider()
else:
    st.info("Click the button above to fetch emails.")


# ---------------------------------------------------------------------------
# Step 2: Extract Events with Claude
# ---------------------------------------------------------------------------

st.header("Step 2: Extract Events")

if not st.session_state.email_texts:
    st.info("Import emails first.")
elif st.session_state.extraction_done:
    st.success(f"Extraction complete — {len(st.session_state.extracted_events)} event(s) found.")
else:
    if st.button("🤖 Extract Events with Claude Haiku", type="primary"):
        if not config.ANTHROPIC_API_KEY:
            st.error("ANTHROPIC_API_KEY not set in .env")
            st.stop()

        processed_ids = load_processed_ids()
        all_events = []
        newly_processed = set()

        # Filter to unprocessed emails only
        to_process = {
            mid: info for mid, info in st.session_state.email_texts.items()
            if not info["already_processed"]
        }

        if not to_process:
            st.warning("All emails already processed. Clear processed_ids.json to reprocess.")
            st.session_state.extraction_done = True
            st.rerun()

        progress = st.progress(0, text="Extracting events...")
        total = len(to_process)

        for i, (msg_id, info) in enumerate(to_process.items()):
            progress.progress((i) / total, text=f"Processing: {info['subject']}")

            if not info["text"].strip():
                add_log(f"Skipped (no text): {info['subject']}")
                newly_processed.add(msg_id)
                continue

            try:
                result = extract_events_with_llm(info["text"], info["subject"])
                events = result.get("events", [])
                source_name = result.get("source_name", "Unknown")
                source_type = result.get("source_type", "newsletter")

                for ev in events:
                    ev["source_name"] = source_name
                    ev["source_type"] = source_type

                all_events.extend(events)
                newly_processed.add(msg_id)
                add_log(f"Extracted {len(events)} event(s) from {source_name}")

            except json.JSONDecodeError as e:
                add_log(f"JSON parse error for '{info['subject']}': {e}")
                st.warning(f"Failed to parse LLM response for: {info['subject']}")
            except Exception as e:
                add_log(f"Error for '{info['subject']}': {type(e).__name__}: {e}")
                st.warning(f"Error processing '{info['subject']}': {type(e).__name__}: {e}")
                with st.expander("Full traceback"):
                    st.code(traceback.format_exc())

        progress.progress(1.0, text="Done!")
        st.session_state.extracted_events = all_events
        st.session_state.extraction_done = True
        st.session_state._newly_processed = newly_processed
        st.rerun()


# ---------------------------------------------------------------------------
# Step 3: Preview & Write
# ---------------------------------------------------------------------------

if st.session_state.extraction_done and st.session_state.extracted_events:
    st.header("Step 3: Preview & Write")

    events = st.session_state.extracted_events

    # Build preview rows (one per event-date, as they'd appear in Sheets/Supabase)
    preview_rows = []
    for ev in events:
        for date in ev.get("dates_iso", [""]):
            preview_rows.append({
                "source_name": ev.get("source_name", ""),
                "source_type": ev.get("source_type", ""),
                "event_title": ev.get("event_title", ""),
                "event_type": ev.get("event_type", ""),
                "event_date": date,
                "description": ev.get("description", ""),
                "url": ev.get("url", ""),
            })

    df = pd.DataFrame(preview_rows)
    st.subheader(f"📋 {len(preview_rows)} rows to write")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Raw JSON view
    with st.expander("🔍 Raw extracted JSON"):
        st.json(events)

    # Write buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Write to Google Sheets", type="primary"):
            if not st.session_state.creds:
                st.error("Not authenticated. Go back to Step 1.")
            else:
                with st.spinner("Writing to Google Sheets..."):
                    try:
                        write_to_sheets(st.session_state.creds, events)
                        st.success("Written to Google Sheets!")
                        add_log(f"Wrote {len(preview_rows)} rows to Sheets")
                    except Exception as e:
                        st.error(f"Error: {e}")
                        add_log(f"Sheets error: {e}")

    with col2:
        if st.button("🗄️ Write to Supabase"):
            if not config.SUPABASE_URL:
                st.warning("Supabase not configured in .env — skipping")
            else:
                with st.spinner("Writing to Supabase..."):
                    try:
                        write_to_supabase(events)
                        st.success("Written to Supabase!")
                        add_log(f"Upserted {len(preview_rows)} rows to Supabase")
                    except Exception as e:
                        st.error(f"Error: {e}")
                        add_log(f"Supabase error: {e}")

    st.divider()

    if st.button("✅ Mark emails as processed"):
        processed = load_processed_ids()
        newly = st.session_state.get("_newly_processed", set())
        processed.update(newly)
        save_processed_ids(processed)

        # Also save to Supabase
        sb = get_supabase_client()
        if sb:
            for mid in newly:
                info = st.session_state.email_texts.get(mid, {})
                save_processed_email(sb, mid, info.get("subject", ""), info.get("sender", ""))

        st.success(f"Marked {len(newly)} email(s) as processed.")
        add_log(f"Marked {len(newly)} emails processed")

elif st.session_state.extraction_done:
    st.info("No events were extracted from the emails.")
