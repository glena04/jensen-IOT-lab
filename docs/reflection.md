<img width="1394" height="868" alt="architecture" src="https://github.com/user-attachments/assets/40475b5c-05b0-4591-971e-2f290df0b729" />

# Reflektionsdokument – obligatorisk leverabel

1. Varför API istället för direktåtkomst till PostgreSQL?
API:t fungerar som en grindvakt. All validering – som att kolla device_exists() och säkerställa att temperaturen är ett nummer – sker på ett ställe. Sensorerna behöver inte känna till databasens inloggningsuppgifter, och jag kan byta lagringslösning utan att uppdatera dem. Med direktåtkomst skulle varje sensor behöva hantera sin egen validering, vilket blir rörigt.

2. Varför stoppa felaktig data innan den sparas?
Felaktig data förstör statistik som medelvärden och kan utlösa falska larm. Det är också svårt att städa i efterhand. Genom att returnera ett 400-fel med tydliga meddelanden (t.ex. när sensor-003 skickar "ERROR") får avsändaren direkt feedback, vilket är mycket bättre än att behöva åtgärda korrupt historik.

3. Varför PostgreSQL för historiska mätvärden?
Mätvärden är strukturerade rader som behöver tillförlitlig lagring. PostgreSQL erbjuder starka datatyper, främmande nycklar för att förhindra föräldralösa poster och enkel SQL för tidsbaserade frågor. Volymen gör också att datan finns kvar även efter en omstart av containern.

4. Vad händer om Redis slutar fungera?
Inget kritiskt går sönder – systemet blir bara långsammare. Koden fångar Redis-fel, loggar dem och faller tillbaka på PostgreSQL. Jag testade detta med FLUSHDB; cachen fylls på igen vid nästa anrop. Redis är enbart till för hastighet.

5. Vad händer om PostgreSQL slutar fungera?
Då slutar hela systemet att fungera. Nya skrivningar misslyckas, enhetskontroller misslyckas och historikfrågor ger fel. Cachen kan möjligen hålla några värden en kort stund, men PostgreSQL är den enda sanna källan, så säkerhetskopior är avgörande.

6. Varför använda Docker Compose lokalt?
Det startar alla fyra tjänster med ett enda kommando, med konsekventa versioner och nätverk. depends_on ser till att API:t väntar på databasen, och init.sql skapar tabellerna automatiskt. Ingen behöver installera något lokalt, och städning görs med ett enda kommando.

7. Vad gör CI-pipelinen?
Vid varje push eller pull request checkar den ut koden, sätter upp Python, kör pytest och bygger Docker-avbilden. Detta fångar valideringsbuggar och byggfel tidigt – innan någon annan hinner klona repot.

8. Vad hände när du tog bort en Kubernetes Pod?
Poden gick in i Terminating, men Deploymenten skapade omedelbart en ny. Inom några sekunder var den nya Poden Running och klarade /health-kontrollen. Tjänsten var tillgänglig hela tiden – det är Kubernetes självläkande förmåga.

9. Varför förbättrar flera repliker tillgängligheten?
Med tre Pods finns ingen enskild felpunkt. Tjänsten skickar trafik endast till friska Pods, så om en dör fortsätter de andra att fungera. Eftersom API:t är tillståndslöst (tillståndet finns i PostgreSQL/Redis) kan vilken replik som helst hantera vilket anrop som helst.

10. När är Kubernetes överflödigt?
För den här labbmiljön – tre sensorer, låg trafik, ensam utvecklare – tillför det enorm komplexitet utan verklig nytta. Docker Compose fungerar utmärkt. Kubernetes lönar sig först när man behöver riktig hög tillgänglighet, skalning över flera noder och frekventa driftsättningar i produktion.
