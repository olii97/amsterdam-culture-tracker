-- Seed Amsterdam cultural venues
-- Run this in Supabase SQL Editor after schema.sql

INSERT INTO venues (name, address, latitude, longitude, website) VALUES
    ('De Kleine Komedie', 'Amstel 56-58, Amsterdam', 52.3667, 4.8981, 'https://dekleinekomedie.nl'),
    ('Rode Hoed', 'Keizersgracht 102, Amsterdam', 52.3761, 4.8867, 'https://rodehoed.nl'),
    ('Koninklijk Theater Carré', 'Amstel 115-125, Amsterdam', 52.3627, 4.9022, 'https://carre.nl'),
    ('Muziekgebouw aan ''t IJ', 'Piet Heinkade 1, Amsterdam', 52.3784, 4.9125, 'https://muziekgebouw.nl')
ON CONFLICT (name) DO NOTHING;
