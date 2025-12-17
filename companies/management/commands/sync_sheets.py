from django.core.management.base import BaseCommand
from django.db import transaction
from companies.models import AICompany
import requests
import os

# Ladda miljövariabler från .env om filen finns
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv är inte installerat, fortsätt ändå
    pass


class Command(BaseCommand):
    help = 'Synkroniserar AICompany-data från Google Sheets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sheet-id',
            type=str,
            required=True,
            help='Google Sheet ID (från URL:en)'
        )
        parser.add_argument(
            '--range',
            type=str,
            default='Sheet1!A:BN',  # A till BN (64 kolumner)
            help='Sheet range (default: Sheet1!A:BN)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Visa vad som skulle hända utan att göra ändringar'
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Hoppa över bekräftelseprompts'
        )

    def fetch_sheet_data(self, sheet_id, range_name):
        """
        Hämtar data från Google Sheets (med API key)
        """
        try:
            # Hämta API key från miljövariabel
            api_key = os.environ.get('GOOGLE_SHEETS_API_KEY')

            if not api_key:
                self.stdout.write(self.style.ERROR(
                    'GOOGLE_SHEETS_API_KEY miljövariabel saknas!'
                ))
                self.stdout.write(self.style.ERROR(
                    'Sätt miljövariabeln: export GOOGLE_SHEETS_API_KEY="din-api-key"'
                ))
                self.stdout.write(self.style.ERROR(
                    'Se GOOGLE_SHEETS_SYNC.txt för instruktioner om hur du skaffar en API key.'
                ))
                return None

            # Google Sheets API v4 endpoint med API key
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_name}"
            params = {'key': api_key}

            response = requests.get(url, params=params)

            if response.status_code == 403:
                self.stdout.write(self.style.ERROR(
                    'HTTP 403: API key ogiltig eller saknar behörighet'
                ))
                self.stdout.write(self.style.ERROR(
                    'Kontrollera att du har aktiverat Google Sheets API i Google Cloud Console'
                ))
                self.stdout.write(self.style.ERROR(
                    'Se GOOGLE_SHEETS_SYNC.txt för instruktioner.'
                ))
                return None
            elif response.status_code == 400:
                self.stdout.write(self.style.ERROR(
                    'HTTP 400: Felaktig förfrågan till Google Sheets API'
                ))
                # Visa detaljerat felmeddelande från Google
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error'].get('message', 'Inget felmeddelande')
                        self.stdout.write(self.style.ERROR(f'Google säger: {error_msg}'))

                        # Visa status om tillgänglig
                        if 'status' in error_data['error']:
                            self.stdout.write(self.style.ERROR(f'Status: {error_data["error"]["status"]}'))
                except:
                    pass

                self.stdout.write(self.style.ERROR(
                    'Kontrollera att:'
                ))
                self.stdout.write(self.style.ERROR(
                    '  1. Google Sheets API är aktiverad i Google Cloud Console'
                ))
                self.stdout.write(self.style.ERROR(
                    '  2. API keyen är korrekt (inga extra mellanslag eller radbrytningar)'
                ))
                self.stdout.write(self.style.ERROR(
                    '  3. Sheet ID är korrekt'
                ))
                return None
            elif response.status_code != 200:
                self.stdout.write(self.style.ERROR(
                    f'Fel vid hämtning från Google Sheets: HTTP {response.status_code}'
                ))
                self.stdout.write(self.style.ERROR(
                    'Kontrollera att Sheet ID är korrekt och att sheetet är publikt.'
                ))
                return None

            data = response.json()
            values = data.get('values', [])

            if not values:
                self.stdout.write(self.style.ERROR('Inga data hittades i sheetet'))
                return None

            # Första raden = headers
            headers = values[0]
            # Fixa case sensitivity för ID-kolumnen (Google Sheets använder "ID", Django model använder "id")
            headers = ['id' if h == 'ID' else h for h in headers]
            rows = values[1:]

            return {'headers': headers, 'rows': rows}

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(
                f'Fel vid hämtning från Google Sheets: {str(e)}'
            ))
            self.stdout.write(self.style.ERROR(
                'Kontrollera din internetanslutning och att Sheet ID är korrekt.'
            ))
            return None

    def parse_row(self, headers, row):
        """
        Konverterar en rad till dict med rätt fältnamn
        """
        # Map Google Sheets tillämpning column names to model field names
        tillampning_mapping = {
            'Optimering & Automation': 'TILLAMPNING_OPTIMERING_AUTOMATION',
            'Språk & Ljud': 'TILLAMPNING_SPRAK_LJUD',
            'Prognos & Prediktion': 'TILLAMPNING_PROGNOS_PREDIKTION',
            'Infrastruktur & Data': 'TILLAMPNING_INFRASTRUKTUR_DATA',
            'Insikt & Analys': 'TILLAMPNING_INSIKT_ANALYS',
            'Visuell AI': 'TILLAMPNING_VISUELL_AI',
        }

        row_dict = {}
        for i, header in enumerate(headers):
            value = row[i] if i < len(row) else None

            # Map tillämpning column names
            field_name = tillampning_mapping.get(header, header)

            # Hantera tomma värden
            if value == '' or value is None:
                row_dict[field_name] = None
            # Boolean-konvertering för STORSTOCKHOLM och TILLAMPNING fields
            elif field_name == 'STORSTOCKHOLM' or field_name.startswith('TILLAMPNING_'):
                row_dict[field_name] = self.parse_boolean(value)
            # ID ska vara integer
            elif field_name == 'id':
                try:
                    row_dict[field_name] = int(value) if value else None
                except ValueError:
                    row_dict[field_name] = None
            else:
                row_dict[field_name] = value

        return row_dict

    def parse_boolean(self, value):
        """
        Konverterar olika boolean-representationer till True/False
        """
        if value is None or value == '':
            return None

        true_values = ['TRUE', '1', 'YES', 'JA', 'Y', 'J', 'True', 'true']
        return str(value).strip() in true_values

    def detect_changes(self, sheet_data):
        """
        Analyserar vilka rader som ska skapas/uppdateras
        """
        headers = sheet_data['headers']
        rows = sheet_data['rows']

        to_create = []
        to_update = []
        conflicts = []
        missing_id_rows = []
        new_columns = []

        # Detektera nya kolumner
        # Inkludera både field names (Python-attribut) OCH db_column names (databas-kolumner)
        model_fields = set()
        for f in AICompany._meta.get_fields():
            model_fields.add(f.name)  # Python-attributnamn (t.ex. AI_FÖRMÅGA_V2)
            # Lägg till db_column om det finns (t.ex. AI-FÖRMÅGA_V2)
            if hasattr(f, 'db_column') and f.db_column:
                model_fields.add(f.db_column)

        sheet_columns = set(headers)
        new_columns = sheet_columns - model_fields

        for row_num, row in enumerate(rows, start=2):  # +2 för Excel-radnummer
            row_dict = self.parse_row(headers, row)

            # Hantera rader utan ID
            if not row_dict.get('id'):
                missing_id_rows.append({
                    'row_num': row_num,
                    'data': row_dict
                })
                continue

            company_id = row_dict['id']

            try:
                existing = AICompany.objects.get(id=company_id)

                # Kolla om det finns konflikter
                has_conflict = self.check_conflicts(existing, row_dict)

                if has_conflict:
                    conflicts.append({
                        'id': company_id,
                        'row_num': row_num,
                        'existing': existing,
                        'new_data': row_dict
                    })
                else:
                    to_update.append({
                        'id': company_id,
                        'row_num': row_num,
                        'data': row_dict
                    })

            except AICompany.DoesNotExist:
                to_create.append({
                    'id': company_id,
                    'row_num': row_num,
                    'data': row_dict
                })

        return {
            'to_create': to_create,
            'to_update': to_update,
            'conflicts': conflicts,
            'missing_id_rows': missing_id_rows,
            'new_columns': list(new_columns)
        }

    def check_conflicts(self, existing, new_data):
        """
        Kontrollera om det finns betydande skillnader
        som användaren bör granska
        """
        # Viktiga fält att kontrollera för konflikter
        important_fields = ['NAMN', 'SCB_ORGNR', 'BESKRIVNING']

        for field in important_fields:
            old_val = getattr(existing, field, None)
            new_val = new_data.get(field)

            # Om båda har värden och de är olika
            if old_val and new_val and old_val != new_val:
                return True

        return False

    def show_preview(self, changes):
        """
        Visa preview av ändringar innan synkning
        """
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('FÖRHANDSVISNING AV ÄNDRINGAR'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))

        # Nya rader
        if changes['to_create']:
            self.stdout.write(self.style.SUCCESS(
                f"✓ {len(changes['to_create'])} nya företag kommer att skapas"
            ))
            for item in changes['to_create'][:5]:  # Visa första 5
                self.stdout.write(f"  - ID {item['id']}: {item['data'].get('NAMN', 'Inget namn')}")
            if len(changes['to_create']) > 5:
                self.stdout.write(f"  ... och {len(changes['to_create']) - 5} till")

        # Uppdateringar
        if changes['to_update']:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ {len(changes['to_update'])} företag kommer att uppdateras"
            ))
            for item in changes['to_update'][:5]:
                self.stdout.write(f"  - ID {item['id']}: {item['data'].get('NAMN', 'Inget namn')}")
            if len(changes['to_update']) > 5:
                self.stdout.write(f"  ... och {len(changes['to_update']) - 5} till")

        # Konflikter
        if changes['conflicts']:
            self.stdout.write(self.style.ERROR(
                f"\n⚠ {len(changes['conflicts'])} konflikter upptäcktes"
            ))
            for item in changes['conflicts'][:3]:
                self.stdout.write(f"  - ID {item['id']}: {item['new_data'].get('NAMN', 'Inget namn')}")
                self.stdout.write(f"    Befintlig data skiljer sig i viktiga fält")
            if len(changes['conflicts']) > 3:
                self.stdout.write(f"  ... och {len(changes['conflicts']) - 3} till")

        # Rader utan ID
        if changes['missing_id_rows']:
            self.stdout.write(self.style.WARNING(
                f"\n⚠ {len(changes['missing_id_rows'])} rader saknar ID och behöver genereras"
            ))

        # Nya kolumner
        if changes['new_columns']:
            self.stdout.write(self.style.WARNING(
                f"\n⚠ {len(changes['new_columns'])} nya kolumner upptäcktes i sheetet"
            ))
            self.stdout.write("Nya kolumner:")
            for col in changes['new_columns']:
                self.stdout.write(f"  - {col}")

        self.stdout.write('\n' + '='*60 + '\n')

    def handle_new_columns(self, new_columns, auto_approve):
        """
        Hantera nya kolumner - låt användaren välja vilka som ska importeras
        """
        if not new_columns:
            return []

        self.stdout.write(self.style.WARNING(
            f"\nNya kolumner upptäcktes som inte finns i AICompany-modellen:"
        ))

        # Visa alla nya kolumner med nummer
        for i, col in enumerate(new_columns, 1):
            self.stdout.write(f"  {i}. {col}")

        if auto_approve:
            self.stdout.write(self.style.WARNING(
                "\n--auto-approve är satt: Hoppar över nya kolumner"
            ))
            return []

        self.stdout.write("\n" + "="*60)
        self.stdout.write("Välj vilka kolumner du vill importera:")
        self.stdout.write("  - Skriv nummer separerade med komma (ex: 1,3,5)")
        self.stdout.write("  - Skriv 'alla' för att importera alla kolumner")
        self.stdout.write("  - Tryck Enter för att hoppa över alla")
        self.stdout.write("="*60)

        response = input("\nDitt val: ").strip()

        # Om tomt svar, hoppa över alla
        if not response:
            self.stdout.write(self.style.WARNING("Hoppar över alla nya kolumner"))
            return []

        # Om användaren vill ha alla
        if response.lower() == 'alla':
            self.stdout.write(self.style.SUCCESS(
                f"Kommer att importera alla {len(new_columns)} nya kolumner"
            ))
            self.stdout.write(self.style.WARNING(
                "(Detta kommer att kräva en migrering och omstart)"
            ))
            return new_columns

        # Parse nummerval (ex: "1,3,5")
        try:
            selected_indices = [int(x.strip()) for x in response.split(',')]
            selected_columns = []

            for idx in selected_indices:
                if 1 <= idx <= len(new_columns):
                    selected_columns.append(new_columns[idx - 1])
                else:
                    self.stdout.write(self.style.ERROR(
                        f"Ogiltigt nummer: {idx} (måste vara mellan 1 och {len(new_columns)})"
                    ))

            if selected_columns:
                self.stdout.write(self.style.SUCCESS(
                    f"\nKommer att importera {len(selected_columns)} kolumn(er):"
                ))
                for col in selected_columns:
                    self.stdout.write(f"  - {col}")
                self.stdout.write(self.style.WARNING(
                    "(Detta kommer att kräva en migrering och omstart)"
                ))
                return selected_columns
            else:
                self.stdout.write(self.style.WARNING("Inga giltiga kolumner valda, hoppar över alla"))
                return []

        except ValueError:
            self.stdout.write(self.style.ERROR(
                f"Ogiltigt format: '{response}'. Förväntade nummer separerade med komma (ex: 1,3,5)"
            ))
            self.stdout.write(self.style.WARNING("Hoppar över alla nya kolumner"))
            return []

    def handle_missing_ids(self, missing_id_rows, auto_approve):
        """
        Hantera rader som saknar ID - generera nya ID:n
        """
        if not missing_id_rows:
            return []

        self.stdout.write(self.style.WARNING(
            f"\n{len(missing_id_rows)} rader saknar ID"
        ))

        if not auto_approve:
            response = input("Vill du generera nya ID:n för dessa? (ja/nej): ")
            if response.lower() != 'ja':
                self.stdout.write("Hoppar över rader utan ID")
                return []

        # Hitta högsta befintliga ID
        max_id = AICompany.objects.all().order_by('-id').first()
        next_id = (max_id.id if max_id else 0) + 1

        generated = []
        for item in missing_id_rows:
            item['data']['id'] = next_id
            generated.append(item)
            next_id += 1

        self.stdout.write(self.style.SUCCESS(
            f"Genererade {len(generated)} nya ID:n (från {generated[0]['data']['id']} till {generated[-1]['data']['id']})"
        ))

        return generated

    def handle_conflicts(self, conflicts, auto_approve):
        """
        Hantera konflikter - ge användaren möjlighet att avsluta
        """
        if not conflicts:
            return True  # Fortsätt

        self.stdout.write(self.style.ERROR(
            f"\n⚠ VARNING: {len(conflicts)} konflikter upptäcktes"
        ))

        # Visa exempel på konflikter
        for item in conflicts[:3]:
            self.stdout.write(f"\nID {item['id']} - {item['new_data'].get('NAMN')}:")
            self.stdout.write(f"  Befintlig NAMN: {item['existing'].NAMN}")
            self.stdout.write(f"  Ny NAMN: {item['new_data'].get('NAMN')}")

        if auto_approve:
            self.stdout.write(self.style.WARNING(
                "\n--auto-approve är satt: Google Sheets kommer att vinna alla konflikter"
            ))
            return True

        self.stdout.write("\nGoogle Sheets kommer att skriva över befintlig data.")
        self.stdout.write("Vill du fortsätta? (ja/nej/avbryt)")
        response = input("> ")

        if response.lower() == 'ja':
            return True
        elif response.lower() == 'avbryt':
            self.stdout.write(self.style.WARNING("Avbryter synkning"))
            return False
        else:
            self.stdout.write(self.style.WARNING("Hoppar över konfliktrader"))
            # Ta bort konflikter från to_update
            return 'skip_conflicts'

    def perform_sync(self, changes, dry_run):
        """
        Utför faktisk synkning till databasen
        """
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n--dry-run är satt: Inga ändringar görs i databasen"
            ))
            return

        created_count = 0
        updated_count = 0

        try:
            with transaction.atomic():
                # Skapa nya företag
                for item in changes['to_create']:
                    data = {k: v for k, v in item['data'].items()
                           if k in [f.name for f in AICompany._meta.get_fields()]}
                    AICompany.objects.create(**data)
                    created_count += 1

                # Uppdatera befintliga
                for item in changes['to_update']:
                    company = AICompany.objects.get(id=item['id'])

                    # Uppdatera alla fält
                    for field, value in item['data'].items():
                        if hasattr(company, field):
                            setattr(company, field, value)

                    company.save()
                    updated_count += 1

                self.stdout.write(self.style.SUCCESS(
                    f"\n✓ Synkning klar!"
                ))
                self.stdout.write(f"  - Skapade: {created_count} företag")
                self.stdout.write(f"  - Uppdaterade: {updated_count} företag")

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"\n✗ Fel vid synkning: {str(e)}"
            ))
            raise

    def handle(self, *args, **options):
        sheet_id = options['sheet_id']
        sheet_range = options['range']
        dry_run = options['dry_run']
        auto_approve = options['auto_approve']

        self.stdout.write(self.style.SUCCESS(
            f"\nHämtar data från Google Sheets..."
        ))
        self.stdout.write(f"Sheet ID: {sheet_id}")
        self.stdout.write(f"Range: {sheet_range}\n")

        # 1. Hämta data från Google Sheets
        sheet_data = self.fetch_sheet_data(sheet_id, sheet_range)
        if not sheet_data:
            return

        self.stdout.write(self.style.SUCCESS(
            f"✓ Hämtade {len(sheet_data['rows'])} rader från Google Sheets"
        ))

        # 2. Analysera ändringar
        self.stdout.write("\nAnalyserar ändringar...")
        changes = self.detect_changes(sheet_data)

        # 3. Visa preview
        self.show_preview(changes)

        # 4. Hantera nya kolumner
        if changes['new_columns']:
            columns_to_add = self.handle_new_columns(
                changes['new_columns'],
                auto_approve
            )
            if columns_to_add:
                self.stdout.write(self.style.WARNING(
                    "\nNya kolumner måste läggas till i modellen först."
                ))
                self.stdout.write("Kör detta kommando efter att ha uppdaterat models.py:")
                self.stdout.write("  python3 manage.py makemigrations")
                self.stdout.write("  python3 manage.py migrate")
                return

        # 5. Hantera rader utan ID
        if changes['missing_id_rows']:
            generated = self.handle_missing_ids(
                changes['missing_id_rows'],
                auto_approve
            )
            # Lägg till genererade rader till to_create
            changes['to_create'].extend(generated)

        # 6. Hantera konflikter
        if changes['conflicts']:
            conflict_result = self.handle_conflicts(
                changes['conflicts'],
                auto_approve
            )

            if conflict_result is False:
                # Användaren valde att avbryta
                return
            elif conflict_result == 'skip_conflicts':
                # Användaren valde att hoppa över konflikter
                # Filtrera bort konfliktraderna från to_update
                conflict_ids = {c['id'] for c in changes['conflicts']}
                changes['to_update'] = [
                    u for u in changes['to_update']
                    if u['id'] not in conflict_ids
                ]
            else:
                # conflict_result is True - lägg till konflikter i to_update
                for conflict in changes['conflicts']:
                    changes['to_update'].append({
                        'id': conflict['id'],
                        'row_num': conflict['row_num'],
                        'data': conflict['new_data']
                    })

        # 7. Final bekräftelse
        if not auto_approve and not dry_run:
            total = len(changes['to_create']) + len(changes['to_update'])
            self.stdout.write(f"\nKommer att synkronisera {total} rader.")
            response = input("Fortsätt? (ja/nej): ")
            if response.lower() != 'ja':
                self.stdout.write("Avbryter synkning")
                return

        # 8. Utför synkning
        self.perform_sync(changes, dry_run)
