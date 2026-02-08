---
name: venue-scraper
description: >
  Create event scrapers for Amsterdam cultural venue websites. Use when the user provides
  a venue agenda URL and wants events extracted into standardized MD and CSV files. Handles
  the full workflow: reconnaissance of the site structure, building a requests+BeautifulSoup
  scraper, pagination, and output. All scrapers produce the same 7 columns: title, event_type,
  date, hall, description, url, price. Trigger when user says things like "scrape this venue",
  "add this venue", "extract events from this website", or provides a venue agenda URL.
---

# Venue Scraper Creation Workflow

Create scrapers for Amsterdam cultural venue agenda pages. Each scraper lives in
`cultural_venues_scraper/<venue_name>/scraper.py` and outputs `events.md` + `events.csv`.

## Required Output Columns

Every scraper MUST produce events as dicts with exactly these 7 keys:

| Column | Content |
|---|---|
| `title` | Event name |
| `event_type` | Category (Concert, Film, Debate, Festival, etc.) |
| `date` | Date + time as shown on site |
| `hall` | Room/zaal name within the venue |
| `description` | Short description, subtitle, or featured artists/pieces |
| `url` | Full URL to the event detail page |
| `price` | Price string, "Gratis", or "TBA". Append `[UITVERKOCHT]` / `[Laatste kaarten]` if applicable |

## Step-by-Step Workflow

### 1. Reconnaissance (DO NOT SKIP)

Fetch the agenda URL with `requests.get()` and analyze the HTML:

```python
import requests
from bs4 import BeautifulSoup
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 ..."})
soup = BeautifulSoup(r.text, "html.parser")
```

Determine:
- **Is the content server-side rendered?** Check if event text appears in the raw HTML.
  Search for event-related strings: `soup.get_text()` should contain titles, dates, prices.
  If the HTML is mostly empty JS bundles, the site is client-rendered (needs different strategy).
- **What is the event card structure?** Find the repeating HTML element per event.
  Look for `<article>`, `<div class="card/event/program">`, or `<a>` tags with event links.
- **Where is each field?** Map each of the 7 columns to an HTML element/class/pattern.
- **How does pagination work?** Check for: `?page=N`, `/page/N`, month-based URLs (`/YYYY/MM`),
  "load more" buttons, or API endpoints.

### 2. Create the Scraper

Place files at: `cultural_venues_scraper/<venue_name>/scraper.py`

The scraper MUST expose these 3 functions (required by `scrape_all.py`):

```python
def scrape_all_pages() -> list[dict]:
    """Fetch all pages, return list of event dicts."""

def write_markdown(events, filename=None):
    """Write events to events.md in the scraper's directory."""

def write_csv(events, filename=None):
    """Write events to events.csv in the scraper's directory."""
```

See `references/scraper-template.md` for the full boilerplate.

Key implementation rules:
- Use `requests` + `BeautifulSoup` (NOT Selenium/Playwright)
- Add `time.sleep(0.5)` between page requests
- Deduplicate events by URL across pages
- Stop pagination when a page returns 0 events
- Use `SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))` for output paths
- Create `__init__.py` in the venue folder

### 3. Pagination Strategies

Pick the strategy that matches the site:

| Pattern | Example | Loop Strategy |
|---|---|---|
| Page number query param | `?page=1`, `?page=2` | Increment page until 0 events |
| Month-based URLs | `/agenda/start/2026/03` | Iterate months from now, stop at 0 events |
| Offset-based | `?offset=0&limit=20` | Increment offset by page size |
| Single page | No pagination | Fetch once |

### 4. Register and Test

1. Add `__init__.py` to the venue folder
2. Add venue name to `VENUES` list in `cultural_venues_scraper/scrape_all.py`
3. Test standalone: `python -m cultural_venues_scraper.<venue_name>.scraper`
4. Test combined: `python -m cultural_venues_scraper.scrape_all`
5. Verify output: check row count, spot-check titles/dates/prices in CSV

### 5. Common Parsing Patterns

**Dutch dates:** `(ma|di|wo|do|vr|za|zo)\s+\d+\s+(jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec)`

**Price patterns:**
- `v.a. EUR X,XX` or `vanaf X,XX`
- `gratis` / `free` / `Gratis`
- `Uitverkocht` = sold out, `Laatste kaarten` = last tickets

**Event type:** Often in a subtitle, tag, category label, or CSS class above the title.

**Description:** Look for subtitles, taglines, or "met onder andere" (featuring) sections.
