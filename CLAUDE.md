# Amsterdam Culture Tracker

## What it does

Automatically extracts cultural events from Amsterdam venue newsletters (Gmail) using Claude Haiku, stores them in Supabase, and writes them to Google Sheets. The goal is to build toward an iPhone app that lets you browse events, see venues on a map, and track your cultural outings.

## Architecture

```
Gmail Newsletters (De Kleine Komedie, Rode Hoed, etc.)
        |
  Python Extractor (extract_events.py)
  - fetches emails via Gmail API
  - extracts event data with Claude Haiku
  - deduplicates via processed_ids.json + Supabase processed_emails
        |
   +----+----+
   |         |
Google    Supabase (central DB)
Sheets    - events (31 rows)
          - venues (4 Amsterdam venues with coordinates)
          - venue_visits (track attendance)
          - processed_emails (dedup)
              |
        iPhone App (future)
```

## Current state

### Phase 1: Supabase Setup & Integration -- DONE
- Supabase project created, schema deployed (`schema.sql`)
- `extract_events.py` writes events to Supabase with upsert on `(event_title, event_date)`
- Deduplication uses union of local `processed_ids.json` AND Supabase `processed_emails` table
- Error handling with try/except and detailed logging on all Supabase operations
- RLS enabled with permissive policies (single-user app)
- Streamlit UI (`app.py`) also reads/writes Supabase

### Phase 2: Seed Venues -- DONE
- 4 venues seeded via `seed_venues.sql`: De Kleine Komedie, Rode Hoed, Koninklijk Theater Carre, Muziekgebouw aan 't IJ
- Each with address, GPS coordinates, and website

## Remaining phases

### Phase 3: iPhone App (SwiftUI)
Build a native iOS app that connects to Supabase and shows events.

**Screens:**
1. Events List -- upcoming events sorted by date, filterable by type/venue
2. Event Detail -- title, date, venue, description, ticket URL button
3. Venue Map -- MapKit with pins for all venues from `venues` table
4. Venue Detail -- venue info, upcoming events there, visit history
5. Visit Log -- mark that you visited a venue, see your history

**Tech stack:**
- SwiftUI for UI
- supabase-swift SDK (official, supports auth + database + realtime)
- MapKit for venue map
- No auth needed initially (read with anon key, writes for visits only)
- Develop on MacBook using Xcode
- Separate repo or subfolder `ios/`

### Phase 4: Push Notifications for New Events
Get notified on iPhone when new events are extracted.

**Options (simplest first):**
1. MVP: Poll Supabase on app launch, show badge/banner if `created_at` newer than last check
2. Supabase Realtime: live-update event list when app is open
3. Full push: Supabase Database Webhook -> Edge Function -> APNs (requires Apple Developer cert setup)

### Phase 5: Event Suggestions (future)
The app suggests events based on preferences and visit history.

- Track which event types you attend (cabaret, concert, debate...)
- Weight by venue visit frequency
- Surface events matching your profile
- Could use Claude API from an Edge Function for smarter recommendations
- Depends on having enough visit history data

## Files

| File | Purpose |
|------|---------|
| `extract_events.py` | Main extraction pipeline: Gmail -> Claude Haiku -> Sheets + Supabase |
| `app.py` | Streamlit UI for the pipeline |
| `config.py` | Loads env vars from `.env` |
| `schema.sql` | Full Supabase schema (events, venues, venue_visits, processed_emails + RLS) |
| `seed_venues.sql` | Initial Amsterdam venue data (4 venues with coordinates) |
| `.env` | Credentials (not committed) |
| `.env.example` | Template for `.env` |
| `requirements.txt` | Python dependencies |
| `run_extract.bat` | Windows batch file to run the extractor |

## Env vars

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API key for event extraction |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/public key |
| `GOOGLE_SHEET_ID` | Google Sheets spreadsheet ID |
| `DAYS_LOOKBACK` | How many days back to search Gmail (default: 7) |

## Commands

```bash
# Run extraction pipeline
python extract_events.py

# Run Streamlit UI
streamlit run app.py
```
