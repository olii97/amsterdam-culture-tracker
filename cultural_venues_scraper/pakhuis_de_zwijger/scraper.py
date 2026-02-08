"""
Scrape all events from Pakhuis de Zwijger agenda.
Uses requests + BeautifulSoup (SSR HTML parsing).
Pagination is month-based: /agenda/start/YYYY/MM
Outputs to events.md and events.csv in this folder.
"""

import requests
from bs4 import BeautifulSoup
import re
import csv
import time
import os
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://dezwijger.nl"
AGENDA_URL = f"{BASE_URL}/agenda"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def parse_events_from_page(soup):
    """Extract event data from a parsed page."""
    cards = soup.find_all("div", class_="program teaser")
    events = []
    seen_hrefs = set()

    for card in cards:
        # Get link
        link = card.find("a", class_="program-link")
        if not link:
            continue
        href = link.get("href", "")
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        details = card.find("div", class_="details")
        if not details:
            continue

        # Event type (suptitle): "Boekpresentatie & nagesprek", "Europa in Amsterdam", etc.
        suptitle = details.find("div", class_="suptitle")
        event_type = suptitle.get_text(strip=True) if suptitle else ""
        # Remove trailing numbers from series (e.g. "Europa in Amsterdam 2" -> "Europa in Amsterdam")
        event_type = re.sub(r"\s*\d+\s*$", "", event_type)

        # Title
        title_el = details.find("div", class_="title")
        title = title_el.get_text(strip=True) if title_el else ""

        # Description (subtitle)
        subtitle_el = details.find("div", class_="subtitle")
        description = subtitle_el.get_text(strip=True) if subtitle_el else ""

        # Meta section
        meta = details.find("div", class_="meta")
        date_str = ""
        hall = ""
        price = ""

        if meta:
            # Date/time: "di 10 feb, 19.30" or "Morgen, 19.30" or "Vandaag, 20.00"
            date_el = meta.find("div", class_="date-time")
            date_str = date_el.get_text(strip=True) if date_el else ""

            # Location/hall
            loc_el = meta.find("div", class_="location")
            hall = loc_el.get_text(strip=True) if loc_el else ""

            # Price/entrance
            entrance_el = meta.find("div", class_="entrance")
            price = entrance_el.get_text(strip=True) if entrance_el else ""

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
    """Scrape all months of the Pakhuis de Zwijger agenda."""
    all_events = []
    seen_urls = set()

    # Start from current month, go up to 12 months ahead
    now = datetime.now()
    year, month = now.year, now.month

    for i in range(12):
        m = month + i
        y = year + (m - 1) // 12
        m = ((m - 1) % 12) + 1

        if i == 0:
            url = AGENDA_URL
        else:
            url = f"{AGENDA_URL}/start/{y}/{m:02d}"

        print(f"Fetching {y}/{m:02d}... ", end="", flush=True)

        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"HTTP {r.status_code}, stopping.")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        events = parse_events_from_page(soup)

        if not events:
            print("0 events, stopping.")
            break

        # Deduplicate across months (some events may appear on multiple pages)
        new_events = []
        for e in events:
            if e["url"] not in seen_urls:
                seen_urls.add(e["url"])
                new_events.append(e)

        all_events.extend(new_events)
        print(f"{len(new_events)} new events (total: {len(all_events)})")

        time.sleep(0.5)

    return all_events


def write_markdown(events, filename=None):
    if filename is None:
        filename = os.path.join(SCRIPT_DIR, "events.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Pakhuis de Zwijger Events\n\n")
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
    print("Scraping Pakhuis de Zwijger agenda...")
    print("=" * 60)
    events = scrape_all_pages()
    print("=" * 60)
    print(f"\nTotal: {len(events)} events\n")
    write_markdown(events)
    write_csv(events)
    print("\nDone!")
