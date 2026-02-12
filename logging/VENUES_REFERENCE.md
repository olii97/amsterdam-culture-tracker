# Venues reference — what the app shows

The app **Map** and **venue picker** (and visit logging) use only rows from the Supabase **`venues`** table. If you only see Concertgebouw and De Balie, your `venues` table currently has only those two (or only they match what you expect).

---

## Venue data in this repo

| Source | What it adds |
|--------|----------------|
| **seed_venues.sql** | 4 venues: **De Kleine Komedie**, **Rode Hoed**, Koninklijk Theater Carré, Muziekgebouw aan 't IJ |
| **seed_museums.sql** | 30 museums (Rijksmuseum, Van Gogh, Stedelijk, Anne Frank, etc.) — run after `001_phase0_schema.sql` |
| **seed_venues_scraper.py** | 4 venues used by the scrapers: **Concertgebouw**, **Pakhuis de Zwijger**, **De Balie**, **Paradiso** |

The **scraper** writes events with `source_name` like:  
`Concertgebouw`, `Pakhuis De Zwijger`, `De Balie`, `Paradiso`, `De Kleine Komedie`, `Rode Hoed`.

So for all 6 scraper venues to appear on the map you need those 6 names in `venues`. That means running both **seed_venues.sql** (adds De Kleine Komedie, Rode Hoed) and **seed_venues_scraper.py** (adds Concertgebouw, Pakhuis de Zwijger, De Balie, Paradiso). Carré and Muziekgebouw are in seed_venues but not in the current scraper list.

---

## How to get all 6 scraper venues in the app

1. **Run in Supabase SQL Editor** (in this order if starting fresh):
   - `schema.sql`
   - `migrations/001_phase0_schema.sql` (if you use exhibitions/saved_events)
   - `seed_venues.sql`
   - `seed_museums.sql` (optional; for museums map filter)

2. **Run the Python seeder** (adds the 4 scraper-only venues):
   ```bash
   source venv/bin/activate
   python seed_venues_scraper.py
   ```

After that, `venues` will have at least: De Kleine Komedie, Rode Hoed, Carré, Muziekgebouw (from SQL) + Concertgebouw, Pakhuis de Zwijger, De Balie, Paradiso (from Python). So you’ll see **all 6 scraper venues** on the map and in the venue picker.

---

## Check what’s in Supabase now

In Supabase **SQL Editor** run:

```sql
SELECT id, name, latitude, longitude FROM venues ORDER BY name;
```

That lists every row in `venues`. If you only see Concertgebouw and De Balie, run the steps above to add the rest.
