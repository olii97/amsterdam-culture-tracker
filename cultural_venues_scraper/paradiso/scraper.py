"""
Scrape events from Paradiso via podiuminfo.nl.
Uses requests + BeautifulSoup to parse JSON-LD structured data.
Paginated listing (25 events per page, offset-based).
Outputs to events.md and events.csv in this folder.
"""

import requests
import json
import re
import csv
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://www.podiuminfo.nl"
LISTING_URL = f"{BASE_URL}/podium/2/concerten/Paradiso/Amsterdam/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
VENUE_NAME = "Paradiso"


def format_date(iso_str):
    """Convert ISO datetime to readable Dutch-style format."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        days_nl = ["ma", "di", "wo", "do", "vr", "za", "zo"]
        months_nl = [
            "jan", "feb", "mrt", "apr", "mei", "jun",
            "jul", "aug", "sep", "okt", "nov", "dec",
        ]
        day_name = days_nl[dt.weekday()]
        month_name = months_nl[dt.month - 1]
        return f"{day_name} {dt.day} {month_name}. {dt.year}, {dt.strftime('%H:%M')}"
    except Exception:
        return iso_str


def extract_hall_from_html(soup, event_url):
    """Extract hall name (e.g. Grote Zaal) from the HTML row."""
    link = soup.find("a", href=event_url)
    if not link:
        return ""
    row = link.find_parent("section", class_="concert_rows_info")
    if not row:
        return ""
    td4 = row.find("div", class_="td_4_1")
    if td4:
        # Normalize whitespace (some hall names have extra spaces/newlines)
        import re as _re
        return _re.sub(r"\s+", " ", td4.get_text(strip=True))
    return ""


def parse_page(url):
    """Parse a single listing page, returning events from JSON-LD."""
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    ld_scripts = soup.find_all("script", type="application/ld+json")

    events = []
    for script in ld_scripts:
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue

        if data.get("@type") != "MusicEvent":
            continue

        # Title: strip " @ Paradiso" suffix
        name = data.get("name", "")
        title = re.sub(r"\s*@\s*Paradiso\s*$", "", name).strip()

        # Date
        start_date = data.get("startDate", "")

        # Location
        location = VENUE_NAME
        loc_data = data.get("location", {})
        if isinstance(loc_data, dict):
            location = loc_data.get("name", VENUE_NAME)

        # Price
        price = "TBA"
        offers = data.get("offers", [])
        if isinstance(offers, dict):
            offers = [offers]
        if offers and isinstance(offers, list):
            offer = offers[0]
            p = offer.get("price", "")
            currency = offer.get("priceCurrency", "EUR")
            avail = offer.get("availability", "")
            if p:
                price = f"{currency} {p}"
            if "SoldOut" in avail:
                price += " [UITVERKOCHT]" if price != "TBA" else "[UITVERKOCHT]"

        # Description
        description = data.get("description", "").strip()
        if len(description) > 120:
            description = description[:120].rsplit(" ", 1)[0] + "..."

        event_type = "Concert"

        # Get hall name from HTML (e.g. Grote Zaal, Kleine Zaal)
        event_url = data.get("url", "")
        hall_name = extract_hall_from_html(soup, event_url)
        if hall_name:
            location = f"{location} - {hall_name}"

        # Event status
        status = data.get("eventStatus", "")
        if "Cancelled" in status:
            price = "[GEANNULEERD]"
        elif "Postponed" in status:
            price += " [UITGESTELD]" if price != "TBA" else "[UITGESTELD]"

        events.append({
            "title": title,
            "event_type": event_type,
            "date": format_date(start_date),
            "hall": location,
            "description": description,
            "url": event_url,
            "price": price,
        })

    return events


def scrape_all_pages():
    """Fetch all pages of the Paradiso listing on podiuminfo.nl."""
    all_events = []
    seen_urls = set()
    page = 0

    while True:
        if page == 0:
            url = LISTING_URL
        else:
            url = f"{BASE_URL}/podium/2/concerten/{page}/Paradiso/Amsterdam/"

        print(f"Page {page}: {url}... ", end="", flush=True)
        events = parse_page(url)

        if not events:
            print("0 events (done)")
            break

        # Deduplicate (pages can overlap by 1 event)
        new_events = []
        for e in events:
            if e["url"] not in seen_urls:
                seen_urls.add(e["url"])
                new_events.append(e)

        all_events.extend(new_events)
        print(f"{len(events)} events ({len(new_events)} new)")

        time.sleep(0.5)
        page += 1

        # Safety limit
        if page > 20:
            break

    return all_events


def write_markdown(events, filename=None):
    if filename is None:
        filename = os.path.join(SCRIPT_DIR, "events.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {VENUE_NAME} Events\n\n")
        f.write(f"Source: {LISTING_URL}\n\n")
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
    print(f"Scraping {VENUE_NAME} (via podiuminfo.nl)...")
    print("=" * 60)
    events = scrape_all_pages()
    print("=" * 60)
    print(f"\nTotal: {len(events)} events\n")
    write_markdown(events)
    write_csv(events)
    print("\nDone!")
