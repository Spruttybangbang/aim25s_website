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

    # Bransch och sektor (kommaseparerade text-fält)
    BRANSCHKLUSTER_LITEN = models.TextField(blank=True, null=True, verbose_name="Branschkluster Liten")
    BRANSCHKLUSTER_STOR = models.TextField(blank=True, null=True, verbose_name="Branschkluster Stor")
    SEKTOR_SEMANTISK_MODELL = models.TextField(blank=True, null=True, verbose_name="Sektor (Semantisk Modell)")
    SEKTOR_DETERMINISTISK_MODELL_1 = models.TextField(blank=True, null=True, verbose_name="Sektor (Deterministisk 1)")
    SEKTOR_DETERMINISTISK_MODELL_2 = models.TextField(blank=True, null=True, verbose_name="Sektor (Deterministisk 2)")
    SEKTOR_GAMMAL = models.TextField(blank=True, null=True, verbose_name="Sektor (Gammal)")
    
    # Nya fält (version 2)
    AI_FÖRMÅGA_V2 = models.TextField(blank=True, null=True, verbose_name="AI-förmåga V2", db_column="AI-FÖRMÅGA_V2")
    BRANSCHKLUSTER_V2 = models.TextField(blank=True, null=True, verbose_name="Branschkluster V2")
    ANSTÄLLDA_GRUPPERING_V2 = models.TextField(blank=True, null=True, verbose_name="Anställda gruppering V2", db_column="ANSTÄLLDA_GRUPPERING_V2")
    OMSÄTTNING_GRUPPERING_V2 = models.TextField(blank=True, null=True, verbose_name="Omsättning gruppering V2", db_column="OMSÄTTNING_GRUPPERING_V2")


    # AI-förmågor (kommaseparerade text-fält)
    AI_FÖRMÅGA_SEMANTISK_MODELL = models.TextField(
        blank=True, null=True,
        verbose_name="AI-förmåga (Semantisk Modell)",
        db_column="AI-FÖRMÅGA_SEMANTISK_MODELL"
    )
    AI_FÖRMÅGA_GAMMAL = models.TextField(
        blank=True, null=True,
        verbose_name="AI-förmåga (Gammal)",
        db_column="AI-FÖRMÅGA_GAMMAL"
    )

    # Metadata
    KONFIDENS_SEMANTISK_MODELL = models.TextField(blank=True, null=True, verbose_name="Konfidens (Semantisk)")
    ORGANISATIONSTYP_GAMMAL = models.TextField(blank=True, null=True, verbose_name="Organisationstyp (Gammal)")

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
# GAMLA MODELLER (används ej längre, men behålls för kompatibilitet)
# ============================================================================

class Company(models.Model):
    """
    Huvudtabell för AI-företag
    """
    name = models.TextField(verbose_name="Företagsnamn")
    website = models.TextField(blank=True, null=True, verbose_name="Webbplats")
    type = models.TextField(blank=True, null=True, verbose_name="Typ")
    logo_url = models.TextField(blank=True, null=True, verbose_name="Logotyp URL")
    description = models.TextField(blank=True, null=True, verbose_name="Beskrivning")
    owner = models.TextField(blank=True, null=True, verbose_name="Ägare")
    location_city = models.TextField(blank=True, null=True, verbose_name="Stad")
    location_greater_stockholm = models.BooleanField(blank=True, null=True, verbose_name="Stor-Stockholm")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Senast uppdaterad")
    data_quality_score = models.IntegerField(default=0, blank=True, null=True, verbose_name="Datakvalitet")
    source_url = models.TextField(blank=True, null=True, verbose_name="Käll-URL")
    sector_vec_1 = models.TextField(blank=True, null=True, verbose_name="Sector Vec 1")
    sector_vec_2 = models.TextField(blank=True, null=True, verbose_name="Sector Vec 2")
    type_new = models.TextField(blank=True, null=True, verbose_name="Type New")
    description_new = models.TextField(blank=True, null=True, verbose_name="Description New")
    ai_capabilities_new = models.TextField(blank=True, null=True, verbose_name="Ai Capabilities New")
    sector_1_new = models.TextField(blank=True, null=True, verbose_name="Sector 1 New")
    sector_2_new = models.TextField(blank=True, null=True, verbose_name="Sector 2 New")
    confidence_newdata = models.TextField(blank=True, null=True, verbose_name="Confidence Newdata")

    class Meta:
        db_table = 'companies'
        verbose_name = "AI-företag"
        verbose_name_plural = "AI-företag"
        ordering = ['name']
        managed = False  # Django skapar inte tabellen, den finns redan

    def __str__(self):
        return self.name


