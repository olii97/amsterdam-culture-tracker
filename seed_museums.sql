-- Seed 30 museumkaart-eligible Amsterdam museums
-- Run after migrations/001_phase0_schema.sql
-- Coordinates verified for Amsterdam area (52.35–52.39°N, 4.85–4.92°E)

INSERT INTO venues (name, address, latitude, longitude, website, venue_type, museumkaart) VALUES
    ('Rijksmuseum', 'Museumstraat 1, 1071 XX Amsterdam', 52.359998, 4.885219, 'https://www.rijksmuseum.nl', 'museum', true),
    ('Van Gogh Museum', 'Museumplein 6, 1071 DJ Amsterdam', 52.358416, 4.881076, 'https://www.vangoghmuseum.nl', 'museum', true),
    ('Stedelijk Museum Amsterdam', 'Museumplein 10, 1071 DJ Amsterdam', 52.357778, 4.879722, 'https://www.stedelijk.nl', 'museum', true),
    ('Anne Frank Huis', 'Westermarkt 20, 1016 DK Amsterdam', 52.375081, 4.883991, 'https://www.annefrank.org', 'museum', true),
    ('Het Scheepvaartmuseum', 'Kattenburgerplein 1, 1018 KK Amsterdam', 52.371801, 4.913501, 'https://www.hetscheepvaartmuseum.nl', 'museum', true),
    ('NEMO Science Museum', 'Oosterdok 2, 1011 VX Amsterdam', 52.374444, 4.912500, 'https://www.nemosciencemuseum.nl', 'museum', true),
    ('Amsterdam Museum', 'Amstel 51, 1018 EJ Amsterdam', 52.369500, 4.890200, 'https://www.amsterdammuseum.nl', 'museum', true),
    ('Museum Het Rembrandthuis', 'Jodenbreestraat 4, 1011 NK Amsterdam', 52.369167, 4.902222, 'https://www.rembrandthuis.nl', 'museum', true),
    ('Foam Fotografiemuseum', 'Keizersgracht 609, 1017 DS Amsterdam', 52.368833, 4.885556, 'https://www.foam.org', 'museum', true),
    ('Tropenmuseum / Wereldmuseum', 'Linnaeusstraat 2, 1092 CK Amsterdam', 52.365833, 4.918889, 'https://www.wereldmuseum.nl', 'museum', true),
    ('Allard Pierson', 'Oude Turfmarkt 127, 1012 GC Amsterdam', 52.369500, 4.890222, 'https://www.allardpierson.nl', 'museum', true),
    ('Museum Ons'' Lieve Heer op Solder', 'Oudezijds Voorburgwal 40, 1012 GE Amsterdam', 52.374444, 4.898056, 'https://www.opsolder.nl', 'museum', true),
    ('Het Grachtenhuis', 'Herengracht 386, 1016 CJ Amsterdam', 52.371778, 4.885556, 'https://www.hetgrachtenhuis.nl', 'museum', true),
    ('Museum Van Loon', 'Keizersgracht 672, 1017 ET Amsterdam', 52.364833, 4.883778, 'https://www.museumvanloon.nl', 'museum', true),
    ('Museum Willet-Holthuysen', 'Herengracht 605, 1017 CE Amsterdam', 52.365556, 4.899167, 'https://www.museumwilletholthuysen.nl', 'museum', true),
    ('Bijbels Museum', 'Herengracht 366, 1016 CH Amsterdam', 52.372778, 4.887778, 'https://www.bijbelsmuseum.nl', 'museum', true),
    ('Joods Historisch Museum', 'Nieuwe Amstelstraat 1, 1011 PL Amsterdam', 52.367500, 4.905556, 'https://www.jhm.nl', 'museum', true),
    ('Portugees-Israëlietische Synagoge', 'Mr. Visserplein 3, 1011 RD Amsterdam', 52.367222, 4.902778, 'https://www.portugesesynagoge.nl', 'museum', true),
    ('Verzetsmuseum Amsterdam', 'Plantage Kerklaan 61, 1018 CX Amsterdam', 52.368056, 4.911389, 'https://www.verzetsmuseum.org', 'museum', true),
    ('EYE Filmmuseum', 'IJpromenade 1, 1031 KT Amsterdam', 52.384444, 4.902222, 'https://www.eyefilm.nl', 'museum', true),
    ('Museum Het Schip', 'Spaarndammerplantsoen 140, 1013 XT Amsterdam', 52.392500, 4.868889, 'https://www.hetschip.nl', 'museum', true),
    ('Huis Marseille', 'Keizersgracht 401, 1016 EK Amsterdam', 52.367640, 4.884870, 'https://www.huismarseille.nl', 'museum', true),
    ('Hermitage Amsterdam', 'Amstel 51, 1018 EJ Amsterdam', 52.368889, 4.903889, 'https://www.hermitage.nl', 'museum', true),
    ('Paleis op de Dam', 'Nieuwezijds Voorburgwal 147, 1012 RJ Amsterdam', 52.373056, 4.892778, 'https://www.paleisamsterdam.nl', 'museum', true),
    ('De Nieuwe Kerk', 'Dam, 1012 NP Amsterdam', 52.373056, 4.892778, 'https://www.nieuwekerk.nl', 'museum', true),
    ('Museum van de Geest', '2e Constantijn Huygensstraat 25, 1054 DT Amsterdam', 52.356833, 4.871833, 'https://www.museumvandegeest.nl', 'museum', true),
    ('Museum Tot Zover', 'Kruislaan 124, 1099 GA Amsterdam', 52.352778, 4.908889, 'https://www.totzover.nl', 'museum', true),
    ('Stadsarchief Amsterdam', 'Vijzelstraat 32, 1017 HL Amsterdam', 52.364167, 4.888056, 'https://www.amsterdam.nl/stadsarchief', 'museum', true),
    ('Diamond Museum Amsterdam', 'Paulus Potterstraat 8, 1071 CZ Amsterdam', 52.358333, 4.879722, 'https://www.diamantmuseum.nl', 'museum', true),
    ('Micropia', 'Plantage Kerklaan 38-40, 1018 CZ Amsterdam', 52.366389, 4.908333, 'https://www.micropia.nl', 'museum', true)
ON CONFLICT (name) DO UPDATE SET
    address = EXCLUDED.address,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    website = EXCLUDED.website,
    venue_type = EXCLUDED.venue_type,
    museumkaart = EXCLUDED.museumkaart;
