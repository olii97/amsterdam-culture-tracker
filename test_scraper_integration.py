#!/usr/bin/env python3
"""
Test script to verify scraper Supabase integration works
"""

import sys
from pathlib import Path

# Add cultural_venues_scraper to path
sys.path.insert(0, str(Path(__file__).parent / "cultural_venues_scraper"))

from scrape_all import parse_dutch_date, write_to_supabase

def test_date_parsing():
    """Test the Dutch date parsing function"""
    test_dates = [
        "ma 9 feb 2026, 09:30 - 10:00",
        "zo 15 feb 2026, 15:00 - 17:00", 
        "vr 13 mrt 2026, 20:15 - 22:15"
    ]
    
    print("Testing date parsing:")
    for date_str in test_dates:
        parsed = parse_dutch_date(date_str)
        print(f"  '{date_str}' -> {parsed}")
    print()

def test_supabase_write():
    """Test writing a sample event to Supabase"""
    sample_events = [
        {
            "venue": "Test Venue",
            "title": "Test Event from Scraper Integration",
            "event_type": "Test",
            "date": "ma 9 feb 2026, 09:30 - 10:00",
            "hall": "Test Hall",
            "description": "This is a test event",
            "url": "https://example.com/test",
            "price": "v.a. EUR 25,00"
        }
    ]
    
    print("Testing Supabase write:")
    write_to_supabase(sample_events)

if __name__ == "__main__":
    test_date_parsing()
    test_supabase_write()
    print("Test completed!")