class Sector(models.Model):
    """
    Sektorer/branscher
    """
    name = models.TextField(unique=True, verbose_name="Sektor")
    companies = models.ManyToManyField(
        Company,
        through='CompanySector',
        related_name='sectors',
        verbose_name="Företag"
    )

    class Meta:
        db_table = 'sectors'
        verbose_name = "Sektor"
        verbose_name_plural = "Sektorer"
        ordering = ['name']
        managed = False

    def __str__(self):
        return self.name


class CompanySector(models.Model):
    """
    Kopplingstabell: företag <-> sektorer
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='company_id', primary_key=True)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, db_column='sector_id')

    class Meta:
        db_table = 'company_sectors'
        unique_together = ('company', 'sector')
        managed = False


class Domain(models.Model):
    """
    Domäner/områden
    """
    name = models.TextField(unique=True, verbose_name="Domän")
    companies = models.ManyToManyField(
        Company,
        through='CompanyDomain',
        related_name='domains',
        verbose_name="Företag"
    )

    class Meta:
        db_table = 'domains'
        verbose_name = "Domän"
        verbose_name_plural = "Domäner"
        ordering = ['name']
        managed = False

    def __str__(self):
        return self.name


class CompanyDomain(models.Model):
    """
    Kopplingstabell: företag <-> domäner
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='company_id', primary_key=True)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, db_column='domain_id')

    class Meta:
        db_table = 'company_domains'
        unique_together = ('company', 'domain')
        managed = False


class AICapability(models.Model):
    """
    AI-kapaciteter
    """
    name = models.TextField(unique=True, verbose_name="AI-kapacitet")
    companies = models.ManyToManyField(
        Company,
        through='CompanyAICapability',
        related_name='ai_capabilities',
        verbose_name="Företag"
    )

    class Meta:
        db_table = 'ai_capabilities'
        verbose_name = "AI-kapacitet"
        verbose_name_plural = "AI-kapaciteter"
        ordering = ['name']
        managed = False

    def __str__(self):
        return self.name


class CompanyAICapability(models.Model):
    """
    Kopplingstabell: företag <-> AI-kapaciteter
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='company_id', primary_key=True)
    capability = models.ForeignKey(AICapability, on_delete=models.CASCADE, db_column='capability_id')

    class Meta:
        db_table = 'company_ai_capabilities'
        unique_together = ('company', 'capability')
        managed = False


class Dimension(models.Model):
    """
    Dimensioner
    """
    name = models.TextField(unique=True, verbose_name="Dimension")
    companies = models.ManyToManyField(
        Company,
        through='CompanyDimension',
        related_name='dimensions',
        verbose_name="Företag"
    )

    class Meta:
        db_table = 'dimensions'
        verbose_name = "Dimension"
        verbose_name_plural = "Dimensioner"
        ordering = ['name']
        managed = False

    def __str__(self):
        return self.name


class CompanyDimension(models.Model):
    """
    Kopplingstabell: företag <-> dimensioner
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='company_id', primary_key=True)
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, db_column='dimension_id')

    class Meta:
        db_table = 'company_dimensions'
        unique_together = ('company', 'dimension')
        managed = False


