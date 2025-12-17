from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
import json
from .models import AICompany, PublicViewConfiguration


def login_view(request):
    """
    Hanterar inloggning för studenter
    """
    # Om användaren redan är inloggad, redirect till public_view
    if request.user.is_authenticated:
        return redirect('public_view')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('public_view')
        else:
            return render(request, 'companies/login.html', {
                'error': 'Ogiltigt användarnamn eller lösenord'
            })

    return render(request, 'companies/login.html')


def logout_view(request):
    """
    Hanterar utloggning
    """
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def companies_list(request):
    """
    Huvudvy för att visa företagslista (kräver inloggning)
    Stöder filtrering, sökning och paginering
    """
    # Hämta alla företag
    companies = AICompany.objects.all()

    # Sökning
    search_query = request.GET.get('search', '').strip()
    if search_query:
        companies = companies.filter(
            Q(NAMN__icontains=search_query) |
            Q(BESKRIVNING__icontains=search_query) |
            Q(STAD__icontains=search_query) |
            Q(SCB_STAD__icontains=search_query)
        )

    # Filter: Branschkluster Liten
    bransch_filter = request.GET.get('bransch', '')
    if bransch_filter:
        companies = companies.filter(BRANSCHKLUSTER_LITEN__icontains=bransch_filter)

    # Filter: Stor-Stockholm
    stockholm_filter = request.GET.get('stockholm', '')
    if stockholm_filter == 'yes':
        companies = companies.filter(STORSTOCKHOLM=True)
    elif stockholm_filter == 'no':
        companies = companies.filter(Q(STORSTOCKHOLM=False) | Q(STORSTOCKHOLM__isnull=True))

    # Paginering (50 per sida)
    paginator = Paginator(companies, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Hämta alla unika filter-alternativ
    all_bransch = AICompany.objects.exclude(BRANSCHKLUSTER_LITEN__isnull=True).exclude(BRANSCHKLUSTER_LITEN='').values_list('BRANSCHKLUSTER_LITEN', flat=True).distinct().order_by('BRANSCHKLUSTER_LITEN')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'bransch_filter': bransch_filter,
        'stockholm_filter': stockholm_filter,
        'all_bransch': all_bransch,
    }

    return render(request, 'companies/companies_list.html', context)


@login_required(login_url='login')
def public_view(request):
    """
    Renderar den publika vyn för att visa företag
    """
    return render(request, 'companies/public_view.html')


@login_required(login_url='login')
def staging_view(request):
    """
    Staging-version av public view (endast tillgänglig lokalt när DEBUG=True)
    """
    return render(request, 'companies/public_view_staging.html')


def get_column_config(request):
    """
    API endpoint för att hämta kolumnkonfiguration
    """
    # Hämta device type från query parameter (desktop eller mobile)
    device_type = request.GET.get('device', 'desktop')

    # Hämta kolumner baserat på device type
    if device_type == 'mobile':
        configs = PublicViewConfiguration.objects.filter(show_on_mobile=True)
    else:
        configs = PublicViewConfiguration.objects.filter(show_on_desktop=True)

    # Om ingen konfiguration finns, returnera defaultkolumner
    if not configs:
        default_columns = _get_default_columns(device_type)
        return JsonResponse({
            'columns': default_columns,
            'using_defaults': True
        })

    # Bygg kolumnlista med antingen custom_label eller standardetikett
    columns = []
    for config in configs:
        # Använd custom_label om det finns, annars get_column_name_display()
        label = config.custom_label if config.custom_label else config.get_column_name_display()
        columns.append({
            'column_name': config.column_name,
            'label': label,
            'display_order': config.display_order
        })

    return JsonResponse({
        'columns': columns,
        'using_defaults': False
    })


def _get_default_columns(device_type):
    """
    Returnerar nya standardkolumner
    """
    if device_type == 'mobile':
        return [
            {'column_name': 'name', 'label': 'Företag', 'display_order': 0},
            {'column_name': 'bransch', 'label': 'Bransch', 'display_order': 1},
            {'column_name': 'location_city', 'label': 'Ort', 'display_order': 2},
        ]
    else:
        return [
            {'column_name': 'name', 'label': 'Företag', 'display_order': 0},
            {'column_name': 'bransch', 'label': 'Bransch', 'display_order': 1},
            {'column_name': 'sectors', 'label': 'Område', 'display_order': 2},
            {'column_name': 'ai_capabilities', 'label': 'AI-typ', 'display_order': 3},
            {'column_name': 'location_city', 'label': 'Ort', 'display_order': 4},
        ]


