from django.db import models


class AICompany(models.Model):
    """
    Flat databas för AI-företag - direktimport från BETTER_DATA_FINAL.csv
    Alla kolumner är exakt som i CSV-filen för enkel hantering.
    """
    # Primärnyckel från CSV (behåller original-ID)
    id = models.IntegerField(primary_key=True, verbose_name="ID")

    # Grundläggande företagsdata
    NAMN = models.TextField(blank=True, null=True, verbose_name="Företagsnamn")
    SAJT = models.TextField(blank=True, null=True, verbose_name="Webbplats")
    BESKRIVNING = models.TextField(blank=True, null=True, verbose_name="Beskrivning")
    STAD = models.TextField(blank=True, null=True, verbose_name="Stad")
    STORSTOCKHOLM = models.BooleanField(blank=True, null=True, verbose_name="Stor-Stockholm")
    URL_LOGOTYP = models.TextField(blank=True, null=True, verbose_name="URL Logotyp")
    URL_KÄLLA = models.TextField(blank=True, null=True, verbose_name="URL Källa", db_column="URL_KÄLLA")

    # Nya fält (version 2)
    AI_FÖRMÅGA_V2 = models.TextField(blank=True, null=True, verbose_name="AI-förmåga V2", db_column="AI-FÖRMÅGA_V2")
    BRANSCHKLUSTER_V2 = models.TextField(blank=True, null=True, verbose_name="Branschkluster V2")
    ANSTÄLLDA_GRUPPERING_V2 = models.TextField(blank=True, null=True, verbose_name="Anställda gruppering V2", db_column="ANSTÄLLDA_GRUPPERING_V2")
    OMSÄTTNING_GRUPPERING_V2 = models.TextField(blank=True, null=True, verbose_name="Omsättning gruppering V2", db_column="OMSÄTTNING_GRUPPERING_V2")

    # AI-tillämpningar (användningsområden)
    TILLAMPNING_OPTIMERING_AUTOMATION = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name="Optimering & Automation",
        db_column="Optimering & Automation"
    )
    TILLAMPNING_SPRAK_LJUD = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name="Språk & Ljud",
        db_column="Språk & Ljud"
    )
    TILLAMPNING_PROGNOS_PREDIKTION = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name="Prognos & Prediktion",
        db_column="Prognos & Prediktion"
    )
    TILLAMPNING_INFRASTRUKTUR_DATA = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name="Infrastruktur & Data",
        db_column="Infrastruktur & Data"
    )
    TILLAMPNING_INSIKT_ANALYS = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name="Insikt & Analys",
        db_column="Insikt & Analys"
    )
    TILLAMPNING_VISUELL_AI = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name="Visuell AI",
        db_column="Visuell AI"
    )

    # SCB-data
    SCB_ORGNR = models.TextField(blank=True, null=True, verbose_name="SCB Organisationsnummer")
    SCB_NAMN = models.TextField(blank=True, null=True, verbose_name="SCB Namn")
    SCB_ADRESS = models.TextField(blank=True, null=True, verbose_name="SCB Adress")
    SCB_POSTNR = models.TextField(blank=True, null=True, verbose_name="SCB Postnummer")
    SCB_STAD = models.TextField(blank=True, null=True, verbose_name="SCB Stad")
    SCB_KONTOR = models.TextField(blank=True, null=True, verbose_name="SCB Antal kontor")
    SCB_ANSTÄLLDA = models.TextField(blank=True, null=True, verbose_name="SCB Antal anställda", db_column="SCB_ANSTÄLLDA")
    SCB_VERKSAMHETSSTATUS = models.TextField(blank=True, null=True, verbose_name="SCB Verksamhetsstatus")
    SCB_JURIDISK_FORM = models.TextField(blank=True, null=True, verbose_name="SCB Juridisk form")
    SCB_STARTDATUM = models.TextField(blank=True, null=True, verbose_name="SCB Startdatum")
    SCB_REGISTRERINGSDATUM = models.TextField(blank=True, null=True, verbose_name="SCB Registreringsdatum")
    SCB_BRANSCH_1 = models.TextField(blank=True, null=True, verbose_name="SCB Bransch 1")
    SCB_BRANSCH_2 = models.TextField(blank=True, null=True, verbose_name="SCB Bransch 2")
    SCB_OMSÄTTNING_ÅR = models.TextField(blank=True, null=True, verbose_name="SCB Omsättningsår", db_column="SCB_OMSÄTTNING_ÅR")
    SCB_OMSÄTTNING_STORLEK = models.TextField(blank=True, null=True, verbose_name="SCB Omsättning storlek")
    SCB_TEL = models.TextField(blank=True, null=True, verbose_name="SCB Telefon")
    SCB_MAIL = models.TextField(blank=True, null=True, verbose_name="SCB E-post")
    SCB_ARBETSGIVARE_STATUS = models.TextField(blank=True, null=True, verbose_name="SCB Arbetsgivare status")
    SCB_FÖRETAGSÅLDER = models.TextField(blank=True, null=True, verbose_name="SCB Företagsålder", db_column="SCB_FÖRETAGSÅLDER")

    class Meta:
        db_table = 'ai_companies'
        verbose_name = "Företagsdatabas"
        verbose_name_plural = "Företagsdatabas"
        ordering = ['NAMN']
        managed = True  # Django hanterar denna tabell

    def __str__(self):
        return self.NAMN or f"Företag {self.id}"

    # Hjälpmetoder för pipe-separerade fält
    def get_ai_formaga_v2_list(self):
        """
        Returnerar AI-förmågor V2 som en lista.

        Exempel:
            "NLP|Computer Vision|Robotics" → ["NLP", "Computer Vision", "Robotics"]
        """
        if not self.AI_FÖRMÅGA_V2:
            return []
        return [item.strip() for item in self.AI_FÖRMÅGA_V2.split('|') if item.strip()]

    def set_ai_formaga_v2_list(self, items):
        """
        Sätter AI-förmågor V2 från en lista.

        Exempel:
            ["NLP", "Computer Vision", "Robotics"] → "NLP|Computer Vision|Robotics"
        """
        if not items:
            self.AI_FÖRMÅGA_V2 = None
        else:
            self.AI_FÖRMÅGA_V2 = '|'.join(str(item).strip() for item in items if item)

    def get_branschkluster_v2_list(self):
        """
        Returnerar branschkluster V2 som en lista (ifall det också är pipe-separerat).
        """
        if not self.BRANSCHKLUSTER_V2:
            return []
        return [item.strip() for item in self.BRANSCHKLUSTER_V2.split('|') if item.strip()]

    def set_branschkluster_v2_list(self, items):
        """
        Sätter branschkluster V2 från en lista.
        """
        if not items:
            self.BRANSCHKLUSTER_V2 = None
        else:
            self.BRANSCHKLUSTER_V2 = '|'.join(str(item).strip() for item in items if item)


