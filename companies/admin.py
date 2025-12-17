from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
import csv
from datetime import datetime
import os
import json
import requests
from .models import (
    AICompany,
    PublicViewConfiguration,
    ErrorReport
)


# ============================================================================
# AICompany - Företagsdatabas
# ============================================================================

@admin.register(AICompany)
class AICompanyAdmin(admin.ModelAdmin):
    """
    Admin för företagsdatabasen
    """
    # Alla fält utom BESKRIVNING
    list_display = [
        'id',
        'NAMN',
        'SAJT',
        'STAD',
        'STORSTOCKHOLM',
        'URL_LOGOTYP',
        'URL_KÄLLA',
        'AI_FÖRMÅGA_V2',
        'BRANSCHKLUSTER_V2',
        'ANSTÄLLDA_GRUPPERING_V2',
        'OMSÄTTNING_GRUPPERING_V2',
        'TILLAMPNING_OPTIMERING_AUTOMATION',
        'TILLAMPNING_SPRAK_LJUD',
        'TILLAMPNING_PROGNOS_PREDIKTION',
        'TILLAMPNING_INFRASTRUKTUR_DATA',
        'TILLAMPNING_INSIKT_ANALYS',
        'TILLAMPNING_VISUELL_AI',
        'SCB_ORGNR',
        'SCB_NAMN',
        'SCB_ADRESS',
        'SCB_POSTNR',
        'SCB_STAD',
        'SCB_KONTOR',
        'SCB_ANSTÄLLDA',
        'SCB_VERKSAMHETSSTATUS',
        'SCB_JURIDISK_FORM',
        'SCB_STARTDATUM',
        'SCB_REGISTRERINGSDATUM',
        'SCB_BRANSCH_1',
        'SCB_BRANSCH_2',
        'SCB_OMSÄTTNING_ÅR',
        'SCB_OMSÄTTNING_STORLEK',
        'SCB_TEL',
        'SCB_MAIL',
        'SCB_ARBETSGIVARE_STATUS',
        'SCB_FÖRETAGSÅLDER',
    ]

    list_display_links = ['id', 'NAMN']

    search_fields = [
        'NAMN',
        'BESKRIVNING',
        'STAD',
        'SCB_ORGNR',
        'SCB_NAMN',
        'AI_FÖRMÅGA_V2',
        'BRANSCHKLUSTER_V2',
    ]

    # Utökade filter enligt användarens önskemål
    list_filter = [
        'AI_FÖRMÅGA_V2',
        'BRANSCHKLUSTER_V2',
        'ANSTÄLLDA_GRUPPERING_V2',
        'OMSÄTTNING_GRUPPERING_V2',
        'TILLAMPNING_OPTIMERING_AUTOMATION',
        'TILLAMPNING_SPRAK_LJUD',
        'TILLAMPNING_PROGNOS_PREDIKTION',
        'TILLAMPNING_INFRASTRUKTUR_DATA',
        'TILLAMPNING_INSIKT_ANALYS',
        'TILLAMPNING_VISUELL_AI',
        'STAD',
        'STORSTOCKHOLM',
        'SCB_ANSTÄLLDA',
        'SCB_OMSÄTTNING_STORLEK',
        'SCB_JURIDISK_FORM',
        'SCB_VERKSAMHETSSTATUS',
    ]

    ordering = ['NAMN']
    list_per_page = 50
    save_on_top = True

    fieldsets = (
        ('Grundläggande information', {
            'fields': ('id', 'NAMN', 'SAJT', 'BESKRIVNING', 'URL_LOGOTYP', 'URL_KÄLLA')
        }),
        ('Plats', {
            'fields': ('STAD', 'STORSTOCKHOLM')
        }),
        ('AI-förmågor och Bransch (V2)', {
            'fields': (
                'AI_FÖRMÅGA_V2',
                'BRANSCHKLUSTER_V2',
                'ANSTÄLLDA_GRUPPERING_V2',
                'OMSÄTTNING_GRUPPERING_V2',
            ),
        }),
        ('AI-tillämpningar (Användningsområden)', {
            'fields': (
                'TILLAMPNING_OPTIMERING_AUTOMATION',
                'TILLAMPNING_SPRAK_LJUD',
                'TILLAMPNING_PROGNOS_PREDIKTION',
                'TILLAMPNING_INFRASTRUKTUR_DATA',
                'TILLAMPNING_INSIKT_ANALYS',
                'TILLAMPNING_VISUELL_AI',
            ),
            'description': 'Markera vilka tillämpningsområden företaget arbetar med',
        }),
        ('SCB - Företagsinfo', {
            'fields': ('SCB_ORGNR', 'SCB_NAMN'),
            'classes': ('collapse',),
        }),
        ('SCB - Adress', {
            'fields': ('SCB_ADRESS', 'SCB_POSTNR', 'SCB_STAD'),
            'classes': ('collapse',),
        }),
        ('SCB - Organisation', {
            'fields': (
                'SCB_KONTOR',
                'SCB_ANSTÄLLDA',
                'SCB_VERKSAMHETSSTATUS',
                'SCB_JURIDISK_FORM',
                'SCB_FÖRETAGSÅLDER',
            ),
            'classes': ('collapse',),
        }),
        ('SCB - Datum', {
            'fields': ('SCB_STARTDATUM', 'SCB_REGISTRERINGSDATUM'),
            'classes': ('collapse',),
        }),
        ('SCB - Bransch', {
            'fields': ('SCB_BRANSCH_1', 'SCB_BRANSCH_2'),
            'classes': ('collapse',),
        }),
        ('SCB - Ekonomi', {
            'fields': ('SCB_OMSÄTTNING_ÅR', 'SCB_OMSÄTTNING_STORLEK'),
            'classes': ('collapse',),
        }),
        ('SCB - Kontakt', {
            'fields': ('SCB_TEL', 'SCB_MAIL'),
            'classes': ('collapse',),
        }),
        ('SCB - Status', {
            'fields': ('SCB_ARBETSGIVARE_STATUS',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = []  # Alla fält är redigerbara

    def sync_from_google_sheets(self, request, queryset):
        """
        Synkronisera data från Google Sheets (admin action)
        """
        try:
            # Hämta API key och Sheet ID från miljövariabler
            api_key = os.environ.get('GOOGLE_SHEETS_API_KEY')
            if not api_key:
                # Try legacy credentials format
                credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
                if credentials_json:
                    try:
                        credentials = json.loads(credentials_json)
                        # For service account, we can't use simple API key
                        # Let user know they should use the management command instead
                        self.message_user(
                            request,
                            'Google Sheets synkronisering kräver service account. '
                            'Använd management command: python manage.py sync_sheets --sheet-id=YOUR_ID',
                            messages.WARNING
                        )
                        return
                    except json.JSONDecodeError:
                        pass

                self.message_user(
                    request,
                    'GOOGLE_SHEETS_API_KEY eller GOOGLE_SHEETS_CREDENTIALS saknas i miljövariabler',
                    messages.ERROR
                )
                return

            sheet_id = os.environ.get('GOOGLE_SHEETS_SPREADSHEET_ID')
            if not sheet_id:
                self.message_user(
                    request,
                    'GOOGLE_SHEETS_SPREADSHEET_ID saknas i miljövariabler',
                    messages.ERROR
                )
                return

            # Hämta data från Google Sheets
            range_name = 'A:Z'  # Simplified range
            url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_name}?key={api_key}'

            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.message_user(
                    request,
                    f'Kunde inte hämta data från Google Sheets: HTTP {response.status_code}',
                    messages.ERROR
                )
                return

            data = response.json()
            rows = data.get('values', [])

            if not rows:
                self.message_user(request, 'Inga data hittades i sheetet', messages.WARNING)
                return

            # Första raden är headers
            headers = rows[0]

            # Uppdatera företag
            updated_count = 0
            created_count = 0

            for row in rows[1:]:  # Skip header row
                if not row:  # Skip empty rows
                    continue

                # Skapa dict med data
                row_data = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_data[header] = row[i]

                # Hitta eller skapa företag baserat på id
                company_id = row_data.get('id')
                if not company_id:
                    continue

                try:
                    company_id = int(company_id)
                except (ValueError, TypeError):
                    continue

                # Uppdatera eller skapa
                defaults = {}

                # Map sheet columns to model fields
                field_mapping = {
                    'NAMN': 'NAMN',
                    'SAJT': 'SAJT',
                    'BESKRIVNING': 'BESKRIVNING',
                    'STAD': 'STAD',
                    'STORSTOCKHOLM': 'STORSTOCKHOLM',
                    'URL_LOGOTYP': 'URL_LOGOTYP',
                    'URL_KÄLLA': 'URL_KÄLLA',
                    'AI_FÖRMÅGA_V2': 'AI_FÖRMÅGA_V2',
                    'BRANSCHKLUSTER_V2': 'BRANSCHKLUSTER_V2',
                    'ANSTÄLLDA_GRUPPERING_V2': 'ANSTÄLLDA_GRUPPERING_V2',
                    'OMSÄTTNING_GRUPPERING_V2': 'OMSÄTTNING_GRUPPERING_V2',
                    'Optimering & Automation': 'TILLAMPNING_OPTIMERING_AUTOMATION',
                    'Språk & Ljud': 'TILLAMPNING_SPRAK_LJUD',
                    'Prognos & Prediktion': 'TILLAMPNING_PROGNOS_PREDIKTION',
                    'Infrastruktur & Data': 'TILLAMPNING_INFRASTRUKTUR_DATA',
                    'Insikt & Analys': 'TILLAMPNING_INSIKT_ANALYS',
                    'Visuell AI': 'TILLAMPNING_VISUELL_AI',
                }

                for sheet_col, model_field in field_mapping.items():
                    if sheet_col in row_data:
                        value = row_data[sheet_col]

                        # Convert boolean fields
                        if model_field.startswith('TILLAMPNING_') or model_field == 'STORSTOCKHOLM':
                            value = value.lower() in ('true', 'yes', '1', 'ja') if value else False

                        defaults[model_field] = value

                company, created = AICompany.objects.update_or_create(
                    id=company_id,
                    defaults=defaults
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            self.message_user(
                request,
                f'Synkronisering klar: {created_count} skapade, {updated_count} uppdaterade',
                messages.SUCCESS
            )

        except Exception as e:
            self.message_user(
                request,
                f'Fel vid synkronisering: {str(e)}',
                messages.ERROR
            )

    sync_from_google_sheets.short_description = "Synkronisera från Google Sheets"

    def export_selected_to_csv(self, request, queryset):
        """
        Exportera markerade/filtrerade företag till CSV för batch-redigering
        """
        # Skapa filnamn med tidsstämpel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'foretagsdatabas_{timestamp}.csv'

        # Skapa HTTP-respons med CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # UTF-8 BOM för korrekt Excel-hantering av svenska tecken
        response.write('\ufeff')

        writer = csv.writer(response)

        # Skriv header med alla fältnamn
        field_names = [
            'id', 'NAMN', 'SAJT', 'BESKRIVNING', 'STAD', 'STORSTOCKHOLM',
            'URL_LOGOTYP', 'URL_KÄLLA',
            'AI_FÖRMÅGA_V2', 'BRANSCHKLUSTER_V2', 'ANSTÄLLDA_GRUPPERING_V2', 'OMSÄTTNING_GRUPPERING_V2',
            'TILLAMPNING_OPTIMERING_AUTOMATION', 'TILLAMPNING_SPRAK_LJUD', 'TILLAMPNING_PROGNOS_PREDIKTION',
            'TILLAMPNING_INFRASTRUKTUR_DATA', 'TILLAMPNING_INSIKT_ANALYS', 'TILLAMPNING_VISUELL_AI',
            'SCB_ORGNR', 'SCB_NAMN', 'SCB_ADRESS', 'SCB_POSTNR', 'SCB_STAD',
            'SCB_KONTOR', 'SCB_ANSTÄLLDA', 'SCB_VERKSAMHETSSTATUS',
            'SCB_JURIDISK_FORM', 'SCB_STARTDATUM', 'SCB_REGISTRERINGSDATUM',
            'SCB_BRANSCH_1', 'SCB_BRANSCH_2',
            'SCB_OMSÄTTNING_ÅR', 'SCB_OMSÄTTNING_STORLEK',
            'SCB_TEL', 'SCB_MAIL', 'SCB_ARBETSGIVARE_STATUS', 'SCB_FÖRETAGSÅLDER'
        ]
        writer.writerow(field_names)

        # Skriv data för varje företag
        for company in queryset:
            row = [
                company.id,
                company.NAMN,
                company.SAJT,
                company.BESKRIVNING,
                company.STAD,
                company.STORSTOCKHOLM,
                company.URL_LOGOTYP,
                company.URL_KÄLLA,
                company.AI_FÖRMÅGA_V2,
                company.BRANSCHKLUSTER_V2,
                company.ANSTÄLLDA_GRUPPERING_V2,
                company.OMSÄTTNING_GRUPPERING_V2,
                company.TILLAMPNING_OPTIMERING_AUTOMATION,
                company.TILLAMPNING_SPRAK_LJUD,
                company.TILLAMPNING_PROGNOS_PREDIKTION,
                company.TILLAMPNING_INFRASTRUKTUR_DATA,
                company.TILLAMPNING_INSIKT_ANALYS,
                company.TILLAMPNING_VISUELL_AI,
                company.SCB_ORGNR,
                company.SCB_NAMN,
                company.SCB_ADRESS,
                company.SCB_POSTNR,
                company.SCB_STAD,
                company.SCB_KONTOR,
                company.SCB_ANSTÄLLDA,
                company.SCB_VERKSAMHETSSTATUS,
                company.SCB_JURIDISK_FORM,
                company.SCB_STARTDATUM,
                company.SCB_REGISTRERINGSDATUM,
                company.SCB_BRANSCH_1,
                company.SCB_BRANSCH_2,
                company.SCB_OMSÄTTNING_ÅR,
                company.SCB_OMSÄTTNING_STORLEK,
                company.SCB_TEL,
                company.SCB_MAIL,
                company.SCB_ARBETSGIVARE_STATUS,
                company.SCB_FÖRETAGSÅLDER,
            ]
            writer.writerow(row)

        # Visa bekräftelse
        self.message_user(
            request,
            f'{queryset.count()} företag exporterades till {filename}',
            messages.SUCCESS
        )

        return response

    export_selected_to_csv.short_description = "Exportera markerade företag till CSV"

    # Registrera actions
    actions = ['sync_from_google_sheets', 'export_selected_to_csv']


# ============================================================================
# PublicViewConfiguration - Kolumnkonfiguration för publik vy
# ============================================================================

@admin.register(PublicViewConfiguration)
class PublicViewConfigurationAdmin(admin.ModelAdmin):
    """
    Admin för publik vy - kolumnkonfiguration
    """
    list_display = [
        'get_column_display_name',
        'show_on_desktop',
        'show_on_mobile',
        'display_order',
    ]

    list_editable = [
        'show_on_desktop',
        'show_on_mobile',
        'display_order',
    ]

    list_filter = [
        'show_on_desktop',
        'show_on_mobile',
    ]

    ordering = ['display_order', 'column_name']
    list_per_page = 100

    fieldsets = (
        ('Kolumn', {
            'fields': ('column_name',)
        }),
        ('Synlighet', {
            'fields': ('show_on_desktop', 'show_on_mobile')
        }),
        ('Sortering', {
            'fields': ('display_order',)
        }),
    )

    def get_column_display_name(self, obj):
        """Visa kolumnnamnet med läsbart namn"""
        return obj.get_column_name_display()
    get_column_display_name.short_description = "Kolumn"
    get_column_display_name.admin_order_field = 'column_name'

    def reset_to_defaults(self, request, queryset):
        """
        Återställer till standardkolumner
        """
        # Ta bort alla existerande konfigurationer
        PublicViewConfiguration.objects.all().delete()

        # Skapa standardkonfigurationer
        default_configs = [
            # Desktop defaults
            {'column_name': 'name', 'show_on_desktop': True, 'show_on_mobile': True, 'display_order': 0},
            {'column_name': 'description', 'show_on_desktop': True, 'show_on_mobile': False, 'display_order': 1},
            {'column_name': 'location_city', 'show_on_desktop': True, 'show_on_mobile': True, 'display_order': 2},
            {'column_name': 'municipality', 'show_on_desktop': True, 'show_on_mobile': False, 'display_order': 3},
            {'column_name': 'employee_size', 'show_on_desktop': True, 'show_on_mobile': True, 'display_order': 4},
            {'column_name': 'sectors', 'show_on_desktop': True, 'show_on_mobile': False, 'display_order': 5},
            {'column_name': 'website', 'show_on_desktop': True, 'show_on_mobile': False, 'display_order': 6},
        ]

        for config in default_configs:
            PublicViewConfiguration.objects.create(**config)

        self.message_user(
            request,
            f'Återställde till standardkonfiguration med {len(default_configs)} kolumner',
            messages.SUCCESS
        )

    reset_to_defaults.short_description = "Återställ till standardkolumner"

    def create_all_columns(self, request, queryset):
        """
        Skapar konfigurationer för alla tillgängliga kolumner
        """
        existing_columns = set(PublicViewConfiguration.objects.values_list('column_name', flat=True))
        all_columns = [choice[0] for choice in PublicViewConfiguration.COLUMN_CHOICES]

        created = 0
        for column_name in all_columns:
            if column_name not in existing_columns:
                PublicViewConfiguration.objects.create(
                    column_name=column_name,
                    show_on_desktop=True,
                    show_on_mobile=False,
                    display_order=999,
                )
                created += 1

        self.message_user(
            request,
            f'Skapade {created} nya kolumnkonfigurationer',
            messages.SUCCESS
        )

    create_all_columns.short_description = "Skapa alla kolumner"

    # Registrera actions
    actions = ['reset_to_defaults', 'create_all_columns']


# ============================================================================
# ErrorReport - Felanmälningar
# ============================================================================

@admin.register(ErrorReport)
class ErrorReportAdmin(admin.ModelAdmin):
    """
    Admin för felanmälningar
    """
    list_display = [
        'id',
        'get_company_name',
        'error_type',
        'subject',
        'status',
        'created_at',
    ]

    list_editable = ['status']

    list_filter = [
        'status',
        'error_type',
        'created_at',
    ]

    search_fields = [
        'company__NAMN',
        'subject',
        'description',
        'suggestion',
    ]

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Företag', {
            'fields': ('company',)
        }),
        ('Felanmälan', {
            'fields': ('error_type', 'subject', 'description', 'suggestion')
        }),
        ('Hantering', {
            'fields': ('status', 'admin_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-created_at']
    list_per_page = 50
    save_on_top = True

    def get_company_name(self, obj):
        """Visa företagsnamn, eller 'Företagsförslag' om det är ett nytt företag"""
        if obj.company:
            return obj.company.NAMN
        return "– Företagsförslag –"
    get_company_name.short_description = "Företag"
    get_company_name.admin_order_field = 'company__NAMN'

    def mark_as_resolved(self, request, queryset):
        """Markera valda felanmälningar som hanterade"""
        updated = queryset.update(status='resolved')
        self.message_user(
            request,
            f'{updated} felanmälan(ingar) markerades som hanterade',
            messages.SUCCESS
        )
    mark_as_resolved.short_description = "Markera som hanterade"

    def mark_as_in_progress(self, request, queryset):
        """Markera valda felanmälningar som under granskning"""
        updated = queryset.update(status='in_progress')
        self.message_user(
            request,
            f'{updated} felanmälan(ingar) markerades som under granskning',
            messages.SUCCESS
        )
    mark_as_in_progress.short_description = "Markera som under granskning"

    def mark_as_rejected(self, request, queryset):
        """Markera valda felanmälningar som avvisade"""
        updated = queryset.update(status='rejected')
        self.message_user(
            request,
            f'{updated} felanmälan(ingar) markerades som avvisade',
            messages.SUCCESS
        )
    mark_as_rejected.short_description = "Markera som avvisade"

    actions = ['mark_as_resolved', 'mark_as_in_progress', 'mark_as_rejected']
