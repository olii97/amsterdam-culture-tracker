"""
Scrape all events from Rode Hoed agenda.
Uses requests + BeautifulSoup (SSR HTML parsing).
Single page with tile cards — no pagination needed.
Outputs to events.md and events.csv in this folder.
"""

import requests
from bs4 import BeautifulSoup
import re
import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://rodehoed.nl"
AGENDA_URL = f"{BASE_URL}/agenda/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
VENUE_NAME = "Rode Hoed"


def parse_events_from_page(soup):
    """Extract event data from the agenda page."""
    links = soup.find_all("a", href=re.compile(r"/programma/"))
    events = []
    seen_hrefs = set()

    for link in links:
        href = link.get("href", "")
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        article = link.find("article", class_="tile")
        if not article:
            continue

        content = article.find("div", class_="tile__content")
        if not content:
            continue

        # Info spans contain date, time, price in order
        info_spans = content.find_all("span", class_="tile__content__info")
        date_str = ""
        time_str = ""
        price = ""

        for span in info_spans:
            text = span.get_text(strip=True)
            if re.match(r"(ma|di|wo|do|vr|za|zo)\s", text):
                date_str = text
            elif re.match(r"\d{1,2}:\d{2}", text):
                time_str = text
            elif text.startswith("\u20ac") or text.startswith("€"):
                price = text.replace("\u20ac", "EUR").replace("€", "EUR").strip()

        if time_str:
            date_str = f"{date_str}, {time_str}"

        # Title
        title_el = content.find("h5", class_="tile__content__title")
        title = title_el.get_text(strip=True) if title_el else ""

        # Subtitle
        subtitle_el = content.find("h6", class_="tile__content__subtitle")
        subtitle = subtitle_el.get_text(strip=True) if subtitle_el else ""

        # Description
        excerpt_el = content.find("div", class_="tile__content__excerpt")
        excerpt = excerpt_el.get_text(strip=True) if excerpt_el else ""
        description = subtitle if subtitle else excerpt

        # Tags as event type
        tags_el = content.find("div", class_="tile__content__tags")
        if tags_el:
            tag_spans = tags_el.find_all("span")
            event_type = ", ".join(s.get_text(strip=True) for s in tag_spans)
        else:
            event_type = "Debat"

        # Sold out
        full_text = link.get_text()
        if "Uitverkocht" in full_text:
            price += " [UITVERKOCHT]" if price else "[UITVERKOCHT]"

        if not price:
            price = "TBA"

        events.append({
            "title": title,
            "event_type": event_type,
            "date": date_str,
            "hall": VENUE_NAME,
            "description": description,
            "url": href,
            "price": price,
        })

    return events


def scrape_all_pages():
    """Fetch the agenda page (single page, no pagination)."""
    print(f"Fetching {AGENDA_URL}... ", end="", flush=True)

    r = requests.get(AGENDA_URL, headers=HEADERS)
    if r.status_code != 200:
        print(f"HTTP {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    events = parse_events_from_page(soup)
    print(f"{len(events)} events")
    return events


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
