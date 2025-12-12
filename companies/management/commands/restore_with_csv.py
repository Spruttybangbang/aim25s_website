from django.core.management.base import BaseCommand
from django.db import transaction
from companies.models import Company, Sector, Domain, AICapability, Dimension, SCBEnrichment
import csv
import os
import sys
from datetime import datetime


class Command(BaseCommand):
    help = 'Återställer företagsdata från CSV-filer i todo/ mappen'

    def _get_input(self, prompt):
        """Säker input-funktion som fungerar i Django management commands"""
        self.stdout.write(prompt, ending='')
        self.stdout.flush()
        return input().strip()

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('DATABASÅTERSTÄLLNING FRÅN CSV'))
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write('\nDetta script återställer databasen till värden från en CSV-fil.')
        self.stdout.write('Användbart om fel data har importerats.\n')

        # Hitta projektroten och todo-mappen
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        todo_dir = os.path.join(project_root, 'todo')

        # Hitta alla CSV-filer i todo
        if not os.path.exists(todo_dir):
            self.stdout.write(self.style.ERROR(f'Todo-mappen finns inte: {todo_dir}'))
            return

        csv_files = [f for f in os.listdir(todo_dir) if f.endswith('.csv') and os.path.isfile(os.path.join(todo_dir, f))]

        if not csv_files:
            self.stdout.write(self.style.WARNING('Inga CSV-filer hittades i todo/'))
            return

        # Låt användaren välja fil
        selected_file = self._select_file(csv_files)
        if not selected_file:
            return

        filepath = os.path.join(todo_dir, selected_file)

        # Analysera CSV
        delimiter, columns, row_count = self._analyze_csv(filepath)

        self.stdout.write(f'\n{"=" * 80}')
        self.stdout.write(self.style.SUCCESS(f'Vald fil: {selected_file}'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'\nRader i CSV: {row_count}')
        self.stdout.write(f'Delimiter: "{delimiter}"')
        self.stdout.write(f'Kolumner: {len(columns)}')

        # Kontrollera att company_id finns
        if 'company_id' not in columns:
            self.stdout.write(self.style.ERROR('\nFel: Kolumnen "company_id" saknas i CSV-filen!'))
            return

        # Skapa preview av vad som kommer att återställas
        preview_data = self._preview_restore(filepath, delimiter, columns)

        if not preview_data['changes']:
            self.stdout.write(self.style.WARNING('\nInga ändringar skulle göras - databasen matchar redan CSV:n'))
            return

        # Visa preview
        self._display_preview(preview_data, selected_file)

        # Kräv godkännande
        self.stdout.write('\n' + '!' * 80)
        self.stdout.write(self.style.WARNING('VARNING: Detta kommer att SKRIVA ÖVER data i databasen!'))
        self.stdout.write('!' * 80)
        response = self._get_input('\nÄr du säker på att du vill fortsätta? Skriv "ÅTERSTÄLL" för att bekräfta: ').strip()

        if response != 'ÅTERSTÄLL':
            self.stdout.write(self.style.WARNING('Återställning avbruten'))
            return

        # Utför återställningen
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('UTFÖR ÅTERSTÄLLNING...'))
        self.stdout.write('=' * 80)

        restore_log = self._perform_restore(filepath, delimiter, columns)

        # Skriv logg till markdown-fil
        log_filename = self._write_restore_log(todo_dir, selected_file, restore_log)

        # Sammanfattning
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('ÅTERSTÄLLNING KLAR!'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Företag återställda: {restore_log["restored_count"]}')
        self.stdout.write(f'Fel: {restore_log["error_count"]}')
        self.stdout.write(f'Loggfil skapad: {log_filename}')
        self.stdout.write('\nKontrollera databasen i Django Admin för att verifiera resultatet.')

    def _select_file(self, csv_files):
        """Låter användaren välja vilken CSV-fil att använda för återställning"""
        if len(csv_files) == 1:
            self.stdout.write(f'\nHittade en CSV-fil: {csv_files[0]}')
            response = self._get_input('Vill du använda denna fil? [y/N]: ').strip().lower()
            if response in ['y', 'yes', 'ja', 'j']:
                return csv_files[0]
            return None

        self.stdout.write('\nHittade följande CSV-filer i todo/:')
        for i, filename in enumerate(csv_files, 1):
            # Visa filstorlek och datum
            filepath = os.path.join('todo', filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                self.stdout.write(f'  {i}. {filename} ({size} bytes, {mtime.strftime("%Y-%m-%d %H:%M")})')
            else:
                self.stdout.write(f'  {i}. {filename}')

        while True:
            response = self._get_input(f'\nVälj fil att använda [1-{len(csv_files)}] eller [q] för att avbryta: ').strip()

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

    def _preview_restore(self, filepath, delimiter, columns):
        """Skapar en preview av vad som kommer att återställas"""
        changes = []
        errors = []
        total_processed = 0

        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):
                company_id = row.get('company_id', '').strip()
                if not company_id:
                    errors.append(f'Rad {row_num}: saknar company_id')
                    continue

                try:
                    company = Company.objects.get(id=company_id)
                    total_processed += 1

                    # Detektera ändringar som skulle göras
                    company_changes = self._detect_restore_changes(company, row, columns)

                    if company_changes:
                        changes.append({
                            'company': company,
                            'changes': company_changes,
                            'row_num': row_num
                        })
                except Company.DoesNotExist:
                    errors.append(f'Rad {row_num}: Företag ID {company_id} finns inte i databasen')

        return {
            'changes': changes,
            'errors': errors,
            'total_processed': total_processed,
            'total_rows': total_processed + len(errors)
        }

    def _detect_restore_changes(self, company, row, columns):
        """Detekterar vilka ändringar som skulle göras vid återställning"""
        changes = []

        # Company-fält
        company_fields = {
            'name', 'website', 'type', 'logo_url', 'description',
            'owner', 'location_city', 'location_greater_stockholm',
            'data_quality_score', 'source_url'
        }

        for field in company_fields:
            if field not in columns or field not in row:
                continue

            csv_value = row[field].strip()
            current_value = getattr(company, field)

            # Konvertera tomma strängar till None för jämförelse
            if csv_value == '':
                csv_value = None

            # Hantera boolean
            if field == 'location_greater_stockholm' and csv_value:
                if csv_value.lower() in ['true', '1', 'yes', 'ja']:
                    csv_value = True
                elif csv_value.lower() in ['false', '0', 'no', 'nej']:
                    csv_value = False

            # Hantera integer
            if field == 'data_quality_score' and csv_value:
                try:
                    csv_value = int(csv_value)
                except ValueError:
                    csv_value = None

            # Jämför värden
            if str(current_value) != str(csv_value):
                changes.append({
                    'field': field,
                    'type': 'company',
                    'current': current_value,
                    'restore_to': csv_value
                })

        # SCB-fält
        scb_fields = {
            'organization_number', 'scb_company_name', 'municipality',
            'employee_size', 'legal_form', 'phone', 'email'
        }

        try:
            scb = company.scb_enrichment
            for field in scb_fields:
                if field not in columns or field not in row:
                    continue

                csv_value = row[field].strip()
                current_value = getattr(scb, field, '')

                if csv_value == '':
                    csv_value = None

                if str(current_value) != str(csv_value):
                    changes.append({
                        'field': f'scb.{field}',
                        'type': 'scb',
                        'current': current_value,
                        'restore_to': csv_value
                    })
        except SCBEnrichment.DoesNotExist:
            # Om SCB-post inte finns men CSV har SCB-data, notera det
            has_scb_data = any(row.get(field, '').strip() for field in scb_fields if field in columns)
            if has_scb_data:
                changes.append({
                    'field': 'scb_enrichment',
                    'type': 'scb',
                    'current': 'Saknas',
                    'restore_to': 'Kommer skapas med data från CSV'
                })

        return changes

    def _display_preview(self, preview_data, filename):
        """Visar en preview av återställningen"""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.WARNING('PREVIEW AV ÅTERSTÄLLNING'))
        self.stdout.write('=' * 80)

        self.stdout.write(f'\nFil: {filename}')
        self.stdout.write(f'Totalt antal företag som kommer att påverkas: {len(preview_data["changes"])}')
        self.stdout.write(f'Totalt antal rader: {preview_data["total_processed"]}')

        if preview_data['errors']:
            self.stdout.write('\n' + self.style.WARNING('VARNINGAR:'))
            for error in preview_data['errors']:
                self.stdout.write(f'  - {error}')

        if preview_data['changes']:
            # Visa de första 10 företagen
            display_count = min(10, len(preview_data['changes']))
            self.stdout.write(f'\n' + self.style.SUCCESS(f'EXEMPEL PÅ ÄNDRINGAR (visar {display_count} av {len(preview_data["changes"])} företag):'))

            for item in preview_data['changes'][:display_count]:
                self.stdout.write(f'\n  {item["company"].name} (ID: {item["company"].id}):')
                for change in item['changes']:
                    current_display = repr(change['current']) if change['current'] else '(tomt)'
                    restore_display = repr(change['restore_to']) if change['restore_to'] else '(tomt)'
                    self.stdout.write(f'    - {change["field"]}: {current_display} → {restore_display}')

            if len(preview_data['changes']) > display_count:
                self.stdout.write(f'\n  ... och {len(preview_data["changes"]) - display_count} företag till')

    def _perform_restore(self, filepath, delimiter, columns):
        """Utför den faktiska återställningen"""
        restored_count = 0
        error_count = 0
        detailed_log = []

        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):
                try:
                    company_id = row.get('company_id', '').strip()
                    if not company_id:
                        error_count += 1
                        continue

                    try:
                        company = Company.objects.get(id=company_id)
                    except Company.DoesNotExist:
                        error_count += 1
                        detailed_log.append({
                            'company_id': company_id,
                            'company_name': 'OKÄND',
                            'status': 'FEL',
                            'message': 'Företag finns inte i databasen',
                            'changes': []
                        })
                        continue

                    # Återställ företaget
                    changes = self._restore_company(company, row, columns)

                    if changes:
                        restored_count += 1
                        detailed_log.append({
                            'company_id': company.id,
                            'company_name': company.name,
                            'status': 'ÅTERSTÄLLD',
                            'message': f'{len(changes)} fält återställda',
                            'changes': changes
                        })
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Återställde {company.name} (ID: {company.id})'))

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Rad {row_num}: Fel - {str(e)}'))
                    detailed_log.append({
                        'company_id': company_id if 'company_id' in locals() else 'OKÄND',
                        'company_name': 'FEL',
                        'status': 'FEL',
                        'message': str(e),
                        'changes': []
                    })

        return {
            'restored_count': restored_count,
            'error_count': error_count,
            'detailed_log': detailed_log
        }

    def _restore_company(self, company, row, columns):
        """Återställer ett företag från CSV-data"""
        changes = []

        # Company-fält
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

        # Återställ Company-fält
        for field in company_fields:
            if field not in columns or field not in row:
                continue

            csv_value = row[field].strip()
            current_value = getattr(company, field)

            # Hantera tomma strängar
            if csv_value == '':
                csv_value = None

            # Konvertera värden
            if field == 'location_greater_stockholm' and csv_value:
                if csv_value.lower() in ['true', '1', 'yes', 'ja']:
                    csv_value = True
                elif csv_value.lower() in ['false', '0', 'no', 'nej']:
                    csv_value = False

            if field == 'data_quality_score' and csv_value:
                try:
                    csv_value = int(csv_value)
                except ValueError:
                    csv_value = None

            # Uppdatera om värdet har ändrats
            if str(current_value) != str(csv_value):
                setattr(company, field, csv_value)
                changes.append(f"{field}: {repr(current_value)} → {repr(csv_value)}")

        # Spara Company om det finns ändringar
        if changes:
            company.save()

        # Återställ SCB-data
        scb_changes = []
        has_scb_data = any(row.get(field, '').strip() for field in scb_fields if field in columns)

        if has_scb_data:
            try:
                scb = company.scb_enrichment
            except SCBEnrichment.DoesNotExist:
                scb = SCBEnrichment.objects.create(company=company)
                scb_changes.append("Skapade ny SCB-post")

            for field in scb_fields:
                if field not in columns or field not in row:
                    continue

                csv_value = row[field].strip()
                current_value = getattr(scb, field, '')

                if csv_value == '':
                    csv_value = None

                if str(current_value) != str(csv_value):
                    setattr(scb, field, csv_value)
                    scb_changes.append(f"scb.{field}: {repr(current_value)} → {repr(csv_value)}")

            if scb_changes:
                scb.save()

        # Återställ relationer
        relation_changes = self._restore_relations(company, row, columns)

        return changes + scb_changes + relation_changes

    def _restore_relations(self, company, row, columns):
        """Återställer relationer från CSV"""
        changes = []

        relations = {
            'sectors': (Sector, 'sectors'),
            'domains': (Domain, 'domains'),
            'ai_capabilities': (AICapability, 'ai_capabilities'),
            'dimensions': (Dimension, 'dimensions'),
        }

        for csv_field, (model_class, relation_attr) in relations.items():
            if csv_field not in columns or csv_field not in row:
                continue

            csv_values = row[csv_field].strip()

            # Parse CSV-värden
            if csv_values:
                csv_items = set(item.strip() for item in csv_values.split(',') if item.strip())
            else:
                csv_items = set()

            # Hämta nuvarande relationer
            current_items = set(getattr(company, relation_attr).values_list('name', flat=True))

            # Uppdatera om det finns skillnader
            if current_items != csv_items:
                relation_manager = getattr(company, relation_attr)
                relation_manager.clear()

                for item_name in csv_items:
                    item, created = model_class.objects.get_or_create(name=item_name)
                    relation_manager.add(item)

                changes.append(
                    f"{csv_field}: {{{', '.join(current_items)}}} → {{{', '.join(csv_items)}}}"
                )

        return changes

    def _write_restore_log(self, todo_dir, csv_filename, restore_log):
        """Skriver en detaljerad logg i markdown-format"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'restore_log_{timestamp}.md'
        log_filepath = os.path.join(todo_dir, log_filename)

        with open(log_filepath, 'w', encoding='utf-8') as f:
            f.write(f'# Återställningslogg\n\n')
            f.write(f'**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            f.write(f'**CSV-fil använd:** `{csv_filename}`\n\n')
            f.write(f'**Totalt återställda företag:** {restore_log["restored_count"]}\n\n')
            f.write(f'**Totalt antal fel:** {restore_log["error_count"]}\n\n')
            f.write('---\n\n')

            f.write('## Detaljerad logg\n\n')

            for entry in restore_log['detailed_log']:
                f.write(f'### {entry["company_name"]} (ID: {entry["company_id"]})\n\n')
                f.write(f'**Status:** {entry["status"]}\n\n')
                f.write(f'**Meddelande:** {entry["message"]}\n\n')

                if entry['changes']:
                    f.write('**Ändringar:**\n\n')
                    for change in entry['changes']:
                        f.write(f'- {change}\n')
                    f.write('\n')

                f.write('---\n\n')

            f.write(f'\n## Sammanfattning\n\n')
            f.write(f'Återställningen genomfördes {datetime.now().strftime("%Y-%m-%d kl. %H:%M:%S")}.\n\n')
            f.write(f'Databasen har återställts till värden från CSV-filen `{csv_filename}`.\n\n')

        return log_filename
