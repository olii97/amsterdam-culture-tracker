"""
Write scraped events to Supabase.
Maps scraper event format to the events table schema.
"""

import re
from datetime import datetime

import config

# Dutch month abbreviations -> month number
DUTCH_MONTHS = {
    "jan": 1, "feb": 2, "mrt": 3, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dec": 12,
}


def parse_event_date(date_str: str) -> str | None:
    """
    Parse Dutch date string (e.g. 'di 10 feb 2026, 19:30 - 23:00') to YYYY-MM-DD.
    Returns None if parsing fails.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    # Match: optional weekday + DD + month (3 chars) + YYYY
    # e.g. "di 10 feb 2026" or "10 feb 2026" or "10 februari 2026"
    m = re.search(r"(\d{1,2})\s+([a-z]{3,9})\s+(\d{4})", date_str.lower())
    if not m:
        return None
    day = int(m.group(1))
    mon_str = m.group(2)[:3]  # first 3 chars for abbreviation
    year = int(m.group(3))
    month = DUTCH_MONTHS.get(mon_str)
    if not month:
        return None
    try:
        dt = datetime(year, month, day)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def get_supabase_client():
    """Return a Supabase client, or None if not configured."""
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        return None
    from supabase import create_client
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def write_to_supabase(events: list[dict]) -> None:
    """
    Upsert scraped events to Supabase events table.
    Events must have: venue, title, event_type, date, description, url
    """
    sb = get_supabase_client()
    if not sb:
        print("Supabase not configured — skipping write")
        return

    rows = []
    skipped = 0
    for ev in events:
        event_date = parse_event_date(ev.get("date", ""))
        if not event_date:
            skipped += 1
            continue
        rows.append({
            "source_name": ev.get("venue", ""),
            "source_type": "scraper",
            "event_title": ev.get("title", ""),
            "event_type": ev.get("event_type", ""),
            "event_date": event_date,
            "description": ev.get("description", "") or "",
            "url": ev.get("url", "") or "",
        })

    if not rows:
        print("No events to write to Supabase (all dates failed to parse or empty)")
        if skipped:
            print(f"  Skipped {skipped} event(s) with unparseable dates")
        return

    try:
        sb.table("events").upsert(
            rows, on_conflict="event_title,event_date"
        ).execute()
        print(f"Upserted {len(rows)} row(s) to Supabase")
        if skipped:
            print(f"  Skipped {skipped} event(s) with unparseable dates")
    except Exception as e:
        print(f"ERROR writing events to Supabase: {type(e).__name__}: {e}")
        raise