def get_companies(request):
    """
    API endpoint för att hämta företagsdata
    """
    # Hämta alla företag
    companies = AICompany.objects.all()

    # Sök
    search = request.GET.get('search', '')
    if search:
        companies = companies.filter(
            Q(NAMN__icontains=search) |
            Q(BESKRIVNING__icontains=search) |
            Q(STAD__icontains=search) |
            Q(SCB_STAD__icontains=search) |
            Q(SCB_ORGNR__icontains=search)
        )

    # Filter: Stor-Stockholm
    stockholm = request.GET.get('stockholm', '')
    if stockholm == 'true':
        companies = companies.filter(STORSTOCKHOLM=True)

    # Filter: Bransch (multi-select)
    bransch_filters = request.GET.getlist('bransch')
    if bransch_filters:
        bransch_q = Q()
        for b in bransch_filters:
            bransch_q |= Q(BRANSCHKLUSTER_V2__iexact=b)
        companies = companies.filter(bransch_q)

    # Filter: Antal anställda (V2) (multi-select)
    anstallda_filters = request.GET.getlist('anstallda')
    if anstallda_filters:
        companies = companies.filter(ANSTÄLLDA_GRUPPERING_V2__in=anstallda_filters)

    # Filter: Omsättning (V2) (multi-select)
    omsattning_filters = request.GET.getlist('omsattning')
    if omsattning_filters:
        companies = companies.filter(OMSÄTTNING_GRUPPERING_V2__in=omsattning_filters)

    # Filter: Registrerad arbetsgivare
    arbetsgivare = request.GET.get('arbetsgivare', '')
    if arbetsgivare == 'true':
        companies = companies.filter(SCB_ARBETSGIVARE_STATUS='Är registrerad som vanlig arbetsgivare')

    # Filter: AI-inriktning
    ai_inriktning = request.GET.get('ai_inriktning', '')
    if ai_inriktning:
        companies = companies.filter(AI_FÖRMÅGA_V2__icontains=ai_inriktning)

    # Filter: Tag (för klickbara taggar i AI-förmåga)
    tag = request.GET.get('tag', '')
    if tag:
        companies = companies.filter(
            Q(AI_FÖRMÅGA_V2__icontains=tag)
        )

    # Filter: Tillämpning (multi-select)
    tillampning_filters = request.GET.getlist('tillampning')
    if tillampning_filters:
        tillampning_q = Q()

        # Map frontend labels to backend field names
        tillampning_mapping = {
            'Optimering & Automation': 'TILLAMPNING_OPTIMERING_AUTOMATION',
            'Språk & Ljud': 'TILLAMPNING_SPRAK_LJUD',
            'Prognos & Prediktion': 'TILLAMPNING_PROGNOS_PREDIKTION',
            'Infrastruktur & Data': 'TILLAMPNING_INFRASTRUKTUR_DATA',
            'Insikt & Analys': 'TILLAMPNING_INSIKT_ANALYS',
            'Visuell AI': 'TILLAMPNING_VISUELL_AI',
        }

        # Build OR query for selected tillämpningar
        for tillampning in tillampning_filters:
            field_name = tillampning_mapping.get(tillampning)
            if field_name:
                tillampning_q |= Q(**{field_name: True})

        if tillampning_q:
            companies = companies.filter(tillampning_q)

    # Paginering
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    start = (page - 1) * per_page
    end = start + per_page

    total = companies.count()
    companies_page = companies[start:end]

    # Serialisera data
    data = []
    for company in companies_page:
        company_data = {
            'id': company.id,
            'name': company.NAMN or '',
            'bransch': company.BRANSCHKLUSTER_V2 or '',
            'website': company.SAJT or '',
            'description': company.BESKRIVNING or '',
            'location_city': company.STAD or '',
            'location_greater_stockholm': company.STORSTOCKHOLM,
            'logo_url': company.URL_LOGOTYP or '',
            'source_url': company.URL_KÄLLA or '',

            # SCB data (now direct fields)
            'organization_number': company.SCB_ORGNR or '',
            'scb_namn': company.SCB_NAMN or '',
            'scb_adress': company.SCB_ADRESS or '',
            'scb_postnr': company.SCB_POSTNR or '',
            'municipality': company.SCB_STAD or '',
            'scb_kontor': company.SCB_KONTOR or '',
            'employee_size': company.SCB_ANSTÄLLDA or '',
            'scb_omsattning': company.SCB_OMSÄTTNING_STORLEK or '',
            'scb_alder': company.SCB_FÖRETAGSÅLDER or '',
            'legal_form': company.SCB_JURIDISK_FORM or '',
            'industry_1': company.SCB_BRANSCH_1 or '',
            'industry_2': company.SCB_BRANSCH_2 or '',
            'phone': company.SCB_TEL or '',
            'email': company.SCB_MAIL or '',

            # V2 fields (pipe-separated)
            'ai_capabilities': company.AI_FÖRMÅGA_V2 or '',

            # Tillämpning fields (Boolean)
            'tillampning_optimering_automation': company.TILLAMPNING_OPTIMERING_AUTOMATION,
            'tillampning_sprak_ljud': company.TILLAMPNING_SPRAK_LJUD,
            'tillampning_prognos_prediktion': company.TILLAMPNING_PROGNOS_PREDIKTION,
            'tillampning_infrastruktur_data': company.TILLAMPNING_INFRASTRUKTUR_DATA,
            'tillampning_insikt_analys': company.TILLAMPNING_INSIKT_ANALYS,
            'tillampning_visuell_ai': company.TILLAMPNING_VISUELL_AI,

            # Fields that don't exist in new model (removed from frontend)
            'type': None,
            'type_new': None,
            'owner': None,
            'data_quality_score': None,
            'sector_vec_1': None,
            'sector_vec_2': None,
            'county': None,
            'post_city': company.SCB_STAD or '',  # Same as municipality
            'domains': '',
            'dimensions': '',
        }

        data.append(company_data)

    return JsonResponse({
        'companies': data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
    })


