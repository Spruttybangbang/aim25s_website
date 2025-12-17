# Svenska AI-företag | AIM25S

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat&logo=django)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-4169E1?style=flat&logo=postgresql&logoColor=white)
![Railway](https://img.shields.io/badge/Deploy-Railway-0B0D0E?style=flat&logo=railway)

> Interaktiv databas över svenska företag som använder AI & ML

## Om Projektet

Detta projekt är en webbapp för att utforska svenska företag som arbetar med AI och maskininlärning. Databasen innehåller företagsinformation, AI-capabilities, bransch, och företagsdata från Bolagsverket.

### Utvecklingsmiljöer

**Production (`/`)**: Stabila releases med testet functionality
- Tillgänglig för alla användare
- Kör senaste stabila versionen (för närvarande v1.1)

**Staging (`/staging/`)**: Utvecklingsmiljö för kommande features
- Används för att testa nya features innan de går till production
- Kan innehålla experimentella funktioner (v1.2, v1.3, etc.)
- Endast tillgänglig när `DEBUG=True` (lokal utveckling)

## Version History

### Version 1.1 (2025-12-18)

**Database Insights Dashboard:**
- ✨ Klickbar databas-batterimätare som öppnar insights modal
- 📊 5 visualiserade metrics med Chart.js (geografisk spridning, bransch, tillämpningar, omsättning, anställda)
- 📈 Scrollbar dashboard med editorial design
- 🔢 Översikt visar: 613 företag totalt, 37 variabler data, 22 817 celler data
- ℹ️ Hjälptext med animerad pil: "Klicka här för mer datainfo"

**Filter & Display Improvements:**
- 🔍 Multi-select filter för alla kategorier (bransch, anställda, omsättning, tillämpningar)
- 📦 Expanderbara/minimerade filter sections med smooth animationer
- 🏷️ Kolumn "AI/ML-tillämpning" ersätter AI-inriktning i tabellen
- 🎨 Tillämpnings-tags transparenta by default, gröna vid hover
- 🖱️ Klickbara bransch- och tillämpnings-tags fungerar som filter
- 🧹 "Rensa alla filter" minimerar automatiskt alla filter-sektioner
- 📱 Förbättrad UX med Material Design easing curves

**UI/UX Polering:**
- 🎯 Underrubrik på separat rad från huvudrubrik
- 🔍 "AI/ML-tillämpning" filter stängt by default (som andra filter)
- 🔤 Större batterimätare-text (50% större för bättre läsbarhet)
- 🎨 Global meny hover-färger: hjälp (röd), lägg till företag (grön), logga ut (svart)
- 📖 Hjälp-modal uppdaterad med 6 AI/ML-tillämpningskategorier
- 📋 Förkortad och tydligare version history modal
- 🗑️ Företags-modal utan AI-inriktning sektion

**Technical Improvements:**
- ⚡ Server-side filtering för alla tillämpningar (visar alla matchande företag, inte bara 50)
- 🔄 Optimerad boolean-konvertering för Google Sheets sync (STORSTOCKHOLM + tillämpningar)
- 💾 6 nya tillämpningsfält i databasen:
  - Optimering & Automation
  - Språk & Ljud
  - Prognos & Prediktion
  - Infrastruktur & Data
  - Insikt & Analys
  - Visuell AI
- 🎭 Smooth filter-animationer med cubic-bezier easing (0.4s duration)

### Features

- 🔍 Sökfunktion med realtidsfiltrering
- 🏷️ Filtrera på AI-inriktning och bransch
- 📊 Batterimätare för dataupptäckt
- 🎲 "Jag känner mig lycklig" - slumpmässigt företag med confetti
- 📝 Rapportera fel och föreslå nya företag
- 🔄 Google Sheets-synkronisering (admin)
- 🎨 Editorial newspaper design aesthetic

## Tech Stack

- **Backend:** Django 5.2
- **Database:** SQLite (dev), PostgreSQL (production)
- **Frontend:** Vanilla JavaScript + CSS
- **Hosting:** Railway
- **Design:** Editorial newspaper aesthetic (Playfair Display, Source Serif 4, Inter)

## Setup - Lokal Utveckling

### 1. Klona projektet

```bash
git clone <repo-url>
cd aim-internships
```

### 2. Skapa virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# eller: venv\Scripts\activate  # Windows
```

### 3. Installera dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurera environment variables

```bash
cp .env.example .env
# Redigera .env med dina nycklar
```

**Nödvändiga environment variables:**
- `SECRET_KEY` - Django secret key
- `DEBUG` - True för dev, False för production
- `GOOGLE_SHEETS_SPREADSHEET_ID` - För Google Sheets sync
- `GOOGLE_SHEETS_CREDENTIALS` - Service account credentials JSON

### 5. Migrera databasen

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Initiera public view configuration

```bash
python init_public_view.py
```

Detta skapar initial konfiguration för vilka kolumner som visas i public view och vilka filter som är aktiva.

### 7. Skapa superuser (admin)

```bash
python manage.py createsuperuser
```

### 8. Starta dev server

```bash
python manage.py runserver
```

Öppna: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Staging Environment (Lokal Testmiljö)

Projektet har en inbyggd staging-miljö för att testa ändringar innan de går live.

### Vad är Staging?

Staging är en **separat URL** (`/staging/`) som endast fungerar lokalt när `DEBUG=True`. Den använder kopior av produktionsfilerna så du kan experimentera fritt utan att påverka live-siten.

### Hur Fungerar Det?

**Staging består av:**
- `/staging/` - Separat URL route (endast lokalt)
- `public_view_staging.html` - Kopia av produktionens template
- `public_view_staging.css` - Kopia av produktionens CSS
- `public_view_staging.js` - Kopia av produktionens JavaScript

**Database-koppling:**
Staging använder **samma databaskonfiguration** som resten av applikationen:
- **Med `DATABASE_URL` i .env** → Staging använder Railway PostgreSQL (samma som live)
- **Utan `DATABASE_URL`** → Staging använder lokal SQLite

### Använda Staging

**1. Öppna staging lokalt:**
```bash
# Kontrollera att DEBUG=True i .env
python manage.py runserver
```
Gå till: [http://127.0.0.1:8000/staging/](http://127.0.0.1:8000/staging/)

Du ser en orange banner: 🚧 STAGING ENVIRONMENT - Endast synlig lokalt

**2. Gör ändringar:**
Redigera staging-filerna:
- `companies/templates/companies/public_view_staging.html`
- `companies/static/companies/css/public_view_staging.css`
- `companies/static/companies/js/public_view_staging.js`

Ladda om `/staging/` för att se dina ändringar.

**3. Testa mot riktig data (valfritt):**
Om du vill testa med Railway-datan, lägg till i `.env`:
```
DATABASE_URL=postgresql://postgres:...@railway.app/railway
```

**4. Promovera till produktion:**
När du är nöjd med staging, kopiera filerna:

```bash
# Backup först (säkerhet!)
cp companies/templates/companies/public_view.html companies/templates/companies/public_view.backup.html
cp companies/static/companies/css/public_view.css companies/static/companies/css/public_view.backup.css
cp companies/static/companies/js/public_view.js companies/static/companies/js/public_view.backup.js

# Kopiera staging → produktion
cp companies/templates/companies/public_view_staging.html companies/templates/companies/public_view.html
cp companies/static/companies/css/public_view_staging.css companies/static/companies/css/public_view.css
cp companies/static/companies/js/public_view_staging.js companies/static/companies/js/public_view.js
```

**5. Rensa staging-markeringar:**
Öppna `companies/templates/companies/public_view.html` och:
- Ta bort `STAGING - ` från `<title>` tag
- Ta bort den orange staging-bannern
- Uppdatera CSS-referens från `public_view_staging.css` → `public_view.css`
- Uppdatera JS-referens från `public_view_staging.js` → `public_view.js`

**6. Deploy till Railway:**
```bash
git add companies/templates/companies/public_view.html \
        companies/static/companies/css/public_view.css \
        companies/static/companies/js/public_view.js

git commit -m "Update public_view with new features from staging"
git push origin main
```

### Viktiga Detaljer

- ✅ **Endast lokalt** - Staging fungerar bara när `DEBUG=True` (aldrig på Railway)
- ✅ **Inte i git** - Staging-filer är listade i `.gitignore` och pushas inte till GitHub
- ✅ **Samma API** - Staging använder samma backend-endpoints som produktionen
- ⚠️ **Database** - Om du använder Railway-databasen, påverkar staging-actions (felanmälningar etc.) live-datan

### Felsökning

**Problem:** `/staging/` ger 404
**Lösning:** Kontrollera att `DEBUG=True` i din `.env` fil

**Problem:** Staging ser identisk ut med produktionen
**Lösning:** Kontrollera att staging-filerna har orange banner och "STAGING" i titeln

**Problem:** Ändringar syns inte
**Lösning:** Ladda om sidan med Cmd+Shift+R (hard refresh) för att cleara cache

## Deployment (Railway)

### 1. Förbered projektet

- Kontrollera att `requirements.txt` innehåller alla dependencies
- Konfigurera environment variables i Railway dashboard
- Sätt upp PostgreSQL database i Railway

### 2. Konfigurera Environment Variables

I Railway dashboard, lägg till:

```
SECRET_KEY=<generera en säker key>
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
DATABASE_URL=<railway tillhandahåller denna automatiskt>
GOOGLE_SHEETS_SPREADSHEET_ID=<ditt spreadsheet ID>
GOOGLE_SHEETS_CREDENTIALS=<din service account JSON>
```

### 3. Deploy

```bash
git push origin main
```

Railway deployas automatiskt från GitHub när du pushar till main branch.

### 4. Initiera produktion-databasen

Efter första deployment, kör:

```bash
# Via Railway CLI eller dashboard
python manage.py migrate
python init_public_view.py
python manage.py createsuperuser
```

### 5. Synkronisera data från Google Sheets

```bash
python manage.py sync_sheets
```

Detta ska köras regelbundet (kan schemaläggas via cron eller Railway scheduled job).

## Admin Panel

Logga in på `/admin/` med superuser credentials för att:

- **Hantera företag** - CRUD operationer på AICompany-modellen
- **Konfigurera public view** - Välj vilka kolumner som ska visas och vilka filter som ska vara aktiva
- **Synkronisera med Google Sheets** - Importera och uppdatera företagsdata
- **Granska felrapporter** - Se och hantera ErrorReport-inlämningar
- **Granska företagsförslag** - Se och godkänn CompanySuggestion-inlämningar

### Konfigurera Public View

1. Gå till Admin → Public View Configurations
2. Redigera den aktiva konfigurationen
3. Välj vilka kolumner som ska visas:
   - `display_columns` - JSON-lista med kolumnnamn
4. Välj vilka filter som ska vara aktiva:
   - `enable_ai_capabilities_filter` - AI-inriktning filter
   - `enable_bransch_filter` - Bransch filter

## API Endpoints

Applikationen exponerar följande JSON API endpoints:

- `GET /api/companies/` - Lista företag (paginerad)
  - Query params: `search`, `page`, `per_page`, `ai_capability`, `bransch`
- `GET /api/columns/` - Hämta synliga kolumner från konfiguration
- `GET /api/filter-options/` - Hämta tillgängliga filter-alternativ
- `POST /api/report-error/` - Rapportera fel
  - Body: `{ "company_id": 123, "company_name": "...", "error_type": "...", "description": "...", "contact_email": "..." }`
- `POST /api/suggest-company/` - Föreslå nytt företag
  - Body: `{ "company_name": "...", "website": "...", "description": "...", "contact_email": "..." }`

## Google Sheets Sync

Projektet kan synkronisera företagsdata från Google Sheets.

### Setup

1. Skapa ett Google Cloud project
2. Aktivera Google Sheets API
3. Skapa en Service Account och ladda ner credentials JSON
4. Dela ditt Google Sheet med service account email
5. Lägg till credentials i `.env`:

```
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_CREDENTIALS='{"type": "service_account", ...}'
```

### Synkronisera

```bash
python manage.py sync_sheets
```

Detta kommando:
- Läser data från Google Sheets
- Uppdaterar befintliga företag
- Skapar nya företag
- Loggar alla ändringar

**Rekommenderad frekvens:** Dagligen via scheduled job

## Projektstruktur

```
aim-internships/
├── ai_companies_admin/       # Django project settings
│   ├── settings.py           # Huvudinställningar
│   ├── urls.py               # URL routing
│   └── wsgi.py               # WSGI application
├── companies/                # Main app
│   ├── management/
│   │   └── commands/
│   │       └── sync_sheets.py  # Google Sheets sync command
│   ├── migrations/           # Database migrations
│   ├── static/companies/     # Static files
│   │   ├── css/
│   │   │   ├── public_view.css         # Production stylesheet
│   │   │   └── public_view_staging.css # Staging stylesheet (gitignored)
│   │   └── js/
│   │       ├── public_view.js          # Production JavaScript
│   │       └── public_view_staging.js  # Staging JavaScript (gitignored)
│   ├── templates/companies/  # HTML templates
│   │   ├── public_view.html         # Production view
│   │   ├── public_view_staging.html # Staging view (gitignored)
│   │   └── login.html               # Login page
│   ├── admin.py              # Admin configuration
│   ├── models.py             # Database models
│   ├── views.py              # Views & API endpoints
│   └── apps.py               # App configuration
├── _new_data_source/         # Google Sheets sync data
├── archive/                  # Archived dev files (not in git)
├── .env                      # Environment variables (not in git)
├── .env.example              # Environment variables template
├── .gitignore
├── init_public_view.py       # Initialize public view config
├── manage.py                 # Django management script
├── Procfile                  # Railway deployment
├── railway.toml              # Railway configuration
├── README.md
└── requirements.txt          # Python dependencies
```

## Databas-modeller

### AICompany

Huvudmodellen för företag med AI-capabilities:

- Företagsinformation (namn, website, beskrivning)
- AI-capabilities (kommaseparerad sträng)
- Bransch (kommaseparerad sträng)
- Bolagsverket-data (org.nr, adress, antal anställda, omsättning, etc.)
- Location data (kommun, län, Stor-Stockholm boolean)

### PublicViewConfiguration

Konfigurerar vad som visas i public view:

- `display_columns` - JSON-lista med kolumnnamn att visa
- `enable_ai_capabilities_filter` - Boolean för AI-filter
- `enable_bransch_filter` - Boolean för bransch-filter
- `is_active` - Endast en config kan vara aktiv åt gången

### ErrorReport

Felrapporter från användare:

- `company` - Foreign key till AICompany
- `error_type` - Val mellan olika feltyper
- `description` - Fri text beskrivning
- `contact_email` - Valfr kontakt
- `resolved` - Boolean
- `admin_notes` - Anteckningar från admin

### CompanySuggestion

Förslag på nya företag från användare:

- `company_name`, `website`, `description`
- `contact_email` - Valfri kontakt
- `status` - pending/approved/rejected
- `admin_notes`

## Testing

### Manuell Testing Checklist

**Public View (`/`):**
- [ ] Sökfunktion fungerar
- [ ] Filter (AI-capabilities och bransch) fungerar
- [ ] Pagination fungerar
- [ ] "Jag känner mig lycklig" button fungerar + confetti
- [ ] Batterimätare uppdateras korrekt
- [ ] Company modal öppnas och visar korrekt data
- [ ] Tags i modal är klickbara och filtrerar
- [ ] Rapportera fel-funktion fungerar
- [ ] Föreslå företag-funktion fungerar
- [ ] Responsive design (mobile, tablet, desktop)

**Login View (`/login/`):**
- [ ] Login fungerar med giltiga credentials
- [ ] Felmeddelande visas vid ogiltiga credentials
- [ ] Redirect till `/companies/` efter login

**Admin Area (`/admin/`):**
- [ ] Admin kan logga in
- [ ] Companies CRUD fungerar
- [ ] PublicViewConfiguration fungerar
- [ ] ErrorReport admin fungerar
- [ ] CompanySuggestion admin fungerar

## Contributing

1. Fork projektet
2. Skapa feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push till branch (`git push origin feature/AmazingFeature`)
5. Öppna Pull Request

## License

Detta projekt är skapat för AIM25S.

## Kontakt

För frågor kontakta: [din kontaktinfo]

---

**För AIM25S, av AIM25S**