# ============================================================================
# GAMLA MODELLER TOGS BORT 2025-12-18
# Deprecated models (Company, Sector, Domain, AICapability, Dimension,
# CompanySector, CompanyDomain, CompanyAICapability, CompanyDimension,
# SCBEnrichment, SCBMatch) raderades - användes inte längre
# ============================================================================


class PublicViewConfiguration(models.Model):
    """
    Konfiguration för publik vy - vilka kolumner som ska visas
    """
    COLUMN_CHOICES = [
        # Basic fields (mapped to frontend expectations)
        ('name', 'Företag'),
        ('bransch', 'Bransch'),
        ('website', 'Webbplats'),
        ('description', 'Beskrivning'),
        ('location_city', 'Stad'),
        ('location_greater_stockholm', 'Stor-Stockholm'),
        ('logo_url', 'Logotyp URL'),
        ('source_url', 'Käll-URL'),

        # SCB fields
        ('organization_number', 'Organisationsnummer'),
        ('municipality', 'Kommun'),
        ('employee_size', 'Antal anställda'),
        ('legal_form', 'Juridisk form'),
        ('industry_1', 'Bransch 1'),
        ('industry_2', 'Bransch 2'),
        ('phone', 'Telefon'),
        ('email', 'E-post'),

        # Relationships (comma-separated in new model)
        ('sectors', 'Område'),
        ('ai_capabilities', 'AI-inriktning'),
    ]

    column_name = models.CharField(max_length=50, choices=COLUMN_CHOICES, unique=True, verbose_name="Kolumn")
    custom_label = models.CharField(max_length=100, blank=True, null=True, verbose_name="Anpassad etikett",
                                     help_text="Valfritt: Anpassat namn som visas i den publika vyn. Lämna tomt för att använda standardnamnet.")
    show_on_desktop = models.BooleanField(default=True, verbose_name="Visa på desktop")
    show_on_mobile = models.BooleanField(default=False, verbose_name="Visa på mobil")
    display_order = models.IntegerField(default=0, verbose_name="Visningsordning")

    class Meta:
        ordering = ['display_order', 'column_name']
        verbose_name = "Publik vy - kolumnkonfiguration"
        verbose_name_plural = "Publik vy - kolumnkonfigurationer"

    def __str__(self):
        return f"{self.get_column_name_display()} (Desktop: {self.show_on_desktop}, Mobil: {self.show_on_mobile})"


class ErrorReport(models.Model):
    """
    Felanmälningar för företag
    """
    ERROR_TYPE_CHOICES = [
        ('incorrect_info', 'Felaktig information'),
        ('company_not_exist', 'Företaget finns ej'),
        ('missing_data', 'Saknad data'),
        ('suggestion_new_company', 'Förslag på nytt företag'),
        ('other', 'Annat'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Väntar'),
        ('in_progress', 'Under granskning'),
        ('resolved', 'Hanterad'),
        ('rejected', 'Avvisad'),
    ]

    company = models.ForeignKey(
        AICompany,
        on_delete=models.CASCADE,
        related_name='error_reports',
        verbose_name="Företag",
        null=True,
        blank=True,
        help_text="Null för företagsförslag"
    )
    error_type = models.CharField(
        max_length=50,
        choices=ERROR_TYPE_CHOICES,
        verbose_name="Typ av fel"
    )
    subject = models.CharField(max_length=200, verbose_name="Ämne")
    description = models.TextField(verbose_name="Beskrivning")
    suggestion = models.TextField(blank=True, verbose_name="Förslag på korrigering")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Uppdaterad")
    admin_notes = models.TextField(blank=True, verbose_name="Admin-anteckningar")

    class Meta:
        db_table = 'error_reports'
        verbose_name = "Felanmälan"
        verbose_name_plural = "Felanmälningar"
        ordering = ['-created_at']

    def __str__(self):
        if self.company:
            return f"{self.company.NAMN} – {self.subject}"
        else:
            return f"Företagsförslag – {self.subject or 'Inget ämne'}"

    @property
    def is_resolved(self):
        return self.status == 'resolved'
