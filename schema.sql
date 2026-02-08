-- Amsterdam Culture Tracker — Supabase Schema
-- Run this in the Supabase SQL Editor to create all tables.

-- Events (extracted event-dates from newsletters)
CREATE TABLE events (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name     TEXT,
    source_type     TEXT,
    event_title     TEXT NOT NULL,
    event_type      TEXT,
    event_date      DATE,
    description     TEXT,
    url             TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(event_title, event_date)
);
CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_events_source ON events(source_name);

-- Venues (for map + tracking)
CREATE TABLE venues (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    address         TEXT,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    website         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Venue visits (track when you went)
CREATE TABLE venue_visits (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    venue_id        BIGINT REFERENCES venues(id),
    visited_at      DATE NOT NULL,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_venue_visits_venue ON venue_visits(venue_id);

-- Processed newsletters (replaces processed_ids.json)
CREATE TABLE processed_emails (
    gmail_id        TEXT PRIMARY KEY,
    subject         TEXT,
    sender          TEXT,
    processed_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (allow anon read, authenticated write)
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE venue_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_emails ENABLE ROW LEVEL SECURITY;

-- Policies: allow anon key full access (single-user app)
CREATE POLICY "Allow all on events" ON events FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on venues" ON venues FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on venue_visits" ON venue_visits FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on processed_emails" ON processed_emails FOR ALL USING (true) WITH CHECK (true);
