"""
Scrape all events from Concertgebouw concert agenda.
Uses requests + BeautifulSoup (SSR HTML parsing, no browser needed).
Outputs to events.md and events.csv in this folder.
"""

import requests
from bs4 import BeautifulSoup
import re
import csv
import time
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "https://www.concertgebouw.nl"
AGENDA_URL = f"{BASE_URL}/concerten-en-tickets"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def parse_events_from_page(soup):
    """Extract event data from a parsed page."""
    concert_links = soup.find_all("a", href=re.compile(r"^/concerten/\d+"))
    events = []
    seen_hrefs = set()

    for link in concert_links:
        href = link.get("href", "")
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        text = link.get_text(" ", strip=True)
        parent_text = link.parent.get_text(" ", strip=True) if link.parent else text

        # Date: 'zo 15 feb 2026'
        date_match = re.search(
            r"((?:ma|di|wo|do|vr|za|zo)\s+\d+\s+(?:jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec)\s+\d{4})",
            text, re.I,
        )
        date = date_match.group(1) if date_match else ""

        # Time: '20:15 – 22:15'
        time_match = re.search(r"(\d{1,2}:\d{2})\s*.\s*(\d{1,2}:\d{2})", text)
        time_str = f"{time_match.group(1)} - {time_match.group(2)}" if time_match else ""

        # Price
        price_match = re.search(r"v\.a\.\s*..(\d+[,\.]\d+)", text)
        if price_match:
            price = f"v.a. EUR {price_match.group(1)}"
        elif "gratis" in text.lower():
            price = "Gratis"
        else:
            price = "TBA"

        # Hall
        hall = ""
        if "Grote Zaal" in text:
            hall = "Grote Zaal"
        elif "Kleine Zaal" in text:
            hall = "Kleine Zaal"

        # Title: between date and time, skip 'Luisteren' tag
        title = ""
        event_type = "Concert"
        if date and time_match:
            after_date = text[text.find(date) + len(date):].strip()
            if after_date.startswith("Luisteren"):
                after_date = after_date[len("Luisteren"):].strip()
                event_type = "Luisteren"
            title_end = after_date.find(time_match.group(1))
            if title_end > 0:
                title = after_date[:title_end].strip()

        # Refine event type
        if "gratis" in title.lower() or "lunchconcert" in title.lower():
            event_type = "Gratis Lunchconcert"
        elif "essentials" in title.lower():
            event_type = "Essentials"
        elif "festival" in title.lower():
            event_type = "Festival"
        elif "familieconcert" in title.lower():
            event_type = "Familieconcert"

        # Description (featured pieces/composers)
        desc_match = re.search(r"met onder andere\s+(.*?)(?:Informatie|Meer informatie)", text)
        desc = desc_match.group(1).strip() if desc_match else ""

        # Availability
        sold_out = "Uitverkocht" in parent_text
        last_tickets = "Laatste kaarten" in parent_text
        if sold_out:
            price += " [UITVERKOCHT]"
        elif last_tickets:
            price += " [Laatste kaarten]"

        url = BASE_URL + href
        full_date = f"{date}, {time_str}".strip(", ")

        events.append({
            "title": title,
            "event_type": event_type,
            "date": full_date,
            "hall": hall,
            "description": desc,
            "url": url,
            "price": price,
        })

    return events


def scrape_all_pages():
    """Scrape all pages of the Concertgebouw agenda."""
    all_events = []
    page = 1

    while True:
        url = f"{AGENDA_URL}?page={page}"
        print(f"Fetching page {page}... ", end="", flush=True)

        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"HTTP {r.status_code}, stopping.")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        events = parse_events_from_page(soup)

        if not events:
            print(f"0 events, stopping.")
            break

        all_events.extend(events)
        print(f"{len(events)} events (total: {len(all_events)})")

        page += 1
        time.sleep(0.5)  # be polite

    return all_events


def write_markdown(events, filename=None):
    if filename is None:
        filename = os.path.join(SCRIPT_DIR, "events.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Concertgebouw Events - Full Agenda\n\n")
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
    print("Scraping Concertgebouw agenda...")
    print("=" * 60)
    events = scrape_all_pages()
    print("=" * 60)
    print(f"\nTotal: {len(events)} events across all pages\n")
    write_markdown(events)
    write_csv(events)
    print("\nDone!")
