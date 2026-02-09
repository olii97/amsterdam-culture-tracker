"""
Run all venue scrapers and produce combined output.
Usage: python -m cultural_venues_scraper.scrape_all
   or: python cultural_venues_scraper/scrape_all.py
"""

import csv
import os
import importlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Register venue scrapers here — each must have scrape_all_pages(), write_markdown(), write_csv()
VENUES = [
    "concertgebouw",
    "pakhuis_de_zwijger",
    "de_kleine_komedie",
    "de_balie",
    "rode_hoed",
    "paradiso",
    # "muziekgebouw",
    # "carré",
]


def run_all():
    combined = []

    for venue in VENUES:
        print(f"\n{'='*60}")
        print(f"  {venue.upper()}")
        print(f"{'='*60}\n")

        module = importlib.import_module(f"cultural_venues_scraper.{venue}.scraper")
        events = module.scrape_all_pages()
        module.write_markdown(events)
        module.write_csv(events)

        # Tag each event with venue name for combined output
        for e in events:
            e["venue"] = venue.replace("_", " ").title()
        combined.extend(events)

        print(f"  -> {len(events)} events from {venue}")

    # Write combined CSV
    combined_csv = os.path.join(SCRIPT_DIR, "all_events.csv")
    with open(combined_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["venue", "title", "event_type", "date", "hall", "description", "url", "price"],
        )
        writer.writeheader()
        writer.writerows(combined)

    print(f"\n{'='*60}")
    print(f"Combined: {len(combined)} events from {len(VENUES)} venue(s)")
    print(f"Written to {combined_csv}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_all()