class SCBEnrichment(models.Model):
    """
    SCB-anrikningsdata för företag
    """
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='company_id',
        related_name='scb_enrichment',
        verbose_name="Företag"
    )
    organization_number = models.TextField(blank=True, null=True, verbose_name="Organisationsnummer")
    scb_company_name = models.TextField(blank=True, null=True, verbose_name="SCB Företagsnamn")
    co_address = models.TextField(blank=True, null=True, verbose_name="C/O Adress")
    post_address = models.TextField(blank=True, null=True, verbose_name="Postadress")
    post_code = models.TextField(blank=True, null=True, verbose_name="Postnummer")
    post_city = models.TextField(blank=True, null=True, verbose_name="Postort")
    municipality_code = models.TextField(blank=True, null=True, verbose_name="Kommunkod")
    municipality = models.TextField(blank=True, null=True, verbose_name="Kommun")
    county_code = models.TextField(blank=True, null=True, verbose_name="Länskod")
    county = models.TextField(blank=True, null=True, verbose_name="Län")
    num_workplaces = models.TextField(blank=True, null=True, verbose_name="Antal arbetsplatser")
    employee_size_code = models.TextField(blank=True, null=True, verbose_name="Anställningskod")
    employee_size = models.TextField(blank=True, null=True, verbose_name="Antal anställda")
    company_status_code = models.TextField(blank=True, null=True, verbose_name="Statuskod")
    company_status = models.TextField(blank=True, null=True, verbose_name="Status")
    legal_form_code = models.TextField(blank=True, null=True, verbose_name="Juridisk form kod")
    legal_form = models.TextField(blank=True, null=True, verbose_name="Juridisk form")
    start_date = models.TextField(blank=True, null=True, verbose_name="Startdatum")
    registration_date = models.TextField(blank=True, null=True, verbose_name="Registreringsdatum")
    industry_1_code = models.TextField(blank=True, null=True, verbose_name="Branschkod 1")
    industry_1 = models.TextField(blank=True, null=True, verbose_name="Bransch 1")
    industry_2_code = models.TextField(blank=True, null=True, verbose_name="Branschkod 2")
    industry_2 = models.TextField(blank=True, null=True, verbose_name="Bransch 2")
    revenue_year = models.TextField(blank=True, null=True, verbose_name="Omsättningsår")
    revenue_size_code = models.TextField(blank=True, null=True, verbose_name="Omsättningskod")
    revenue_size = models.TextField(blank=True, null=True, verbose_name="Omsättning")
    phone = models.TextField(blank=True, null=True, verbose_name="Telefon")
    email = models.TextField(blank=True, null=True, verbose_name="E-post")
    employer_status_code = models.TextField(blank=True, null=True, verbose_name="Arbetsgivarstatuskod")
    employer_status = models.TextField(blank=True, null=True, verbose_name="Arbetsgivarstatus")
    vat_status_code = models.TextField(blank=True, null=True, verbose_name="Momsstatuskod")
    vat_status = models.TextField(blank=True, null=True, verbose_name="Momsstatus")
    export_import = models.TextField(blank=True, null=True, verbose_name="Export/Import")

    class Meta:
        db_table = 'scb_enrichment'
        verbose_name = "SCB-anrikning"
        verbose_name_plural = "SCB-anrikningar"
        managed = False

    def __str__(self):
        return f"SCB data för {self.company.name}"


class SCBMatch(models.Model):
    """
    SCB-matchningsdata
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        db_column='company_id',
        related_name='scb_matches',
        verbose_name="Företag"
    )
    matched = models.IntegerField(verbose_name="Matchad")
    score = models.IntegerField(blank=True, null=True, verbose_name="Poäng")
    city = models.TextField(blank=True, null=True, verbose_name="Stad")
    payload = models.TextField(blank=True, null=True, verbose_name="Data")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Skapad")

    class Meta:
        db_table = 'scb_matches'
        verbose_name = "SCB-matchning"
        verbose_name_plural = "SCB-matchningar"
        managed = False

    def __str__(self):
        return f"Match för {self.company.name}"


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
