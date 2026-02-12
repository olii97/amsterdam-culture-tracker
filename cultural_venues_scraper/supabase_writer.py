"""
Write scraped events to Supabase.
Maps scraper event format to the events table schema.
"""

import re
from datetime import datetime, timezone

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


def _event_key(row: dict) -> tuple[str, str]:
    """Normalize event key used by current UNIQUE(event_title, event_date)."""
    return (
        (row.get("event_title") or "").strip().lower(),
        row.get("event_date") or "",
    )


def _start_scraper_run(sb):
    """Create scraper run row and return run id (or None if unavailable)."""
    payload = {
        "source": "cultural_venues_scraper",
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        resp = sb.table("scraper_runs").insert(payload).execute()
        data = getattr(resp, "data", None) or []
        if data and isinstance(data, list):
            return data[0].get("id")
    except Exception as exc:
        print(f"WARNING: could not create scraper_runs row: {type(exc).__name__}: {exc}")
    return None


def _finish_scraper_run(sb, run_id, status, **fields):
    """Update scraper run row. No-op if run logging is unavailable."""
    if not run_id:
        return
    payload = {
        "status": status,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    try:
        sb.table("scraper_runs").update(payload).eq("id", run_id).execute()
    except Exception as exc:
        print(f"WARNING: could not update scraper_runs row: {type(exc).__name__}: {exc}")


def _fetch_existing_scraper_keys(sb, rows: list[dict]) -> set[tuple[str, str]]:
    """
    Fetch existing scraper event keys within the date window for new-event estimation.
    This estimates new inserts before upsert, based on current UNIQUE(event_title,event_date).
    """
    if not rows:
        return set()

    dates = [r["event_date"] for r in rows if r.get("event_date")]
    if not dates:
        return set()

    min_date = min(dates)
    max_date = max(dates)
    existing = set()
    page_size = 1000
    offset = 0

    while True:
        resp = (
            sb.table("events")
            .select("event_title,event_date")
            .eq("source_type", "scraper")
            .gte("event_date", min_date)
            .lte("event_date", max_date)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        data = getattr(resp, "data", None) or []
        for item in data:
            title = (item.get("event_title") or "").strip().lower()
            event_date = item.get("event_date") or ""
            if title and event_date:
                existing.add((title, event_date))
        if len(data) < page_size:
            break
        offset += page_size

    return existing


def write_to_supabase(events: list[dict]) -> None:
    """
    Upsert scraped events to Supabase events table.
    Events must have: venue, title, event_type, date, description, url
    """
    sb = get_supabase_client()
    if not sb:
        print("Supabase not configured — skipping write")
        return

    run_id = _start_scraper_run(sb)
    rows = []
    skipped = 0
    total_scraped = len(events)

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
        _finish_scraper_run(
            sb,
            run_id,
            "completed",
            total_scraped=total_scraped,
            parsed_rows=0,
            skipped_unparseable_dates=skipped,
            new_events_estimated=0,
        )
        return

    # Deduplicate by (event_title, event_date) so upsert does not see duplicate keys
    seen_keys = set()
    unique_rows = []
    for row in rows:
        key = _event_key(row)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_rows.append(row)
    if len(unique_rows) < len(rows):
        print(f"Deduped {len(rows) - len(unique_rows)} duplicate (title, date) row(s) before upsert")

    try:
        existing_keys = _fetch_existing_scraper_keys(sb, unique_rows)
        new_events_estimated = sum(1 for row in unique_rows if _event_key(row) not in existing_keys)

        sb.table("events").upsert(
            unique_rows, on_conflict="event_title,event_date"
        ).execute()
        print(f"Upserted {len(unique_rows)} row(s) to Supabase")
        print(f"Estimated new events inserted: {new_events_estimated}")
        if skipped:
            print(f"  Skipped {skipped} event(s) with unparseable dates")

        _finish_scraper_run(
            sb,
            run_id,
            "completed",
            total_scraped=total_scraped,
            parsed_rows=len(unique_rows),
            skipped_unparseable_dates=skipped,
            new_events_estimated=new_events_estimated,
        )
    except Exception as e:
        print(f"ERROR writing events to Supabase: {type(e).__name__}: {e}")
        _finish_scraper_run(
            sb,
            run_id,
            "failed",
            total_scraped=total_scraped,
            parsed_rows=len(unique_rows),
            skipped_unparseable_dates=skipped,
            error_message=str(e),
        )
        raise
