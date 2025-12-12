from django.core.management.base import BaseCommand
from django.db import connection
import csv
import os
import re


class Command(BaseCommand):
    help = 'Lägger till nya kolumner från CSV-fil i companies-tabellen (utan att importera data)'

    def _get_input(self, prompt):
        """Säker input-funktion som fungerar i Django management commands"""
        self.stdout.write(prompt, ending='')
        self.stdout.flush()
        return input().strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Visa vilka kolumner som skulle läggas till utan att göra ändringar',
        )
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='CSV-fil att läsa kolumner från',
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Godkänn automatiskt utan bekräftelse',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        csv_file = options['file']
        auto_approve = options.get('auto_approve', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - Inga ändringar kommer att sparas\n'))

        # Hitta projektroten och import_updates-mappen
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        import_dir = os.path.join(project_root, 'import_updates')
        filepath = os.path.join(import_dir, csv_file)

        # Kontrollera att filen finns
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'Filen "{csv_file}" finns inte i import_updates/'))
            return

        self.stdout.write(f'\n{"=" * 80}')
        self.stdout.write(self.style.SUCCESS(f'Analyserar kolumner i: {csv_file}'))
        self.stdout.write('=' * 80)

        # Läs och analysera CSV
        delimiter, columns = self._analyze_csv(filepath)

        self.stdout.write(f'\nDelimiter: "{delimiter}"')
        self.stdout.write(f'\nHittade {len(columns)} kolumner i CSV:')
        for i, col in enumerate(columns, 1):
            self.stdout.write(f'  {i}. {col}')

        # Identifiera nya kolumner
        new_columns = self._identify_new_columns(columns)

        if not new_columns:
            self.stdout.write(self.style.SUCCESS('\nInga nya kolumner att lägga till - alla kolumner finns redan!'))
            return

        # Visa vilka kolumner som skulle läggas till
        self.stdout.write(f'\n{self.style.SUCCESS("NYA KOLUMNER ATT LÄGGA TILL:")}')
        for col in new_columns:
            self.stdout.write(f'  - {col}')

        # Bekräftelse
        if not auto_approve:
            if dry_run:
                response = self._get_input('\nVill du fortsätta med dry-run? [y/N]: ').strip().lower()
            else:
                response = self._get_input(f'\nVill du lägga till {len(new_columns)} nya kolumner? [y/N]: ').strip().lower()

            if response not in ['y', 'yes', 'ja', 'j']:
                self.stdout.write(self.style.WARNING('Operation avbruten av användaren'))
                return

        # Lägg till kolumnerna
        added_columns = self._add_columns_to_database(new_columns, dry_run)

        if added_columns:
            self.stdout.write(self.style.SUCCESS(f'\n{"[DRY RUN] Skulle lägga till" if dry_run else "Lade till"} {len(added_columns)} nya kolumner:'))
            for col in added_columns:
                self.stdout.write(f'  ✓ {col}')

            # Uppdatera models.py och admin.py
            if not dry_run:
                self._update_models_and_admin(added_columns)
                self.stdout.write(self.style.SUCCESS('\n✓ Uppdaterade models.py och admin.py'))
                self.stdout.write(self.style.SUCCESS(f'\n✓ Klart! Nu kan du köra import_enriched_csv för att importera data.'))
        else:
            self.stdout.write(self.style.WARNING('\nInga kolumner lades till'))

    def _analyze_csv(self, filepath):
        """Analyserar CSV-filen för att upptäcka delimiter och kolumner"""
        with open(filepath, 'r', encoding='utf-8') as f:
            # Läs första raden för att upptäcka delimiter
            first_line = f.readline()

            # Försök identifiera delimiter
            comma_count = first_line.count(',')
            semicolon_count = first_line.count(';')

            delimiter = ',' if comma_count >= semicolon_count else ';'

            # Återställ till början av filen
            f.seek(0)

            # Läs kolumner
            reader = csv.DictReader(f, delimiter=delimiter)
            columns = reader.fieldnames

        return delimiter, columns

    def _identify_new_columns(self, csv_columns):
        """Identifierar kolumner som inte finns i databasen eller modellen"""
        # Definiera alla kända fält (från Company och SCBEnrichment modeller)
        known_fields = {
            'company_id', 'name', 'website', 'type', 'logo_url', 'description',
            'owner', 'location_city', 'location_greater_stockholm',
            'data_quality_score', 'source_url', 'last_updated',
            'sectors', 'domains', 'ai_capabilities', 'dimensions',
            'organization_number', 'scb_company_name', 'co_address',
            'post_address', 'post_code', 'post_city', 'municipality_code',
            'municipality', 'county_code', 'county', 'num_workplaces',
            'employee_size_code', 'employee_size', 'company_status_code',
            'company_status', 'legal_form_code', 'legal_form', 'start_date',
            'registration_date', 'industry_1_code', 'industry_1',
            'industry_2_code', 'industry_2', 'revenue_year', 'revenue_size_code',
            'revenue_size', 'phone', 'email', 'employer_status_code',
            'employer_status', 'vat_status_code', 'vat_status', 'export_import'
        }

        # Hämta befintliga kolumner från companies-tabellen i databasen
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(companies)")
        existing_db_columns = {row[1] for row in cursor.fetchall()}

        # Hitta kolumner som inte finns i modellen ELLER i databasen
        new_columns = []
        for col in csv_columns:
            if col not in known_fields and col not in existing_db_columns:
                new_columns.append(col)

        return new_columns

    def _add_columns_to_database(self, columns, dry_run):
        """Lägger till nya kolumner i companies-tabellen"""
        if dry_run:
            return columns

        cursor = connection.cursor()
        added_columns = []

        for column_name in columns:
            try:
                # Lägg till som TEXT-kolumn (standardtyp för flexibilitet)
                cursor.execute(f'ALTER TABLE companies ADD COLUMN {column_name} TEXT')
                added_columns.append(column_name)
                self.stdout.write(f'    Lade till kolumn: {column_name}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Kunde inte lägga till kolumn {column_name}: {e}'))

        return added_columns

    def _update_models_and_admin(self, new_columns):
        """Uppdaterar models.py och admin.py med de nya kolumnerna"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        # Uppdatera models.py
        models_path = os.path.join(project_root, 'companies', 'models.py')
        self._update_models_file(models_path, new_columns)

        # Uppdatera admin.py
        admin_path = os.path.join(project_root, 'companies', 'admin.py')
        self._update_admin_file(admin_path, new_columns)

    def _update_models_file(self, models_path, new_columns):
        """Lägger till nya fält i Company-modellen"""
        try:
            with open(models_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Kolla om fälten redan finns
            already_exist = [col for col in new_columns if f"{col} = models.TextField" in content]
            if already_exist:
                self.stdout.write(self.style.WARNING(f'    Några fält finns redan i models.py: {", ".join(already_exist)}'))

            # Filtrera bort fält som redan finns
            columns_to_add = [col for col in new_columns if col not in already_exist]
            if not columns_to_add:
                return

            # Hitta sista fältet i Company-modellen (före class Meta)
            # Leta efter type_new eller source_url som sista fält
            pattern = r"(    type_new = models\.TextField\(blank=True, null=True, verbose_name=\"Type New\"\)\n)"

            # Om type_new inte finns, leta efter source_url
            if "type_new" not in content:
                pattern = r"(    source_url = models\.TextField\(blank=True, null=True, verbose_name=\"Käll-URL\"\)\n)"

            # Skapa nya fält-definitioner
            new_fields_code = ""
            for column_name in columns_to_add:
                # Skapa ett läsbart verbose_name från kolumnnamnet
                verbose_name = column_name.replace('_', ' ').title()
                new_fields_code += f"    {column_name} = models.TextField(blank=True, null=True, verbose_name=\"{verbose_name}\")\n"

            # Lägg till nya fält
            new_content = re.sub(pattern, r"\1" + new_fields_code, content)

            # Skriv tillbaka
            with open(models_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            self.stdout.write(f'    Uppdaterade models.py med {len(columns_to_add)} nya fält')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Kunde inte uppdatera models.py: {e}'))

    def _update_admin_file(self, admin_path, new_columns):
        """Lägger till nya fält i list_display i CompanyAdmin"""
        try:
            with open(admin_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Kolla om fälten redan finns i list_display
            already_exist = [col for col in new_columns if f"'{col}'" in content or f'"{col}"' in content]
            if already_exist:
                self.stdout.write(self.style.WARNING(f'    Några fält finns redan i admin.py: {", ".join(already_exist)}'))

            # Filtrera bort fält som redan finns
            columns_to_add = [col for col in new_columns if col not in already_exist]
            if not columns_to_add:
                return

            # Leta efter type_new i list_display och lägg till efter den
            pattern = r"(        'type_new',\n)(        # Metadata\n)"

            # Skapa nya list_display-rader
            new_fields_code = ""
            for column_name in columns_to_add:
                new_fields_code += f"        '{column_name}',\n"

            # Lägg till nya fält
            new_content = re.sub(pattern, r"\1" + new_fields_code + r"\2", content)

            # Skriv tillbaka
            with open(admin_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            self.stdout.write(f'    Uppdaterade admin.py med {len(columns_to_add)} nya fält')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Kunde inte uppdatera admin.py: {e}'))
