# Arkitekturdiagram – obligatorisk leverabel

Vad diagrammet visar

Diagrammet har tre delar: den lokala miljön i Docker Compose, CI-pipelinen och Kubernetes-demon.

Lokalt kör simulator-containern tre sensorer som var femte sekund skickar en POST /measurements till API:t. Lösningen skriver alltså mycket mer än den läser. API:t validerar mätningen, kontrollerar att deviceId finns i tabellen devices och skriver till PostgreSQL med parametriserad SQL. Redis används bara till senaste mätningen per sensor, under nyckeln latest:<deviceId>.

När jag pushar startar GitHub Actions, kör enhetstesterna och bygger API:ts Docker-image.

I Kubernetes håller en Deployment tre Pod-repliker av API:t, och en Service av typen NodePort ger dem en gemensam ingång. PostgreSQL, Redis och simulatorn är inte med i demon.

Viktigaste arkitekturvalen

Sensorerna pratar bara med API:t. Ingen klient går direkt mot databasen, så validering och felhantering ligger samlade på ett ställe och jag slipper sprida databasens lösenord.

Två lager med olika uppgifter. Historiken måste överleva omstarter och läsas med COUNT, AVG och tidsfilter, vilket passar en relationsdatabas. Senaste mätningen är ett litet värde som skrivs och läses ofta och alltid går att räkna fram igen, så den ligger i Redis med kort TTL.

Cache-aside. GET /devices/{id}/latest tittar först i Redis, och vid en miss läser jag från PostgreSQL och skriver tillbaka värdet. POST /measurements uppdaterar cachen efter en lyckad insert. Svarar inte Redis loggar jag felet men låter anropet gå vidare, eftersom mätningen redan är sparad.

PostgreSQL är sanningen. Ett tomt Redis gör bara första läsningen långsammare. Därför är cachen ritad som en genväg i diagrammet, inte som en egen datakälla.

Docker Compose lokalt. Fyra tjänster startar med ett kommando. Volymen postgres_data gör att mätningarna finns kvar efter docker compose down.

Källfil

Diagrammet ligger som PNG i docs/architecture.png.
