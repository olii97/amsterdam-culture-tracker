-- Seed venues that have scrapers (Concertgebouw, Pakhuis de Zwijger, De Balie, Paradiso)
-- Run in Supabase SQL Editor so the Map and venue picker show all 6 scraper venues.
-- Also run seed_venues.sql for De Kleine Komedie and Rode Hoed if not already done.

INSERT INTO venues (name, address, latitude, longitude, website, venue_type) VALUES
    ('Concertgebouw', 'Concertgebouwplein 10, 1071 LN Amsterdam', 52.3558, 4.8785, 'https://www.concertgebouw.nl', 'concert_hall'),
    ('Pakhuis de Zwijger', 'Piet Heinkade 179, 1019 HC Amsterdam', 52.3769, 4.9220, 'https://dezwijger.nl', 'cultural_center'),
    ('De Balie', 'Kleine-Gartmanplantsoen 10, 1017 RR Amsterdam', 52.3631, 4.8833, 'https://debalie.nl', 'cultural_center'),
    ('Paradiso', 'Weteringschans 6-8, 1017 SG Amsterdam', 52.3623, 4.8839, 'https://paradiso.nl', 'concert_hall')
ON CONFLICT (name) DO UPDATE SET
    address = EXCLUDED.address,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    website = EXCLUDED.website,
    venue_type = EXCLUDED.venue_type;