def get_filter_options(request):
    """
    API endpoint för att hämta alla tillgängliga filteralternativ
    """
    bransch_options = AICompany.objects.exclude(
        BRANSCHKLUSTER_V2__isnull=True
    ).exclude(
        BRANSCHKLUSTER_V2=''
    ).values_list('BRANSCHKLUSTER_V2', flat=True).distinct().order_by('BRANSCHKLUSTER_V2')

    anstallda_options = AICompany.objects.exclude(
        ANSTÄLLDA_GRUPPERING_V2__isnull=True
    ).exclude(
        ANSTÄLLDA_GRUPPERING_V2=''
    ).values_list('ANSTÄLLDA_GRUPPERING_V2', flat=True).distinct().order_by('ANSTÄLLDA_GRUPPERING_V2')

    omsattning_options = AICompany.objects.exclude(
        OMSÄTTNING_GRUPPERING_V2__isnull=True
    ).exclude(
        OMSÄTTNING_GRUPPERING_V2=''
    ).values_list('OMSÄTTNING_GRUPPERING_V2', flat=True).distinct().order_by('OMSÄTTNING_GRUPPERING_V2')

    # Hämta alla unika AI-förmågor från AI_FÖRMÅGA_V2
    ai_inriktning_set = set()
    ai_inriktning_values = AICompany.objects.exclude(
        AI_FÖRMÅGA_V2__isnull=True
    ).exclude(
        AI_FÖRMÅGA_V2=''
    ).values_list('AI_FÖRMÅGA_V2', flat=True)

    for value in ai_inriktning_values:
        # Splitta på pipe-tecken och lägg till varje individuell förmåga
        if value:
            capabilities = [cap.strip() for cap in value.split('|') if cap.strip()]
            ai_inriktning_set.update(capabilities)

    ai_inriktning_options = sorted(list(ai_inriktning_set))

    return JsonResponse({
        'bransch': list(bransch_options),
        'anstallda': list(anstallda_options),
        'omsattning': list(omsattning_options),
        'ai_inriktning': ai_inriktning_options,
    })


