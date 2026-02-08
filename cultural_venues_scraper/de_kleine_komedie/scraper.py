"""
Scrape all events from De Kleine Komedie agenda.
Uses requests + BeautifulSoup (SSR HTML parsing).
Pagination: ?page=N (8 events per page).
Also fetches detail pages for price + description via JSON-LD.
Outputs to events.md and events.csv in this folder.
"""

import requests
from bs4 import BeautifulSoup
import re
import csv
import json
import time
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://www.dekleinekomedie.nl"
AGENDA_URL = f"{BASE_URL}/agenda"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
VENUE_NAME = "De Kleine Komedie"


def fetch_detail_info(path):
    """Fetch price and description from event detail page JSON-LD."""
    try:
        r = requests.get(BASE_URL + path, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {}, {}
        soup = BeautifulSoup(r.text, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            content = script.string
            if content and '"Event"' in content:
                data = json.loads(content)
                if isinstance(data, list):
                    data = data[0]
                if data.get("@type") == "Event":
                    return data
        return {}
    except Exception:
        return {}


def parse_events_from_page(soup):
    """Extract event data from a parsed agenda page."""
    cards = soup.find_all("li", class_="eventCard")
    events = []
    seen_hrefs = set()

    for card in cards:
        link = card.find("a", class_="desc")
        if not link:
            continue
        href = link.get("href", "")
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        # Title
        title_el = card.find("h3", class_="title")
        title = title_el.get_text(strip=True) if title_el else ""

        # Subtitle (performers, show name)
        subtitle_el = card.find("div", class_="subtitle")
        subtitle = subtitle_el.get_text(strip=True) if subtitle_el else ""

        # Tagline (short description)
        tagline_el = card.find("div", class_="tagline")
        tagline = tagline_el.get_text(strip=True) if tagline_el else ""

        # Date from top-date
        top_date = card.find("div", class_="top-date")
        date_str = ""
        if top_date:
            start = top_date.find("span", class_="start")
            end_span = top_date.find("span", class_="end")
            time_span = top_date.find("span", class_="time")

            date_parts = []
            if start:
                date_parts.append(start.get_text(strip=True))
            if end_span:
                date_parts.append("t/m " + end_span.get_text(strip=True))

            if time_span:
                time_text = time_span.get_text(" ", strip=True)
                # Clean up "20.15 uur tot ca. 22.30 uur"
                time_text = re.sub(r"\s+", " ", time_text)
                date_parts.append(time_text)

            date_str = ", ".join(date_parts)

        # Genres as event type
        genres = card.find_all("a", class_="genres__link")
        genre_list = [g.get_text(strip=True) for g in genres]
        event_type = ", ".join(genre_list) if genre_list else "Cabaret"

        # Description = subtitle + tagline
        description = subtitle
        if tagline:
            description = f"{subtitle} - {tagline}" if subtitle else tagline

        url = BASE_URL + href

        events.append({
            "title": title,
            "event_type": event_type,
            "date": date_str,
            "hall": VENUE_NAME,
            "description": description,
            "url": url,
            "price": "",  # filled from detail pages
            "_path": href,
        })

    return events


def scrape_all_pages():
    """Fetch all agenda pages, then enrich with detail page data."""
    all_events = []
    seen_urls = set()
    page = 1

    # Phase 1: collect all events from listing pages
    while True:
        url = f"{AGENDA_URL}?page={page}"
        print(f"Fetching listing page {page}... ", end="", flush=True)

        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"HTTP {r.status_code}, stopping.")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        events = parse_events_from_page(soup)

        if not events:
            print("0 events, stopping.")
            break

        new_events = [e for e in events if e["url"] not in seen_urls]
        for e in new_events:
            seen_urls.add(e["url"])
        all_events.extend(new_events)
        print(f"{len(new_events)} events (total: {len(all_events)})")

        page += 1
        time.sleep(0.5)

    # Phase 2: fetch detail pages for price + richer description
    print(f"\nFetching {len(all_events)} detail pages for prices...")
    for i, event in enumerate(all_events):
        detail = fetch_detail_info(event["_path"])
        if detail:
            # Price
            offers = detail.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price_val = offers.get("price", "")
            if price_val:
                event["price"] = f"EUR {price_val}"
            availability = offers.get("availability", "")
            if "SoldOut" in availability:
                event["price"] += " [UITVERKOCHT]"

            # Better description from JSON-LD if card had none
            if not event["description"] and detail.get("description"):
                event["description"] = detail["description"]

        if (i + 1) % 10 == 0 or i == len(all_events) - 1:
            print(f"  {i+1}/{len(all_events)}")
        time.sleep(0.3)

    # Remove internal field
    for e in all_events:
        e.pop("_path", None)

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
