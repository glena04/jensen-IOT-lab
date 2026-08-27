-- Jensen IoT Platform – SQL-uppgifter (milstolpe 1, avsnitt 4)
-- Kör med: docker compose exec db psql -U student -d jensen_iot

-- 1. Totalt antal mätningar.
--    COUNT(*) räknar alla rader i measurements och visar hur mycket data
--    simulatorn hittills har lyckats spara via POST /measurements.
SELECT COUNT(*) AS total_measurements
FROM measurements;

-- 2. Medeltemperatur över alla mätningar.
--    AVG() hoppar över NULL-värden. ROUND(..., 2) gör svaret läsbart,
--    eftersom kolumnen är NUMERIC(5,2).
SELECT ROUND(AVG(temperature), 2) AS avg_temperature
FROM measurements;

-- 3. Mätningar från de senaste 24 timmarna.
--    NOW() - INTERVAL '24 hours' ger tidsgränsen. created_at sätts av
--    databasen med DEFAULT NOW() vid varje INSERT.
SELECT id, device_id, temperature, humidity, battery, created_at
FROM measurements
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;