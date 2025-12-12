from django.core.management.base import BaseCommand
from django.db import transaction, connection
from companies.models import Company, Sector, Domain, AICapability, Dimension, SCBEnrichment
import csv
import os
import sys
import shutil
from datetime import datetime
import sqlite3
import re


class Command(BaseCommand):
    help = 'Importerar berikade CSV-filer från import_updates/ och uppdaterar företagsdata'

    def _get_input(self, prompt):
        """Säker input-funktion som fungerar i Django management commands"""
        self.stdout.write(prompt, ending='')
        self.stdout.flush()
        return input().strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Visa vad som skulle uppdateras utan att spara ändringar',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Specifik CSV-fil att importera (annars väljs från listan)',
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Godkänn import automatiskt utan bekräftelse',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specified_file = options.get('file')
        auto_approve = options.get('auto_approve', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - Inga ändringar kommer att sparas\n'))

        # Hitta projektroten och import_updates-mappen
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        import_dir = os.path.join(project_root, 'import_updates')
        completed_dir = os.path.join(import_dir, 'completed')

        # Säkerställ att completed-mappen finns
        os.makedirs(completed_dir, exist_ok=True)

        # Hitta alla CSV-filer i import_updates
        all_csv_files = [f for f in os.listdir(import_dir) if f.endswith('.csv') and os.path.isfile(os.path.join(import_dir, f))]

        if not all_csv_files:
            self.stdout.write(self.style.WARNING('Inga CSV-filer hittades i import_updates/'))
            return

        # Välj fil(er) att bearbeta
        if specified_file:
            if specified_file not in all_csv_files:
                self.stdout.write(self.style.ERROR(f'Filen "{specified_file}" finns inte i import_updates/'))
                return
            csv_files = [specified_file]
        else:
            # Låt användaren välja fil
            csv_files = [self._select_file(all_csv_files)]
            if not csv_files[0]:
                return

        total_updated = 0
        total_errors = 0

        # Bearbeta varje fil
        for filename in csv_files:
            filepath = os.path.join(import_dir, filename)
            self.stdout.write(f'\n{"=" * 80}')
            self.stdout.write(self.style.SUCCESS(f'Bearbetar: {filename}'))
            self.stdout.write('=' * 80)

            # Läs och analysera CSV
            delimiter, columns, row_count = self._analyze_csv(filepath)

            self.stdout.write(f'\nHittade {row_count} rader')
            self.stdout.write(f'Delimiter: "{delimiter}"')
            self.stdout.write(f'\nTillgängliga kolumner i CSV:')
            for i, col in enumerate(columns, 1):
                self.stdout.write(f'  {i}. {col}')

            # Låt användaren välja kolumner att importera
            selected_columns = self._select_columns(columns, auto_approve)
            if not selected_columns:
                self.stdout.write(self.style.WARNING('Ingen import utförd'))
                continue

            # Kontrollera om det finns nya kolumner som inte finns i databasen
            missing_columns = self._check_missing_columns(selected_columns)
            if missing_columns:
                self.stdout.write(self.style.WARNING(f'\nVARNING: Följande kolumner finns INTE i databasen:'))
                for col in missing_columns:
                    self.stdout.write(f'  - {col}')
                self.stdout.write(self.style.WARNING(f'\nKör först: python manage.py import_new_columns --file {filename}'))
                self.stdout.write(self.style.WARNING('för att lägga till dessa kolumner i databasen.\n'))

                # Fråga om användaren vill fortsätta utan dessa kolumner
                if not auto_approve:
                    response = self._get_input('Vill du fortsätta utan dessa kolumner? [y/N]: ').strip().lower()
                    if response not in ['y', 'yes', 'ja', 'j']:
                        self.stdout.write(self.style.WARNING('Import avbruten av användaren'))
                        continue

                # Ta bort saknade kolumner från selected_columns
                selected_columns = [col for col in selected_columns if col not in missing_columns]

            # Visa preview av ändringar
            preview_data = self._preview_changes(filepath, delimiter, selected_columns)

            if not preview_data['changes']:
                self.stdout.write(self.style.WARNING('Inga ändringar att göra'))
                continue

            self._display_preview(preview_data, filename)

            # Bekräftelse innan import (krävs ALLTID förutom med --auto-approve)
            if not auto_approve:
                if dry_run:
                    response = self._get_input('\nVill du fortsätta med dry-run? [y/N]: ').strip().lower()
                else:
                    response = self._get_input('\nVill du fortsätta med importen? [y/N]: ').strip().lower()

                if response not in ['y', 'yes', 'ja', 'j']:
                    self.stdout.write(self.style.WARNING('Import avbruten av användaren'))
                    continue

            # Utför importen
            file_updated, file_errors = self._process_csv_file(
                filepath, delimiter, selected_columns, dry_run
            )
            total_updated += file_updated
            total_errors += file_errors

            # Flytta filen till completed om inte dry-run
            if not dry_run:
                dest = os.path.join(completed_dir, filename)
                shutil.move(filepath, dest)
                self.stdout.write(self.style.SUCCESS(f'\nFlyttade {filename} till completed/'))

        # Sammanfattning
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('SAMMANFATTNING'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Totalt uppdaterade företag: {total_updated}')
        self.stdout.write(f'Totalt antal fel: {total_errors}')
        self.stdout.write(f'Antal filer bearbetade: {len(csv_files)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDetta var en DRY RUN - inga ändringar sparades'))

    def _select_file(self, csv_files):
        """Låter användaren välja vilken CSV-fil att importera"""
        if len(csv_files) == 1:
            return csv_files[0]

        self.stdout.write('\nHittade följande CSV-filer i import_updates/:')
        for i, filename in enumerate(csv_files, 1):
            self.stdout.write(f'  {i}. {filename}')

        while True:
            response = self._get_input(f'\nVälj fil att importera [1-{len(csv_files)}] eller [q] för att avbryta: ').strip()

            if response.lower() in ['q', 'quit', 'avbryt']:
                return None

            try:
                choice = int(response)
                if 1 <= choice <= len(csv_files):
                    return csv_files[choice - 1]
                else:
                    self.stdout.write(self.style.ERROR(f'Välj ett nummer mellan 1 och {len(csv_files)}'))
            except ValueError:
                self.stdout.write(self.style.ERROR('Ange ett giltigt nummer eller "q" för att avbryta'))

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

            # Räkna rader
            row_count = sum(1 for row in reader)

        return delimiter, columns, row_count

    def _select_columns(self, columns, auto_approve):
        """Låter användaren välja vilka kolumner att importera"""
        # Kontrollera att company_id finns
        if 'company_id' not in columns:
            self.stdout.write(self.style.ERROR('\nFel: Kolumnen "company_id" saknas i CSV-filen!'))
            return None

        # Om auto-approve, importera alla kolumner
        if auto_approve:
            return columns

        self.stdout.write('\nVälj vilka kolumner att importera:')
        self.stdout.write('  [a] Alla kolumner')
        self.stdout.write('  [n] Specifika kolumner (ange nummer separerade med komma)')
        self.stdout.write('  [q] Avbryt')

        while True:
            response = self._get_input('\nDitt val: ').strip().lower()

            if response in ['q', 'quit', 'avbryt']:
                return None

            if response == 'a':
                return columns

            if response == 'n':
                # Låt användaren välja specifika kolumner
                while True:
                    col_response = self._get_input(f'\nAnge kolumnnummer separerade med komma [1-{len(columns)}]: ').strip()

                    try:
                        indices = [int(x.strip()) - 1 for x in col_response.split(',')]

                        # Validera
                        if all(0 <= i < len(columns) for i in indices):
                            selected = [columns[i] for i in indices]

                            # Säkerställ att company_id alltid är med
                            if 'company_id' not in selected:
                                selected.insert(0, 'company_id')

                            self.stdout.write('\nValda kolumner:')
                            for col in selected:
                                self.stdout.write(f'  - {col}')

                            confirm = self._get_input('\nÄr detta korrekt? [y/N]: ').strip().lower()
                            if confirm in ['y', 'yes', 'ja', 'j']:
                                return selected
                        else:
                            self.stdout.write(self.style.ERROR('Ogiltiga kolumnnummer'))
                    except ValueError:
                        self.stdout.write(self.style.ERROR('Ogiltigt format. Använd t.ex: 1,3,5'))
            else:
                self.stdout.write(self.style.ERROR('Välj [a], [n] eller [q]'))

    def _check_missing_columns(self, selected_columns):
        """Kontrollerar vilka kolumner som saknas i databasen"""
        # Definiera alla kända fält från modellen
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

        # Hämta befintliga kolumner från companies-tabellen
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(companies)")
        existing_db_columns = {row[1] for row in cursor.fetchall()}

        # Kombinera kända fält med befintliga DB-kolumner
        all_available_columns = known_fields | existing_db_columns

        # Hitta kolumner som inte finns
        missing_columns = [col for col in selected_columns if col not in all_available_columns]

        return missing_columns

    def _preview_changes(self, filepath, delimiter, selected_columns):
        """Skapar en preview av ändringar som kommer att göras"""
        changes = []
        errors = []

        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)

            # Begränsa till första 5 företag för preview
            for row_num, row in enumerate(reader, start=2):
                if row_num > 6:  # Max 5 företag i preview
                    break

                company_id = row.get('company_id', '').strip()
                if not company_id:
                    errors.append(f'Rad {row_num}: saknar company_id')
                    continue

                try:
                    company = Company.objects.get(id=company_id)
                    company_changes = self._detect_changes(company, row, selected_columns)

                    if company_changes:
                        changes.append({
                            'company': company,
                            'changes': company_changes,
                            'row_num': row_num
                        })
                except Company.DoesNotExist:
                    errors.append(f'Rad {row_num}: Företag ID {company_id} finns inte')

        # Räkna totalt antal rader
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            total_rows = sum(1 for _ in reader)

        return {
            'changes': changes,
            'errors': errors,
            'total_rows': total_rows,
            'selected_columns': selected_columns
        }

    def _detect_changes(self, company, row, selected_columns):
        """Detekterar vilka ändringar som kommer att göras"""
        changes = []

        # Company-fält som kan uppdateras
        company_fields = {
            'name', 'website', 'type', 'logo_url', 'description',
            'owner', 'location_city', 'location_greater_stockholm',
            'data_quality_score', 'source_url'
        }

        for field in company_fields:
            if field not in selected_columns or field not in row:
                continue

            new_value = row[field].strip()
            if new_value == '':
                continue

            current_value = getattr(company, field)

            # Konvertera värden beroende på fälttyp
            if field == 'location_greater_stockholm':
                if new_value.lower() in ['true', '1', 'yes', 'ja']:
                    new_value = True
                elif new_value.lower() in ['false', '0', 'no', 'nej']:
                    new_value = False
                else:
                    continue
            elif field == 'data_quality_score':
                try:
                    new_value = int(new_value)
                except ValueError:
                    continue

            if str(current_value) != str(new_value):
                changes.append(f"{field}: '{current_value}' → '{new_value}'")

        # Kolla SCB-fält
        scb_fields = {
            'organization_number', 'municipality', 'employee_size',
            'legal_form', 'phone', 'email'
        }

        for field in scb_fields:
            if field not in selected_columns or field not in row:
                continue

            new_value = row[field].strip()
            if new_value == '':
                continue

            try:
                scb = company.scb_enrichment
                current_value = getattr(scb, field, '')
                if str(current_value) != str(new_value):
                    changes.append(f"scb.{field}: '{current_value}' → '{new_value}'")
            except SCBEnrichment.DoesNotExist:
                if new_value:
                    changes.append(f"scb.{field}: (ny) → '{new_value}'")

        # Kolla dynamiska fält (nya kolumner)
        known_model_fields = company_fields | scb_fields | {
            'company_id', 'last_updated', 'sectors', 'domains',
            'ai_capabilities', 'dimensions'
        }

        scb_all_fields = {
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

        known_all_fields = known_model_fields | scb_all_fields

        # Hitta dynamiska fält
        dynamic_fields = [col for col in selected_columns if col not in known_all_fields]

        if dynamic_fields:
            cursor = connection.cursor()
            for field in dynamic_fields:
                new_value = row.get(field, '').strip()
                if new_value == '':
                    continue

                # Hämta nuvarande värde från databasen (escapa kolumnnamn)
                try:
                    cursor.execute(f'SELECT "{field}" FROM companies WHERE id = %s', [company.id])
                    result = cursor.fetchone()
                    current_value = result[0] if result and result[0] else ''

                    if str(current_value) != str(new_value):
                        changes.append(f"{field}: '{current_value}' → '{new_value}'")
                except Exception:
                    # Kolumnen finns inte än (kommer läggas till)
                    changes.append(f"{field}: (ny kolumn) → '{new_value}'")

        return changes

    def _display_preview(self, preview_data, filename):
        """Visar en preview av vad som kommer att importeras"""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('PREVIEW AV ÄNDRINGAR'))
        self.stdout.write('=' * 80)

        self.stdout.write(f'\nFil: {filename}')
        self.stdout.write(f'Totalt antal rader: {preview_data["total_rows"]}')
        self.stdout.write(f'Kolumner som kommer att importeras: {len(preview_data["selected_columns"])}')

        if preview_data['errors']:
            self.stdout.write('\n' + self.style.WARNING('VARNINGAR:'))
            for error in preview_data['errors']:
                self.stdout.write(f'  - {error}')

        if preview_data['changes']:
            self.stdout.write('\n' + self.style.SUCCESS('EXEMPEL PÅ ÄNDRINGAR (första 5 företagen):'))
            for item in preview_data['changes']:
                self.stdout.write(f'\n  {item["company"].name} (ID: {item["company"].id}):')
                for change in item['changes']:
                    self.stdout.write(f'    - {change}')

            if preview_data['total_rows'] > 5:
                self.stdout.write(f'\n  ... och {preview_data["total_rows"] - 5} rader till')
        else:
            self.stdout.write('\n' + self.style.WARNING('Inga ändringar kommer att göras'))

    def _process_csv_file(self, filepath, delimiter, selected_columns, dry_run):
        """Bearbetar en enskild CSV-fil"""
        updated_count = 0
        error_count = 0

        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):  # Start från 2 (rad 1 är header)
                try:
                    # Hämta company_id
                    company_id = row.get('company_id', '').strip()

                    if not company_id:
                        error_count += 1
                        continue

                    # Hitta företaget
                    try:
                        company = Company.objects.get(id=company_id)
                    except Company.DoesNotExist:
                        error_count += 1
                        continue

                    # Uppdatera företaget
                    updated = self._update_company(company, row, selected_columns, dry_run)

                    if updated:
                        updated_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Rad {row_num}: Fel vid bearbetning - {str(e)}')
                    )
                    error_count += 1

        return updated_count, error_count

    def _update_company(self, company, row, selected_columns, dry_run):
        """Uppdaterar ett företag baserat på CSV-data"""
        changes = []

        # Definiera fält som ska uppdateras
        company_fields = [
            'name', 'website', 'type', 'logo_url', 'description',
            'owner', 'location_city', 'location_greater_stockholm',
            'data_quality_score', 'source_url'
        ]

        scb_fields = [
            'organization_number', 'scb_company_name', 'co_address',
            'post_address', 'post_code', 'post_city', 'municipality_code',
            'municipality', 'county_code', 'county', 'num_workplaces',
            'employee_size_code', 'employee_size', 'company_status_code',
            'company_status', 'legal_form_code', 'legal_form', 'start_date',
            'registration_date', 'industry_1_code', 'industry_1',
            'industry_2_code', 'industry_2', 'revenue_year', 'revenue_size_code',
            'revenue_size', 'phone', 'email', 'employer_status_code',
            'employer_status', 'vat_status_code', 'vat_status', 'export_import'
        ]

        # Uppdatera Company-fält
        for field in company_fields:
            if field not in selected_columns or field not in row:
                continue

            new_value = row[field].strip()

            # Hantera boolean för location_greater_stockholm
            if field == 'location_greater_stockholm':
                if new_value.lower() in ['true', '1', 'yes', 'ja']:
                    new_value = True
                elif new_value.lower() in ['false', '0', 'no', 'nej']:
                    new_value = False
                else:
                    new_value = None

            # Hantera integer för data_quality_score
            elif field == 'data_quality_score':
                if new_value:
                    try:
                        new_value = int(new_value)
                    except ValueError:
                        new_value = None
                else:
                    new_value = None

            # Hoppa över tomma värden (behåll nuvarande)
            elif new_value == '':
                continue

            # Kolla om värdet har ändrats
            current_value = getattr(company, field)
            if str(current_value) != str(new_value) and new_value is not None:
                if not dry_run:
                    setattr(company, field, new_value)
                changes.append(f"{field}: '{current_value}' → '{new_value}'")

        # Spara Company om det finns ändringar
        if changes and not dry_run:
            company.save()

        # Uppdatera SCB-data
        scb_changes = []
        try:
            scb = company.scb_enrichment
        except SCBEnrichment.DoesNotExist:
            # Skapa SCB-post om den inte finns och det finns SCB-data
            has_scb_data = any(row.get(field, '').strip() for field in scb_fields)
            if has_scb_data and not dry_run:
                scb = SCBEnrichment.objects.create(company=company)
            elif has_scb_data:
                scb_changes.append("Skulle skapa ny SCB-post")
                scb = None
            else:
                scb = None

        if scb:
            for field in scb_fields:
                if field not in selected_columns or field not in row:
                    continue

                new_value = row[field].strip()

                # Hoppa över tomma värden
                if new_value == '':
                    continue

                # Kolla om värdet har ändrats
                current_value = getattr(scb, field)
                if str(current_value) != str(new_value):
                    if not dry_run:
                        setattr(scb, field, new_value)
                    scb_changes.append(f"{field}: '{current_value}' → '{new_value}'")

            # Spara SCB om det finns ändringar
            if scb_changes and not dry_run:
                scb.save()

        # Hantera relationer (sectors, domains, etc.)
        relation_changes = self._update_relations(company, row, selected_columns, dry_run)

        # Hantera nya kolumner (dynamiska fält som lagts till i databasen)
        dynamic_changes = self._update_dynamic_fields(company, row, selected_columns, dry_run)

        # Samla alla ändringar
        all_changes = changes + scb_changes + relation_changes + dynamic_changes

        # Logga om det finns ändringar
        if all_changes:
            self.stdout.write(
                self.style.SUCCESS(f'  {"[DRY RUN] " if dry_run else ""}Uppdaterade {company.name} (ID: {company.id}):')
            )
            for change in all_changes:
                self.stdout.write(f'    - {change}')
            return True

        return False

    def _update_dynamic_fields(self, company, row, selected_columns, dry_run):
        """Uppdaterar dynamiska fält (nya kolumner som lagts till i databasen)"""
        changes = []

        # Definiera alla kända fält (modell-fält och SCB-fält)
        known_model_fields = {
            'company_id', 'name', 'website', 'type', 'logo_url', 'description',
            'owner', 'location_city', 'location_greater_stockholm',
            'data_quality_score', 'source_url', 'last_updated',
            'sectors', 'domains', 'ai_capabilities', 'dimensions',
        }

        scb_fields = {
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

        known_fields = known_model_fields | scb_fields

        # Hitta dynamiska fält (kolumner som inte finns i modellen/SCB)
        dynamic_fields = [col for col in selected_columns if col not in known_fields]

        if not dynamic_fields:
            return []

        # Uppdatera fält med raw SQL
        cursor = connection.cursor()
        fields_to_update = {}

        for field in dynamic_fields:
            new_value = row.get(field, '').strip()

            # Hoppa över tomma värden
            if new_value == '':
                continue

            # Hämta nuvarande värde (escapa kolumnnamn med quotes)
            try:
                cursor.execute(f'SELECT "{field}" FROM companies WHERE id = %s', [company.id])
                result = cursor.fetchone()
                current_value = result[0] if result and result[0] else ''
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'    Kunde inte läsa fält {field}: {e}'))
                continue

            if str(current_value) != str(new_value):
                fields_to_update[field] = new_value
                changes.append(f"{field}: '{current_value}' → '{new_value}'")

        # Uppdatera med raw SQL och commit
        if fields_to_update and not dry_run:
            # Escapa kolumnnamn med double quotes för SQL-säkerhet
            placeholders = ', '.join([f'"{field}" = %s' for field in fields_to_update.keys()])
            values = list(fields_to_update.values()) + [company.id]
            try:
                cursor.execute(f"UPDATE companies SET {placeholders} WHERE id = %s", values)
                # Explicit commit för raw SQL
                connection.commit()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Kunde inte uppdatera dynamiska fält: {e}'))

        return changes

    def _update_relations(self, company, row, selected_columns, dry_run):
        """Uppdaterar relationer (sectors, domains, capabilities, dimensions)"""
        changes = []

        # Definiera relationer
        relations = {
            'sectors': (Sector, 'sectors'),
            'domains': (Domain, 'domains'),
            'ai_capabilities': (AICapability, 'ai_capabilities'),
            'dimensions': (Dimension, 'dimensions'),
        }

        for csv_field, (model_class, relation_attr) in relations.items():
            if csv_field not in selected_columns or csv_field not in row:
                continue

            new_values = row[csv_field].strip()

            # Hoppa över om tomt
            if not new_values:
                continue

            # Parse kommaseparerad lista
            new_items = [item.strip() for item in new_values.split(',') if item.strip()]

            # Hämta nuvarande relationer
            current_items = set(getattr(company, relation_attr).values_list('name', flat=True))
            new_items_set = set(new_items)

            # Kolla om det finns ändringar
            if current_items != new_items_set:
                if not dry_run:
                    # Rensa och lägg till nya
                    relation_manager = getattr(company, relation_attr)
                    relation_manager.clear()

                    for item_name in new_items:
                        # Skapa eller hämta item
                        item, created = model_class.objects.get_or_create(name=item_name)
                        relation_manager.add(item)

                changes.append(
                    f"{csv_field}: {{{', '.join(current_items)}}} → {{{', '.join(new_items_set)}}}"
                )

        return changes
