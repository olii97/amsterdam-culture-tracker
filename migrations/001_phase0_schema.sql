-- Phase 0 Schema Migration
-- Add venue_type, museumkaart, exhibitions, saved_events
-- Run this in Supabase SQL Editor after schema.sql

-- 1. Extend venues table
ALTER TABLE venues ADD COLUMN IF NOT EXISTS venue_type TEXT;
-- 'theater', 'concert_hall', 'museum', 'cultural_center'
ALTER TABLE venues ADD COLUMN IF NOT EXISTS museumkaart BOOLEAN DEFAULT false;

-- Update existing venues with their type
UPDATE venues SET venue_type = 'theater' WHERE name IN ('De Kleine Komedie', 'Rode Hoed');
UPDATE venues SET venue_type = 'theater' WHERE name = 'Koninklijk Theater Carré';
UPDATE venues SET venue_type = 'concert_hall' WHERE name = 'Muziekgebouw aan ''t IJ';

-- 2. Exhibitions table (long-running, unlike one-night events)
CREATE TABLE IF NOT EXISTS exhibitions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id        BIGINT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT,
    start_date      DATE,
    end_date        DATE,
    url             TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(title, venue_id)
);
CREATE INDEX IF NOT EXISTS idx_exhibitions_venue ON exhibitions(venue_id);
CREATE INDEX IF NOT EXISTS idx_exhibitions_end_date ON exhibitions(end_date);

-- 3. Saved/bookmarked events
CREATE TABLE IF NOT EXISTS saved_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    saved_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(event_id)
);
CREATE INDEX IF NOT EXISTS idx_saved_events_event ON saved_events(event_id);

-- RLS for new tables
ALTER TABLE exhibitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all on exhibitions" ON exhibitions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on saved_events" ON saved_events FOR ALL USING (true) WITH CHECK (true);
