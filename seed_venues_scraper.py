"""
Seed venues that have scrapers but may not be in Supabase.
Run: python seed_venues_scraper.py
"""

import config
from cultural_venues_scraper.supabase_writer import get_supabase_client

# Venues with scrapers not in original seed_venues.sql
VENUES = [
    {"name": "Concertgebouw", "address": "Concertgebouwplein 10, 1071 LN Amsterdam", "latitude": 52.3558, "longitude": 4.8785, "website": "https://www.concertgebouw.nl"},
    {"name": "Pakhuis de Zwijger", "address": "Piet Heinkade 179, 1019 HC Amsterdam", "latitude": 52.3769, "longitude": 4.9220, "website": "https://dezwijger.nl"},
    {"name": "De Balie", "address": "Kleine-Gartmanplantsoen 10, 1017 RR Amsterdam", "latitude": 52.3631, "longitude": 4.8833, "website": "https://debalie.nl"},
    {"name": "Paradiso", "address": "Weteringschans 6-8, 1017 SG Amsterdam", "latitude": 52.3623, "longitude": 4.8839, "website": "https://paradiso.nl"},
]


def main():
    sb = get_supabase_client()
    if not sb:
        print("Supabase not configured (SUPABASE_URL, SUPABASE_KEY in .env)")
        return 1

    try:
        sb.table("venues").upsert(VENUES, on_conflict="name").execute()
        print(f"Upserted {len(VENUES)} venue(s) to Supabase")
        for v in VENUES:
            print(f"  - {v['name']}")
        return 0
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
