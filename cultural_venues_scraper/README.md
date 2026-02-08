# Cultural Venues Scraper

Extracts events from Amsterdam cultural venue websites into standardized MD and CSV files.

## How It Works

Each venue has its own scraper under `cultural_venues_scraper/<venue_name>/scraper.py` that uses **requests + BeautifulSoup** to parse server-side rendered HTML. No browser automation needed.

## Output Columns

Every scraper produces the same 7 columns:

| Column | Content |
|---|---|
| `title` | Event name |
| `event_type` | Category (Concert, Film, Debate, Festival, etc.) |
| `date` | Date and time as displayed on the site |
| `hall` | Room/zaal name within the venue |
| `description` | Short description, subtitle, or featured artists |
| `url` | Full URL to the event detail page |
| `price` | Price, "Gratis", or "TBA". May include [UITVERKOCHT] or [Laatste kaarten] |

## Venues

| Venue | Events | Pagination |
|---|---|---|
| Concertgebouw | ~300 | `?page=N` |
| Pakhuis de Zwijger | ~34 | `/agenda/start/YYYY/MM` |

## Usage

```bash
# Run all scrapers
python -m cultural_venues_scraper.scrape_all

# Run a single venue
python -m cultural_venues_scraper.concertgebouw.scraper
python -m cultural_venues_scraper.pakhuis_de_zwijger.scraper
```

## Adding a New Venue

1. Create folder: `cultural_venues_scraper/<venue_name>/`
2. Add `__init__.py` (empty)
3. Add `scraper.py` with three required functions:
   - `scrape_all_pages()` - returns list of event dicts
   - `write_markdown(events)` - writes events.md
   - `write_csv(events)` - writes events.csv
4. Add venue name to `VENUES` list in `scrape_all.py`

## Folder Structure

```
cultural_venues_scraper/
  __init__.py
  scrape_all.py            # Runs all venues, outputs all_events.csv
  all_events.csv           # Combined output
  concertgebouw/
    __init__.py
    scraper.py
    events.md
    events.csv
  pakhuis_de_zwijger/
    __init__.py
    scraper.py
    events.md
    events.csv
```
