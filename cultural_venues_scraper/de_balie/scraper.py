"""
Scrape all events from De Balie programma.
Uses the WordPress REST API (wp-json) — no HTML parsing needed.
Custom post type: vo-programme with structured 'vo' field.
Outputs to events.md and events.csv in this folder.
"""

import requests
import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://debalie.nl"
AGENDA_URL = f"{BASE_URL}/programma/"
API_URL = f"{BASE_URL}/wp-json/wp/v2/vo-programme"
CATEGORY_URL = f"{BASE_URL}/wp-json/wp/v2/vo-programme-category"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
VENUE_NAME = "De Balie"


def fetch_categories():
    """Fetch category ID -> name mapping."""
    r = requests.get(f"{CATEGORY_URL}?per_page=100", headers=HEADERS)
    if r.status_code != 200:
        return {}
    from html import unescape
    return {c["id"]: unescape(c["name"]) for c in r.json()}


def scrape_all_pages():
    """Fetch all events from the WP REST API."""
    categories = fetch_categories()
    all_events = []
    page = 1

    while True:
        print(f"Fetching API page {page}... ", end="", flush=True)
        r = requests.get(
            API_URL,
            params={"per_page": 100, "page": page},
            headers=HEADERS,
        )
        if r.status_code != 200:
            print(f"HTTP {r.status_code}, stopping.")
            break

        items = r.json()
        if not items:
            print("0 events, stopping.")
            break

        for item in items:
            vo = item.get("vo", {})
            from html import unescape

            title = unescape(item.get("title", {}).get("rendered", ""))
            subtitle = vo.get("subtitle", "")

            # Date + time
            date_str = vo.get("date", "")
            time_str = vo.get("time_raw", "")
            if time_str:
                date_str = f"{date_str}, {time_str}"

            # Price
            price_val = vo.get("price")
            if price_val and price_val is not False:
                price = f"EUR {price_val}"
            else:
                price = "Gratis"

            # Event type from categories
            cat_ids = item.get("vo-programme-category", [])
            cat_names = [categories.get(cid, "") for cid in cat_ids if categories.get(cid)]
            event_type = ", ".join(cat_names) if cat_names else ""

            # Description
            description = vo.get("short_description", "") or vo.get("description", "")
            # Strip HTML tags from description
            import re
            description = re.sub(r"<[^>]+>", "", description).strip()
            # Truncate very long descriptions
            if len(description) > 200:
                description = description[:200] + "..."

            url = item.get("link", "")

            all_events.append({
                "title": title,
                "event_type": event_type,
                "date": date_str,
                "hall": VENUE_NAME,
                "description": subtitle if subtitle else description,
                "url": url,
                "price": price,
            })

        print(f"{len(items)} events (total: {len(all_events)})")

        # Check if there are more pages
        total_pages = int(r.headers.get("X-WP-TotalPages", 1))
        if page >= total_pages:
            break
        page += 1

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
    print(f"Scraping {VENUE_NAME} programma...")
    print("=" * 60)
    events = scrape_all_pages()
    print("=" * 60)
    print(f"\nTotal: {len(events)} events\n")
    write_markdown(events)
    write_csv(events)
    print("\nDone!")
