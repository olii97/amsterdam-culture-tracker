# Scraper Template

Use this as the starting point for every new venue scraper.
Replace all `TODO` comments with venue-specific logic.

```python
"""
Scrape all events from <VENUE_NAME> agenda.
Uses requests + BeautifulSoup (SSR HTML parsing).
Outputs to events.md and events.csv in this folder.
"""

import requests
from bs4 import BeautifulSoup
import re
import csv
import time
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "TODO"  # e.g. "https://www.concertgebouw.nl"
AGENDA_URL = f"{BASE_URL}/TODO"  # e.g. f"{BASE_URL}/concerten-en-tickets"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
VENUE_NAME = "TODO"  # e.g. "Concertgebouw"


def parse_events_from_page(soup):
    """Extract event data from a parsed page."""
    # TODO: Find the repeating event element
    # Examples:
    #   cards = soup.find_all("div", class_="program teaser")
    #   cards = soup.find_all("a", href=re.compile(r"^/concerten/\d+"))
    cards = []
    events = []
    seen_hrefs = set()

    for card in cards:
        # TODO: Extract the event detail link
        href = ""  # e.g. card.find("a").get("href", "")
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        # TODO: Extract each field from the card HTML
        title = ""
        event_type = ""
        date_str = ""
        hall = ""
        description = ""
        price = ""

        url = BASE_URL + href

        events.append({
            "title": title,
            "event_type": event_type,
            "date": date_str,
            "hall": hall,
            "description": description,
            "url": url,
            "price": price,
        })

    return events


def scrape_all_pages():
    """Fetch all pages and return combined event list."""
    all_events = []
    seen_urls = set()

    # TODO: Implement pagination loop
    # Option A: Page numbers (?page=1, ?page=2, ...)
    # Option B: Month-based (/agenda/start/YYYY/MM)
    # Option C: Single page (just fetch once)
    page = 1
    while True:
        url = f"{AGENDA_URL}?page={page}"  # TODO: adjust URL pattern
        print(f"Fetching page {page}... ", end="", flush=True)

        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"HTTP {r.status_code}, stopping.")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        events = parse_events_from_page(soup)

        if not events:
            print("0 events, stopping.")
            break

        # Deduplicate
        new_events = [e for e in events if e["url"] not in seen_urls]
        for e in new_events:
            seen_urls.add(e["url"])

        all_events.extend(new_events)
        print(f"{len(new_events)} new events (total: {len(all_events)})")

        page += 1
        time.sleep(0.5)

    return all_events


def write_markdown(events, filename=None):
    if filename is None:
        filename = os.path.join(SCRIPT_DIR, "events.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {VENUE_NAME} Events\n\n")
        f.write(f"Source: {AGENDA_URL}\n\n")
        f.write(f"Total events: {len(events)}\n\n")
        f.write("| Event Title | Event Type | Date | Hall | Description | URL | Price |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for e in events:
            desc = (e["description"][:80] + "...") if len(e["description"]) > 80 else e["description"]
            f.write(
                f'| {e["title"]} | {e["event_type"]} | {e["date"]} '
                f'| {e["hall"]} | {desc} | [Link]({e["url"]}) | {e["price"]} |\n'
            )
    print(f"Written {filename}")


def write_csv(events, filename=None):
    if filename is None:
        filename = os.path.join(SCRIPT_DIR, "events.csv")
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["title", "event_type", "date", "hall", "description", "url", "price"]
        )
        writer.writeheader()
        writer.writerows(events)
    print(f"Written {filename}")


if __name__ == "__main__":
    print(f"Scraping {VENUE_NAME} agenda...")
    print("=" * 60)
    events = scrape_all_pages()
    print("=" * 60)
    print(f"\nTotal: {len(events)} events\n")
    write_markdown(events)
    write_csv(events)
    print("\nDone!")
```

## Existing Venue Examples

| Venue | Pagination | Card Selector | Notes |
|---|---|---|---|
| Concertgebouw | `?page=N` (1-21) | `<a href="/concerten/ID-slug">` | All data in link text, regex parsing |
| Pakhuis de Zwijger | `/agenda/start/YYYY/MM` | `div.program.teaser` | Structured divs: `.suptitle`, `.title`, `.subtitle`, `.meta` |

## Registration Checklist

After creating the scraper:

1. Create `cultural_venues_scraper/<venue_name>/__init__.py` (empty file)
2. Add `"<venue_name>"` to `VENUES` list in `cultural_venues_scraper/scrape_all.py`
3. Run `python -m cultural_venues_scraper.<venue_name>.scraper` to test standalone
4. Run `python -m cultural_venues_scraper.scrape_all` to test combined
