-- Phase 0.1 Schema Migration
-- Add scraper_runs operational logging table for daily scrape monitoring
-- Run this in Supabase SQL Editor after existing migrations.

CREATE TABLE IF NOT EXISTS scraper_runs (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source                          TEXT NOT NULL,
    status                          TEXT NOT NULL DEFAULT 'running',
    started_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at                     TIMESTAMPTZ,
    total_scraped                   INTEGER NOT NULL DEFAULT 0,
    parsed_rows                     INTEGER NOT NULL DEFAULT 0,
    skipped_unparseable_dates       INTEGER NOT NULL DEFAULT 0,
    new_events_estimated            INTEGER NOT NULL DEFAULT 0,
    error_message                   TEXT,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scraper_runs_started_at ON scraper_runs(started_at DESC);

ALTER TABLE scraper_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all on scraper_runs" ON scraper_runs FOR ALL USING (true) WITH CHECK (true);
