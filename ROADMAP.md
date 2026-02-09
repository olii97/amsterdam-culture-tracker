# Amsterdam Culture Tracker — Roadmap & Future Ideas

## Current State (as of Feb 2026)

### Done
- **Newsletter extraction** — Gmail → Claude Haiku → Supabase + Google Sheets
- **Venue scrapers** — Concertgebouw, Pakhuis de Zwijger, De Kleine Komedie, De Balie, Rode Hoed, Paradiso
- **Supabase backend** — events, venues, venue_visits, processed_emails
- **iOS app** — Events list, Event detail, Venue map, Venue detail, Visit log
- **Venue seeding** — 8 venues with addresses + coordinates

---

## Remaining Planned Phases

### Phase 4: Push Notifications
- Poll Supabase on app launch, show badge if new events since last check
- Or: Supabase Realtime for live updates when app is open
- Or: Full push via Edge Function → APNs (requires Apple Developer cert)

### Phase 5: Event Suggestions
- Track visit history + event type preferences
- Surface events matching your profile
- Optional: Claude API in Edge Function for smarter recommendations

---

## Future Functionality Ideas

### 1. Event Enrichment via Web Search

**Problem:** Scraped events often have sparse descriptions, missing genres, or no artist bio.

**Ideas:**

| Idea | Description | Effort |
|------|-------------|--------|
| **Artist/performer lookup** | For events with a clear artist name, web search for bio, image URL, social links. Store in `event_metadata` JSON or new columns. | Medium |
| **Wikipedia snippet** | Search "\[artist\] Wikipedia" and extract first paragraph for event detail view. | Low |
| **Genre/style tagging** | Search "\[event title\] genre" or "\[artist\] music style" to add tags (jazz, classical, electronic, etc.) for better filtering. | Medium |
| **Reviews/ratings** | Search for recent reviews (e.g. "[venue] [event] review") to show snippets like "★ ★ ★ ★ ★ Recommended" in the app. | Medium |
| **Similar events** | Search "concerts like [artist]" to suggest related upcoming events. | High |

**Implementation approach:**
- Add an enrichment step in the scraper pipeline (or a separate `enrich_events.py` job)
- Use a search API (Serper, Tavily, Bing, or scrape Google) to fetch snippets
- Optional: Use Claude to parse search results and extract structured data
- Store enriched data in new columns: `artist_bio`, `image_url`, `genre_tags`, `review_snippet`

---

### 2. Data Quality & Completeness

| Idea | Description |
|------|-------------|
| **Unified event deduplication** | Events from newsletter + scrapers may overlap. Use fuzzy matching on (title, date, venue) to merge duplicates. |
| **Price normalization** | Scrapers return "v.a. EUR 39,00" — parse to `price_min` / `price_max` columns for filtering "under €25". |
| **Time extraction** | Store `event_time` (HH:MM) when available; many events only have date. |
| **Cover images** | Fetch from event URL meta tags (`og:image`) or venue API. |

---

### 3. App UX Improvements

| Idea | Description |
|------|-------------|
| **Calendar integration** | "Add to Calendar" button for each event. |
| **Favourites / wishlist** | Mark events you're interested in, separate from visits. |
| **Share event** | Share link or summary to Messages/WhatsApp. |
| **Offline support** | Cache events for offline browsing. |
| **Search** | Full-text search on event title, description, venue. |
| **Date range filter** | "Next 7 days" / "This month" / custom range. |

---

### 4. More Venues & Data Sources

| Idea | Description |
|------|-------------|
| **Enable Muziekgebouw & Carré scrapers** | Already in VENUES but commented out. |
| **New venues** | Melkweg, Bimhuis, Stadsschouwburg, etc. |
| **iCal / RSS feeds** | Some venues publish iCal — parse and import. |
| **Ticketmaster / Eventbrite** | API or scrape for broader coverage (larger effort). |

---

### 5. Analytics & Insights

| Idea | Description |
|------|-------------|
| **Visit stats** | "You visited 12 venues this year", "Favourite venue: Paradiso". |
| **Event type breakdown** | Pie chart of concert vs debate vs theater attended. |
| **Export** | Export visit history as CSV or PDF for personal records. |

---

### 6. Automation & DevOps

| Idea | Description |
|------|-------------|
| **Scheduled scraper** | Run `scrape_all.py` daily via GitHub Actions or cron. |
| **Supabase Edge Function** | Trigger scraper from webhook (e.g. daily cron). |
| **Health check** | Alert if scraper fails or returns 0 events. |

---

## Enrichment via Web Search — Concrete Flow

```
Event in Supabase (title, venue, date, url, description)
        |
   enrich_events.py (batch job, runs after scrape)
        |
   For each event with sparse data:
   1. Extract artist/performers from title (or use Claude)
   2. Web search: "[artist] concert Amsterdam 2026"
   3. Parse results for: bio, image, genre
   4. Update event row: artist_bio, image_url, genre_tags
        |
   iOS app shows richer event cards (image, bio snippet)
```

**APIs to consider:**
- [Serper](https://serper.dev) — Google search API, simple JSON
- [Tavily](https://tavily.com) — AI-oriented search, good for structured extraction
- [DuckDuckGo](https://duckduckgo.com) — Free, via `duckduckgo-search` Python package

---

## Priority Suggestions

1. **Quick wins:** Calendar integration, favourites, search, date range filter
2. **High impact:** Event enrichment (image + bio) — makes the app feel polished
3. **Scale:** Scheduled scraper, enable more venues
4. **Later:** Full push notifications, advanced suggestions, analytics