@require_http_methods(["POST"])
def report_error(request):
    """
    API endpoint för att skapa felanmälan för ett företag eller företagsförslag
    """
    try:
        data = json.loads(request.body)
        error_type = data.get('error_type')

        if not error_type:
            return JsonResponse({'error': 'Missing error_type'}, status=400)

        # Import ErrorReport model
        from .models import ErrorReport

        # Handle company suggestions differently from error reports
        if error_type == 'suggestion_new_company':
            # For company suggestions, company_id is not required
            company = None
            company_name = data.get('company_name')
            company_website = data.get('company_website')

            # Validate required fields for suggestions
            if not company_name or not company_website:
                return JsonResponse({
                    'success': False,
                    'error': 'Företagsnamn och hemsida är obligatoriska'
                }, status=400)

            # Build structured description with all suggestion data
            description_parts = [
                f"Företagsnamn: {company_name}",
                f"Hemsida: {company_website}"
            ]

            additional_info = data.get('additional_info', '').strip()
            if additional_info:
                description_parts.append(f"\nYtterligare information:\n{additional_info}")

            description = '\n'.join(description_parts)
            subject = f"Företagsförslag: {company_name}"
            suggestion = ''
            success_message = 'Tack för ditt företagsförslag!'

        else:
            # For error reports, company_id is required
            company_id = data.get('company_id')
            description = data.get('description')
            suggestion = data.get('suggestion', '')

            if not company_id or not description:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Get company
            try:
                company = AICompany.objects.get(id=company_id)
            except AICompany.DoesNotExist:
                return JsonResponse({'error': 'Company not found'}, status=404)

            subject = f"{dict(ErrorReport.ERROR_TYPE_CHOICES).get(error_type, error_type)} - {company.NAMN}"
            success_message = 'Felanmälan mottagen'

        # Create error report or suggestion
        error_report = ErrorReport.objects.create(
            company=company,
            error_type=error_type,
            subject=subject,
            description=description,
            suggestion=suggestion,
            status='pending'
        )

        return JsonResponse({
            'success': True,
            'message': success_message,
            'report_id': error_report.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f'Error creating report: {str(e)}')
        return JsonResponse({'error': 'Server error'}, status=500)


@login_required(login_url='login')
def get_database_stats(request):
    """
    Returnera aggregerad statistik för database insights modal
    """
    companies = AICompany.objects.all()
    total_count = companies.count()

    # 1. Geographic Distribution (top 5 cities + others)
    city_stats = companies.exclude(
        STAD__isnull=True
    ).exclude(
        STAD=''
    ).values('STAD').annotate(count=Count('id')).order_by('-count')[:5]

    city_data = list(city_stats)
    top_5_total = sum(item['count'] for item in city_data)
    others_count = total_count - top_5_total

    if others_count > 0:
        city_data.append({'STAD': 'Övriga', 'count': others_count})

    # 2. Industry Distribution (bransch)
    bransch_stats = companies.exclude(
        BRANSCHKLUSTER_V2__isnull=True
    ).exclude(
        BRANSCHKLUSTER_V2=''
    ).values('BRANSCHKLUSTER_V2').annotate(count=Count('id')).order_by('-count')

    # 3. Application Distribution (6 TILLAMPNING fields)
    application_stats = {
        'Optimering & Automation': companies.filter(TILLAMPNING_OPTIMERING_AUTOMATION=True).count(),
        'Språk & Ljud': companies.filter(TILLAMPNING_SPRAK_LJUD=True).count(),
        'Prognos & Prediktion': companies.filter(TILLAMPNING_PROGNOS_PREDIKTION=True).count(),
        'Infrastruktur & Data': companies.filter(TILLAMPNING_INFRASTRUKTUR_DATA=True).count(),
        'Insikt & Analys': companies.filter(TILLAMPNING_INSIKT_ANALYS=True).count(),
        'Visuell AI': companies.filter(TILLAMPNING_VISUELL_AI=True).count(),
    }

    # 4. Revenue Distribution
    revenue_stats = companies.exclude(
        OMSÄTTNING_GRUPPERING_V2__isnull=True
    ).exclude(
        OMSÄTTNING_GRUPPERING_V2=''
    ).values('OMSÄTTNING_GRUPPERING_V2').annotate(count=Count('id')).order_by('-count')

    # 5. Employee Distribution
    employee_stats = companies.exclude(
        ANSTÄLLDA_GRUPPERING_V2__isnull=True
    ).exclude(
        ANSTÄLLDA_GRUPPERING_V2=''
    ).values('ANSTÄLLDA_GRUPPERING_V2').annotate(count=Count('id')).order_by('-count')

    return JsonResponse({
        'total_companies': total_count,
        'geographic': city_data,
        'bransch': list(bransch_stats),
        'applications': application_stats,
        'revenue': list(revenue_stats),
        'employees': list(employee_stats),
    })
