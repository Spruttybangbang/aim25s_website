from django.core.management.base import BaseCommand
from django.db import transaction
from companies.models import AICompany
import csv
import os


class Command(BaseCommand):
    help = 'Importerar AI-företag från BETTER_DATA_FINAL.csv till AICompany-tabellen'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='_new_data_source/BETTER_DATA_FINAL.csv',
            help='CSV-fil att importera (default: _new_data_source/BETTER_DATA_FINAL.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Visa vad som skulle importeras utan att spara',
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        dry_run = options['dry_run']

        # Hitta projektroten
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        filepath = os.path.join(project_root, csv_file)

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'Filen finns inte: {filepath}'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - Inga ändringar sparas\n'))

        self.stdout.write(f'Läser CSV: {filepath}')

        # Läs CSV
        with open(filepath, 'r', encoding='utf-8') as f:
            # Upptäck delimiter
            first_line = f.readline()
            delimiter = ';' if first_line.count(';') > first_line.count(',') else ','
            f.seek(0)

            reader = csv.DictReader(f, delimiter=delimiter)

            rows = list(reader)
            total_rows = len(rows)

            self.stdout.write(f'Hittade {total_rows} företag att importera')
            self.stdout.write(f'Delimiter: "{delimiter}"')

            if dry_run:
                # Visa preview av första 3 raderna
                self.stdout.write('\n' + '=' * 80)
                self.stdout.write('PREVIEW (första 3 raderna):')
                self.stdout.write('=' * 80)
                for i, row in enumerate(rows[:3], 1):
                    self.stdout.write(f'\n{i}. ID: {row.get("ID")}, Namn: {row.get("NAMN")}, Stad: {row.get("STAD")}')
                self.stdout.write('\n' + '=' * 80)
                return

            # Bekräftelse
            response = input(f'\nVill du importera {total_rows} företag till databasen? [y/N]: ').strip().lower()
            if response not in ['y', 'yes', 'ja', 'j']:
                self.stdout.write(self.style.WARNING('Import avbruten'))
                return

            # Importera
            created = 0
            updated = 0
            errors = 0

            with transaction.atomic():
                for i, row in enumerate(rows, 1):
                    try:
                        # Hämta ID från CSV
                        company_id = row.get('ID')
                        if not company_id:
                            self.stdout.write(self.style.ERROR(f'Rad {i}: Saknar ID, hoppar över'))
                            errors += 1
                            continue

                        # Konvertera boolean-fält
                        storstockholm = self._parse_boolean(row.get('STORSTOCKHOLM'))

                        # Skapa eller uppdatera företag
                        company, is_created = AICompany.objects.update_or_create(
                            id=int(company_id),
                            defaults={
                                # Grundläggande
                                'NAMN': row.get('NAMN') or '',
                                'SAJT': row.get('SAJT') or '',
                                'BESKRIVNING': row.get('BESKRIVNING') or '',
                                'STAD': row.get('STAD') or '',
                                'STORSTOCKHOLM': storstockholm,
                                'URL_LOGOTYP': row.get('URL_LOGOTYP') or '',
                                'URL_KÄLLA': row.get('URL_KÄLLA') or '',

                                # Bransch och sektor
                                'BRANSCHKLUSTER_LITEN': row.get('BRANSCHKLUSTER_LITEN') or '',
                                'BRANSCHKLUSTER_STOR': row.get('BRANSCHKLUSTER_STOR') or '',
                                'SEKTOR_SEMANTISK_MODELL': row.get('SEKTOR__SEMANTISK_MODELL') or '',
                                'SEKTOR_DETERMINISTISK_MODELL_1': row.get('SEKTOR_DETERMINISTISK_MODELL_1') or '',
                                'SEKTOR_DETERMINISTISK_MODELL_2': row.get('SEKTOR_DETERMINISTISK_MODELL_2') or '',
                                'SEKTOR_GAMMAL': row.get('SEKTOR_GAMMAL') or '',

                                # AI-förmågor
                                'AI_FÖRMÅGA_SEMANTISK_MODELL': row.get('AI-FÖRMÅGA_SEMANTISK_MODELL') or '',
                                'AI_FÖRMÅGA_GAMMAL': row.get('AI-FÖRMÅGA_GAMMAL') or '',

                                # Metadata
                                'KONFIDENS_SEMANTISK_MODELL': row.get('KONFIDENS_SEMANTISK_MODELL') or '',
                                'ORGANISATIONSTYP_GAMMAL': row.get('ORGANISATIONSTYP_GAMMAL') or '',

                                # SCB-data
                                'SCB_ORGNR': row.get('SCB_ORGNR') or '',
                                'SCB_NAMN': row.get('SCB_NAMN') or '',
                                'SCB_ADRESS': row.get('SCB_ADRESS') or '',
                                'SCB_POSTNR': row.get('SCB_POSTNR') or '',
                                'SCB_STAD': row.get('SCB_STAD') or '',
                                'SCB_KONTOR': row.get('SCB_KONTOR') or '',
                                'SCB_ANSTÄLLDA': row.get('SCB_ANSTÄLLDA') or '',
                                'SCB_VERKSAMHETSSTATUS': row.get('SCB_VERKSAMHETSSTATUS') or '',
                                'SCB_JURIDISK_FORM': row.get('SCB_JURIDISK_FORM') or '',
                                'SCB_STARTDATUM': row.get('SCB_STARTDATUM') or '',
                                'SCB_REGISTRERINGSDATUM': row.get('SCB_REGISTRERINGSDATUM') or '',
                                'SCB_BRANSCH_1': row.get('SCB_BRANSCH_1') or '',
                                'SCB_BRANSCH_2': row.get('SCB_BRANSCH_2') or '',
                                'SCB_OMSÄTTNING_ÅR': row.get('SCB_OMSÄTTNING_ÅR') or '',
                                'SCB_OMSÄTTNING_STORLEK': row.get('SCB_OMSÄTTNING_STORLEK') or '',
                                'SCB_TEL': row.get('SCB_TEL') or '',
                                'SCB_MAIL': row.get('SCB_MAIL') or '',
                                'SCB_ARBETSGIVARE_STATUS': row.get('SCB_ARBETSGIVARE_STATUS') or '',
                                'SCB_FÖRETAGSÅLDER': row.get('SCB_FÖRETAGSÅLDER') or '',
                            }
                        )

                        if is_created:
                            created += 1
                        else:
                            updated += 1

                        # Progress update varje 50:e rad
                        if i % 50 == 0:
                            self.stdout.write(f'Bearbetat {i}/{total_rows} rader...')

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Rad {i} (ID: {company_id}): {str(e)}'))
                        errors += 1
                        continue

            # Sammanfattning
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('IMPORT KLAR'))
            self.stdout.write('=' * 80)
            self.stdout.write(f'Nya företag skapade: {created}')
            self.stdout.write(f'Företag uppdaterade: {updated}')
            self.stdout.write(f'Fel: {errors}')
            self.stdout.write(f'Totalt bearbetade: {created + updated}')

    def _parse_boolean(self, value):
        """Konverterar olika boolean-representationer till Python boolean"""
        if value is None or value == '':
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.upper() in ['TRUE', '1', 'YES', 'JA', 'Y', 'J']
        return bool(value)
