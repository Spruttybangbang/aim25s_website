# Svenska AI-företag | AIM25S

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat&logo=django)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-4169E1?style=flat&logo=postgresql&logoColor=white)
![Railway](https://img.shields.io/badge/Deploy-Railway-0B0D0E?style=flat&logo=railway)

> Interaktiv databas över svenska företag som använder AI & ML

## Om Projektet

Detta projekt är en webbapp för att utforska svenska företag som arbetar med AI och maskininlärning. Databasen innehåller företagsinformation, AI-capabilities, bransch, och företagsdata från Bolagsverket.

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
│   │   │   └── public_view.css  # Main stylesheet
│   │   └── js/
│   │       └── public_view.js   # Main JavaScript
│   ├── templates/companies/  # HTML templates
│   │   ├── public_view.html  # Public-facing view
│   │   └── login.html        # Login page
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
