#!/usr/bin/env python3
"""
Test the full scraper with limited events per venue to avoid long runtime
"""

import sys
import importlib
from pathlib import Path

# Add cultural_venues_scraper to path
sys.path.insert(0, str(Path(__file__).parent / "cultural_venues_scraper"))

from scrape_all import write_to_supabase, VENUES

def run_limited_test():
    """Run scraper with limited events per venue"""
    combined = []
    max_events_per_venue = 10  # Limit to 10 events per venue for testing

    for venue in VENUES[:3]:  # Test first 3 venues only
        print(f"\n{'='*60}")
        print(f"  {venue.upper()} (LIMITED TEST)")
        print(f"{'='*60}\n")

        module = importlib.import_module(f"cultural_venues_scraper.{venue}.scraper")
        events = module.scrape_all_pages()
        
        # Limit events for testing
        events = events[:max_events_per_venue]
        
        # Tag each event with venue name for combined output
        for e in events:
            e["venue"] = venue.replace("_", " ").title()
        combined.extend(events)

        print(f"  -> {len(events)} events from {venue} (limited)")

    print(f"\nWriting {len(combined)} events to Supabase...")
    write_to_supabase(combined)
    
    print(f"\nCombined: {len(combined)} events from {len(VENUES[:3])} venue(s) (test mode)")

if __name__ == "__main__":
    run_limited_test()