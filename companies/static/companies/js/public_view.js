// ===== CONFIGURATION =====
const API_BASE = '';
const API_COMPANIES = '/api/companies/';
const API_COLUMNS = '/api/columns/';
const API_FILTER_OPTIONS = '/api/filter-options/';

// Column display names mapping (Swedish)
const COLUMN_LABELS = {
    'name': 'Företagsnamn',
    'bransch': 'Bransch',
    'website': 'Webbplats',
    'type': 'Typ',
    'type_new': 'Typ (ny)',
    'description': 'Beskrivning',
    'location_city': 'Ort',
    'location_greater_stockholm': 'Stor-Stockholm',
    'owner': 'Ägare',
    'logo_url': 'Logotyp URL',
    'data_quality_score': 'Datakvalitet',
    'source_url': 'Käll-URL',
    'sector_vec_1': 'Sektor Vec 1',
    'sector_vec_2': 'Sektor Vec 2',
    'organization_number': 'Org.nr',
    'municipality': 'Ort',
    'county': 'Län',
    'employee_size': 'Antal anställda',
    'legal_form': 'Juridisk form',
    'industry_1': 'Bransch 1',
    'industry_2': 'Bransch 2',
    'phone': 'Telefon',
    'email': 'E-post',
    'post_city': 'Postort',
    'sectors': 'Sektorer',
    'domains': 'Domäner',
    'ai_capabilities': 'AI-inriktning',
    'dimensions': 'Dimensioner',
};

// ===== STATE =====
let currentPage = 1;
let totalPages = 1;
let currentSearch = '';
let currentColumns = [];
let isMobile = false;
let currentFilters = {
    stockholm: false,
    arbetsgivare: false,
    bransch: '',
    ai_inriktning: '',
    anstallda: '',
    omsattning: '',
    tag: ''
};

// Battery bar state
let totalCompaniesInDB = 0;        // Cachat värde från första laddningen
let currentDisplayedCount = 0;     // För smooth counter animation

// ===== HELPER FUNCTIONS FOR FILTERS =====

// Kontrollera om några filter är aktiva
function hasActiveFilters() {
    return currentFilters.stockholm ||
           currentFilters.arbetsgivare ||
           currentFilters.bransch ||
           currentFilters.ai_inriktning ||
           currentFilters.anstallda ||
           currentFilters.omsattning ||
           currentFilters.tag ||
           currentSearch;
}

// Uppdatera stats-text dynamiskt
function updateStatsDisplay(totalCompanies, hasFilters) {
    const statsDisplay = document.getElementById('statsDisplay');
    if (!statsDisplay) return;

    if (hasFilters) {
        statsDisplay.textContent = `Visar nu ${totalCompanies} företag`;
    } else {
        statsDisplay.textContent = `Leta bland ${totalCompanies} företag i hela Sverige!`;
    }
}

// Skapa en enskild filter pill
function createFilterPill(label, onRemove) {
    const pill = document.createElement('div');
    pill.className = 'filter-pill';

    const labelSpan = document.createElement('span');
    labelSpan.textContent = label;

    const removeBtn = document.createElement('span');
    removeBtn.className = 'filter-pill-remove';
    removeBtn.innerHTML = '&times;';
    removeBtn.onclick = onRemove;

    pill.appendChild(labelSpan);
    pill.appendChild(removeBtn);

    return pill;
}

// Rendera aktiva filter pills
function renderActiveFilterPills() {
    const container = document.getElementById('activeFiltersContainer');
    const pillsDiv = document.getElementById('activeFiltersPills');

    if (!container || !pillsDiv) return;

    // Töm befintliga pills
    pillsDiv.innerHTML = '';

    const pills = [];

    // Sök-pill
    if (currentSearch) {
        pills.push(createFilterPill(`Sök: "${currentSearch}"`, () => {
            currentSearch = '';
            document.getElementById('searchInput').value = '';
            currentPage = 1;
            loadCompanies();
        }));
    }

    // Stockholm-pill
    if (currentFilters.stockholm) {
        pills.push(createFilterPill('Stor-Stockholm', () => {
            currentFilters.stockholm = false;
            document.getElementById('stockholmFilter').checked = false;
            currentPage = 1;
            loadCompanies();
        }));
    }

    // Arbetsgivare-pill
    if (currentFilters.arbetsgivare) {
        pills.push(createFilterPill('Registrerad arbetsgivare', () => {
            currentFilters.arbetsgivare = false;
            document.getElementById('arbetsgivareFilter').checked = false;
            currentPage = 1;
            loadCompanies();
        }));
    }

    // Bransch-pill
    if (currentFilters.bransch) {
        pills.push(createFilterPill(`Bransch: ${currentFilters.bransch}`, () => {
            currentFilters.bransch = '';
            document.getElementById('branschFilter').value = '';
            currentPage = 1;
            loadCompanies();
        }));
    }

    // AI-inriktning-pill
    if (currentFilters.ai_inriktning) {
        pills.push(createFilterPill(`AI-inriktning: ${currentFilters.ai_inriktning}`, () => {
            currentFilters.ai_inriktning = '';
            document.getElementById('aiInriktningFilter').value = '';
            currentPage = 1;
            loadCompanies();
        }));
    }

    // Anställda-pill
    if (currentFilters.anstallda) {
        pills.push(createFilterPill(`Anställda: ${currentFilters.anstallda}`, () => {
            currentFilters.anstallda = '';
            document.getElementById('anstalldaFilter').value = '';
            currentPage = 1;
            loadCompanies();
        }));
    }

    // Omsättning-pill
    if (currentFilters.omsattning) {
        pills.push(createFilterPill(`Omsättning: ${currentFilters.omsattning}`, () => {
            currentFilters.omsattning = '';
            document.getElementById('omsattningFilter').value = '';
            currentPage = 1;
            loadCompanies();
        }));
    }

    // Tag-pill (från klickbara taggar)
    if (currentFilters.tag) {
        pills.push(createFilterPill(`AI-inriktning: ${currentFilters.tag}`, () => {
            currentFilters.tag = '';
            currentPage = 1;
            loadCompanies();
        }));
    }

    // Lägg till pills i DOM
    pills.forEach(pill => pillsDiv.appendChild(pill));

    // Visa/dölj container baserat på om det finns pills
    container.style.display = pills.length > 0 ? 'block' : 'none';
}

// ===== BATTERY BAR VISUALIZATION =====

/**
 * Uppdatera batteristapelns fyllnad och counter
 * @param {number} currentCount - Antal filtrerade företag
 * @param {number} totalCount - Totalt antal företag i databasen
 */
function updateBatteryBar(currentCount, totalCount) {
    const batteryFill = document.getElementById('batteryFill');
    const batteryCounter = document.getElementById('batteryCounter');

    if (!batteryFill || !batteryCounter) {
        console.warn('Battery bar elements not found');
        return;
    }

    // Beräkna fyllnadsprocent
    const percentage = totalCount > 0 ? (currentCount / totalCount) * 100 : 0;

    // Uppdatera fyllnadsnivå (CSS transition hanterar animationen)
    batteryFill.style.height = `${percentage}%`;

    // Animera counter från gammalt till nytt värde
    animateCounter(batteryCounter, currentDisplayedCount, currentCount, 300);

    // Uppdatera cached värde
    currentDisplayedCount = currentCount;
}

/**
 * Animera en counter från ett värde till ett annat
 * @param {HTMLElement} element - DOM-elementet att uppdatera
 * @param {number} start - Startvärde
 * @param {number} end - Slutvärde
 * @param {number} duration - Duration i millisekunder
 */
function animateCounter(element, start, end, duration) {
    const startTime = performance.now();
    const difference = end - start;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease-out cubic för smooth slow-down
        const easedProgress = 1 - Math.pow(1 - progress, 3);

        const currentValue = Math.round(start + difference * easedProgress);
        element.textContent = currentValue;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    checkDeviceType();
    setupEventListeners();
    setupFilterListeners();
    setupModalHandlers();
    loadFilterOptions();
    loadData();

    // Re-check device type on resize
    window.addEventListener('resize', () => {
        const wasMobile = isMobile;
        checkDeviceType();
        if (wasMobile !== isMobile) {
            loadData(); // Reload with appropriate columns
        }
    });
});

// ===== DEVICE DETECTION =====
function checkDeviceType() {
    isMobile = window.innerWidth <= 768;
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Search
    document.getElementById('searchButton').addEventListener('click', handleSearch);
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // I feel lucky button
    document.getElementById('luckyButton').addEventListener('click', handleLuckyClick);

    // Pagination
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadCompanies();
        }
    });

    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadCompanies();
        }
    });
}

function setupFilterListeners() {
    document.getElementById('stockholmFilter').addEventListener('change', (e) => {
        currentFilters.stockholm = e.target.checked;
        currentPage = 1;
        loadCompanies();
    });

    document.getElementById('arbetsgivareFilter').addEventListener('change', (e) => {
        currentFilters.arbetsgivare = e.target.checked;
        currentPage = 1;
        loadCompanies();
    });

    document.getElementById('branschFilter').addEventListener('change', (e) => {
        currentFilters.bransch = e.target.value;
        currentPage = 1;
        loadCompanies();
    });

    document.getElementById('aiInriktningFilter').addEventListener('change', (e) => {
        currentFilters.ai_inriktning = e.target.value;
        currentPage = 1;
        loadCompanies();
    });

    document.getElementById('anstalldaFilter').addEventListener('change', (e) => {
        currentFilters.anstallda = e.target.value;
        currentPage = 1;
        loadCompanies();
    });

    document.getElementById('omsattningFilter').addEventListener('change', (e) => {
        currentFilters.omsattning = e.target.value;
        currentPage = 1;
        loadCompanies();
    });

    document.getElementById('clearFilters').addEventListener('click', () => {
        // Rensa filter
        currentFilters = {
            stockholm: false,
            arbetsgivare: false,
            bransch: '',
            ai_inriktning: '',
            anstallda: '',
            omsattning: '',
            tag: ''
        };

        // Rensa sökning
        currentSearch = '';

        // Återställ UI
        document.getElementById('searchInput').value = '';
        document.getElementById('stockholmFilter').checked = false;
        document.getElementById('arbetsgivareFilter').checked = false;
        document.getElementById('branschFilter').value = '';
        document.getElementById('aiInriktningFilter').value = '';
        document.getElementById('anstalldaFilter').value = '';
        document.getElementById('omsattningFilter').value = '';

        currentPage = 1;
        loadCompanies();
    });
}

// ===== SEARCH =====
function handleSearch() {
    currentSearch = document.getElementById('searchInput').value.trim();
    currentPage = 1;
    loadCompanies();
}

async function handleLuckyClick() {
    const button = document.getElementById('luckyButton');
    const buttonText = button.querySelector('.btn-lucky-text');
    const buttonLoading = button.querySelector('.btn-lucky-loading');

    // CONFETTI EXPLOSION!
    triggerConfetti();

    // Show loading state
    button.disabled = true;
    buttonText.style.display = 'none';
    buttonLoading.style.display = 'inline';

    try {
        // Fetch a random company from the API
        const response = await fetch('/api/companies/?page=1&per_page=1000');
        const data = await response.json();

        if (data.companies && data.companies.length > 0) {
            // Pick a random company
            const randomIndex = Math.floor(Math.random() * data.companies.length);
            const randomCompany = data.companies[randomIndex];

            // Dramatic pause for effect
            await new Promise(resolve => setTimeout(resolve, 800));

            // Show the company modal
            showCompanyModal(randomCompany);
        } else {
            alert('Inga företag hittades i databasen.');
        }
    } catch (error) {
        console.error('Error fetching random company:', error);
        alert('Kunde inte hämta ett slumpmässigt företag.');
    } finally {
        // Reset button
        button.disabled = false;
        buttonText.style.display = 'inline';
        buttonLoading.style.display = 'none';
    }
}

function triggerConfetti() {
    const button = document.getElementById('luckyButton');
    const rect = button.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    // Create 30 confetti pieces
    for (let i = 0; i < 30; i++) {
        createConfettiPiece(centerX, centerY);
    }
}

function createConfettiPiece(x, y) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti-piece';

    // Random offset for spread
    const xOffset = (Math.random() - 0.5) * 300;
    const yOffset = Math.random() * 300 + 100;

    confetti.style.left = x + 'px';
    confetti.style.top = y + 'px';
    confetti.style.backgroundColor = getRandomColor();
    confetti.style.setProperty('--x-offset', xOffset);
    confetti.style.setProperty('--y-offset', yOffset);

    document.body.appendChild(confetti);

    // Remove after animation completes
    setTimeout(() => confetti.remove(), 2000);
}

function getRandomColor() {
    const colors = ['#ff6b6b', '#ffd93d', '#6bcf7f', '#4d96ff', '#c77dff'];
    return colors[Math.floor(Math.random() * colors.length)];
}

// ===== DATA LOADING =====
async function loadData() {
    showLoading();
    try {
        // Load column configuration first
        await loadColumns();
        // Then load companies
        await loadCompanies();
    } catch (error) {
        console.error('Error loading data:', error);
        showError();
    }
}

async function loadColumns() {
    const deviceType = isMobile ? 'mobile' : 'desktop';
    const response = await fetch(`${API_COLUMNS}?device=${deviceType}`);
    const data = await response.json();

    currentColumns = data.columns.sort((a, b) => a.display_order - b.display_order);
}

async function loadFilterOptions() {
    try {
        const response = await fetch(API_FILTER_OPTIONS);
        const data = await response.json();

        // Populate Bransch dropdown
        const branschSelect = document.getElementById('branschFilter');
        data.bransch.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            branschSelect.appendChild(opt);
        });

        // Populate AI-inriktning dropdown
        const aiInriktningSelect = document.getElementById('aiInriktningFilter');
        if (data.ai_inriktning) {
            data.ai_inriktning.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option;
                opt.textContent = option;
                aiInriktningSelect.appendChild(opt);
            });
        }

        // Populate Anställda dropdown
        const anstalldaSelect = document.getElementById('anstalldaFilter');
        data.anstallda.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            anstalldaSelect.appendChild(opt);
        });

        // Populate Omsättning dropdown
        const omsattningSelect = document.getElementById('omsattningFilter');
        data.omsattning.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            omsattningSelect.appendChild(opt);
        });
    } catch (error) {
        console.error('Error loading filter options:', error);
    }
}

async function loadCompanies() {
    showLoading();

    try {
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 50,
        });

        if (currentSearch) {
            params.append('search', currentSearch);
        }

        // Add filters
        if (currentFilters.stockholm) {
            params.append('stockholm', 'true');
        }
        if (currentFilters.arbetsgivare) {
            params.append('arbetsgivare', 'true');
        }
        if (currentFilters.bransch) {
            params.append('bransch', currentFilters.bransch);
        }
        if (currentFilters.ai_inriktning) {
            params.append('ai_inriktning', currentFilters.ai_inriktning);
        }
        if (currentFilters.anstallda) {
            params.append('anstallda', currentFilters.anstallda);
        }
        if (currentFilters.omsattning) {
            params.append('omsattning', currentFilters.omsattning);
        }
        if (currentFilters.tag) {
            params.append('tag', currentFilters.tag);
        }

        const response = await fetch(`${API_COMPANIES}?${params}`);
        const data = await response.json();

        totalPages = data.total_pages;

        // Cache totalt antal första gången (utan filter)
        const hasFilters = hasActiveFilters();
        if (totalCompaniesInDB === 0 && !hasFilters) {
            totalCompaniesInDB = data.total;
            currentDisplayedCount = data.total; // Initiera counter
        }

        // Update stats (legacy element)
        const totalCompaniesElem = document.getElementById('totalCompanies');
        if (totalCompaniesElem) {
            totalCompaniesElem.textContent = `Totalt ${data.total} företag`;
        }

        // Update stats display (NEW)
        updateStatsDisplay(data.total, hasFilters);

        // Uppdatera batteristapel
        const totalToUse = totalCompaniesInDB > 0 ? totalCompaniesInDB : data.total;
        updateBatteryBar(data.total, totalToUse);

        // Rendera aktiva filter pills (NEW)
        renderActiveFilterPills();

        // Render data
        if (isMobile) {
            renderMobileCards(data.companies);
        } else {
            renderDesktopTable(data.companies);
        }

        // Update pagination
        updatePagination();

        hideLoading();
    } catch (error) {
        console.error('Error loading companies:', error);
        showError();
    }
}

// ===== TAG RENDERING =====
function renderTags(tagsString) {
    if (!tagsString) return '';

    // Stöd både pipe (|) och komma (,) för bakåtkompatibilitet
    const delimiter = tagsString.includes('|') ? '|' : ',';
    const tags = tagsString.split(delimiter).map(t => t.trim()).filter(t => t);
    return tags.map(tag => {
        return `<span class="tag-pill" data-tag="${tag}">${tag}</span>`;
    }).join(' ');
}

function renderBranschTags(branschString) {
    if (!branschString) return '';

    // Bransch kan vara en sträng med kommatecken eller pipe
    const delimiter = branschString.includes('|') ? '|' : ',';
    const tags = branschString.split(delimiter).map(t => t.trim()).filter(t => t);
    return tags.map(tag => {
        return `<span class="tag-pill-bransch" data-bransch="${tag}">${tag}</span>`;
    }).join(' ');
}

function filterByTag(tag) {
    currentFilters.tag = tag;
    currentPage = 1;
    loadCompanies();
}

function filterByBransch(bransch) {
    currentFilters.bransch = bransch;
    document.getElementById('branschFilter').value = bransch;
    currentPage = 1;
    loadCompanies();
}

// ===== DESKTOP RENDERING =====
function renderDesktopTable(companies) {
    const tableHeaders = document.getElementById('tableHeaders');
    const tableBody = document.getElementById('tableBody');

    // Clear existing content
    tableHeaders.innerHTML = '';
    tableBody.innerHTML = '';

    // Render headers
    currentColumns.forEach(col => {
        const th = document.createElement('th');
        // Använd label från backend (antingen custom_label eller standardetikett)
        th.textContent = col.label || COLUMN_LABELS[col.column_name] || col.column_name;
        tableHeaders.appendChild(th);
    });

    // Add "Mer info" column header (empty)
    const merInfoHeader = document.createElement('th');
    merInfoHeader.textContent = '';
    tableHeaders.appendChild(merInfoHeader);

    // Render rows
    companies.forEach((company, index) => {
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.onclick = () => {
            console.log('Row clicked:', index, company.name);
            showCompanyModal(company);
        };
        tr.setAttribute('data-company-id', company.id);

        currentColumns.forEach(col => {
            const td = document.createElement('td');

            if (col.column_name === 'name' && company.website) {
                const a = document.createElement('a');
                a.href = company.website;
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                a.textContent = company.name;
                a.onclick = (e) => e.stopPropagation(); // Prevent modal from opening
                td.appendChild(a);
            } else if (col.column_name === 'ai_capabilities') {
                // Render as tags (now pipe-separated)
                td.innerHTML = renderTags(company[col.column_name]);
                // Add click handlers to tag pills
                td.querySelectorAll('.tag-pill').forEach(pill => {
                    pill.onclick = (e) => {
                        e.stopPropagation();
                        filterByTag(pill.getAttribute('data-tag'));
                    };
                });
            } else if (col.column_name === 'bransch') {
                // Render as tags with wine red hover
                td.innerHTML = renderBranschTags(company[col.column_name]);
                // Add click handlers to bransch pills
                td.querySelectorAll('.tag-pill-bransch').forEach(pill => {
                    pill.onclick = (e) => {
                        e.stopPropagation();
                        filterByBransch(pill.getAttribute('data-bransch'));
                    };
                });
            } else if (col.column_name === 'website' && company[col.column_name]) {
                const a = document.createElement('a');
                a.href = company[col.column_name];
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                a.textContent = truncate(company[col.column_name], 40);
                a.onclick = (e) => e.stopPropagation();
                td.appendChild(a);
            } else if (col.column_name === 'description') {
                const value = formatCellValue(company, col.column_name);
                td.className = 'truncate';
                td.title = value;
                td.textContent = value;
            } else {
                td.textContent = formatCellValue(company, col.column_name);
            }

            tr.appendChild(td);
        });

        // Add "Mer info" button column
        const merInfoTd = document.createElement('td');
        const merInfoBtn = document.createElement('button');
        merInfoBtn.className = 'btn-mer-info';
        merInfoBtn.textContent = 'Mer info';
        merInfoBtn.onclick = (e) => {
            e.stopPropagation();
            showCompanyModal(company);
        };
        merInfoTd.appendChild(merInfoBtn);
        tr.appendChild(merInfoTd);

        tableBody.appendChild(tr);
    });
}

// ===== MOBILE RENDERING =====
function renderMobileCards(companies) {
    const cardsContainer = document.getElementById('mobileCards');
    cardsContainer.innerHTML = '';

    companies.forEach(company => {
        const card = document.createElement('div');
        card.className = 'company-card';

        // Company name (always first)
        const title = document.createElement('h3');
        if (company.website) {
            const a = document.createElement('a');
            a.href = company.website;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.textContent = company.name;
            title.appendChild(a);
        } else {
            title.textContent = company.name;
        }
        card.appendChild(title);

        // Other fields
        currentColumns.forEach(col => {
            if (col.column_name === 'name') return; // Skip name, already rendered as title

            const value = formatCellValue(company, col.column_name);
            if (!value || value === '-') return; // Skip empty values

            const field = document.createElement('div');
            field.className = 'card-field';

            const label = document.createElement('strong');
            // Använd label från backend (antingen custom_label eller standardetikett)
            label.textContent = (col.label || COLUMN_LABELS[col.column_name] || col.column_name) + ': ';

            const valueSpan = document.createElement('span');

            if (col.column_name === 'website') {
                const a = document.createElement('a');
                a.href = value;
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                a.textContent = truncate(value, 30);
                valueSpan.appendChild(a);
            } else {
                valueSpan.textContent = value;
            }

            field.appendChild(label);
            field.appendChild(valueSpan);
            card.appendChild(field);
        });

        // Add "Mer info" button at bottom of card
        const merInfoBtn = document.createElement('button');
        merInfoBtn.className = 'btn-mer-info mobile-mer-info';
        merInfoBtn.textContent = 'Mer info';
        merInfoBtn.onclick = (e) => {
            e.stopPropagation();
            showCompanyModal(company);
        };
        card.appendChild(merInfoBtn);

        cardsContainer.appendChild(card);
    });
}

// ===== HELPERS =====
function formatCellValue(company, columnName) {
    let value = company[columnName];

    // Handle null/undefined
    if (value === null || value === undefined || value === '') {
        return '-';
    }

    // Handle boolean
    if (typeof value === 'boolean') {
        return value ? 'Ja' : 'Nej';
    }

    // Handle strings
    return String(value);
}

function truncate(text, maxLength) {
    if (!text) return '';
    text = String(text);
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// ===== PAGINATION =====
function updatePagination() {
    document.getElementById('pageInfo').textContent = `Sida ${currentPage} av ${totalPages}`;
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages;
}

// ===== MODAL =====
function showCompanyModal(company) {
    console.log('showCompanyModal called with:', company);

    const modal = document.getElementById('companyModal');
    const modalBody = document.getElementById('modalBody');

    if (!modal || !modalBody) {
        console.error('Modal elements not found in DOM');
        return;
    }

    if (!company) {
        console.error('Company object is null or undefined');
        return;
    }

    // Logo
    let logoHtml = '';
    if (company.logo_url) {
        logoHtml = `<img src="${company.logo_url}" alt="${company.name || 'Company'} logo" class="modal-logo" onerror="this.style.display='none'">`;
    }

    // Company name
    const companyName = company.name || 'Företag utan namn';

    // Website
    let websiteHtml = '';
    if (company.website) {
        websiteHtml = `<p class="modal-field"><strong>Webbplats:</strong> <a href="${company.website}" target="_blank" rel="noopener noreferrer">${company.website}</a></p>`;
    }

    // Basic info (between website and description)
    let basicInfoHtml = '';
    if (company.bransch) {
        basicInfoHtml += `<div class="modal-field-block"><strong>Bransch:</strong><div class="modal-tags">${renderBranschTags(company.bransch)}</div></div>`;
    }
    if (company.ai_capabilities) {
        basicInfoHtml += `<div class="modal-field-block"><strong>AI-inriktning:</strong><div class="modal-tags">${renderTags(company.ai_capabilities)}</div></div>`;
    }

    // Description
    const companyDescription = company.description || 'Ingen beskrivning tillgänglig';
    const descriptionHtml = `<div class="modal-scb-data"><h3>Om företaget</h3><p>${companyDescription}</p></div>`;

    // SCB Data
    let scbDataHtml = '<div class="modal-scb-data"><h3>Företagsinformation (Bolagsverket)</h3>';
    const scbFields = [
        { key: 'organization_number', label: 'Organisationsnummer' },
        { key: 'scb_namn', label: 'Juridiskt namn' },
        { key: 'scb_adress', label: 'Adress' },
        { key: 'scb_postnr', label: 'Postnummer' },
        { key: 'municipality', label: 'Ort' },
        { key: 'scb_kontor', label: 'Antal kontor' },
        { key: 'employee_size', label: 'Antal anställda' },
        { key: 'scb_omsattning', label: 'Omsättning' },
        { key: 'scb_alder', label: 'Antal år verksamt' }
    ];

    scbFields.forEach(field => {
        const value = company[field.key];
        if (value) {
            scbDataHtml += `<p class="modal-field"><strong>${field.label}:</strong> ${value}</p>`;
        }
    });
    scbDataHtml += '</div>';

    modalBody.innerHTML = `
        <button class="modal-report-icon" onclick="openErrorReportModal(${company.id}, '${companyName.replace(/'/g, "\\'")}')" title="Rapportera fel">
            <span class="material-symbols-outlined">report</span>
            <span class="modal-report-text">Rapportera fel</span>
        </button>
        ${logoHtml}
        <h2>${companyName}</h2>
        ${websiteHtml}
        ${basicInfoHtml}
        ${descriptionHtml}
        ${scbDataHtml}
    `;

    // Add click handlers to bransch tags in modal
    const branschTags = modalBody.querySelectorAll('.tag-pill-bransch');
    branschTags.forEach(tag => {
        tag.onclick = () => {
            const bransch = tag.getAttribute('data-bransch');
            closeCompanyModal();
            filterByBransch(bransch);
        };
    });

    // Add click handlers to AI capability tags in modal
    const aiTags = modalBody.querySelectorAll('.tag-pill');
    aiTags.forEach(tag => {
        tag.onclick = () => {
            const aiTag = tag.getAttribute('data-tag');
            closeCompanyModal();
            filterByTag(aiTag);
        };
    });

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    console.log('Modal opened successfully');
}

function closeCompanyModal() {
    const modal = document.getElementById('companyModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
        console.log('Modal closed');
    }
}

function setupModalHandlers() {
    const modal = document.getElementById('companyModal');
    const closeBtn = document.querySelector('.close');

    if (!modal) {
        console.error('Modal element not found during setup');
        return;
    }

    if (!closeBtn) {
        console.error('Close button not found during setup');
        return;
    }

    // Close button click
    closeBtn.onclick = (e) => {
        e.stopPropagation();
        closeCompanyModal();
    };

    // Click outside modal
    modal.onclick = (event) => {
        if (event.target === modal) {
            closeCompanyModal();
        }
    };

    // Prevent clicks inside modal content from closing
    const modalContent = modal.querySelector('.modal-content');
    if (modalContent) {
        modalContent.onclick = (e) => {
            e.stopPropagation();
        };
    }

    // Escape key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            closeCompanyModal();
        }
    });

    console.log('Modal handlers setup complete');
}

// ===== ERROR REPORTING =====
function openErrorReportModal(companyId, companyName) {
    console.log('Opening error report modal for company:', companyId, companyName);

    // Close company modal first
    closeCompanyModal();

    // Get error report modal elements
    const errorModal = document.getElementById('errorReportModal');
    const errorForm = document.getElementById('errorReportForm');
    const errorCompanyId = document.getElementById('errorCompanyId');
    const errorCompanyName = document.getElementById('errorCompanyName');
    const successDiv = document.getElementById('errorReportSuccess');
    const errorDiv = document.getElementById('errorReportError');

    if (!errorModal || !errorForm) {
        console.error('Error report modal elements not found');
        return;
    }

    // Reset form
    errorForm.reset();
    errorForm.style.display = 'block';
    successDiv.style.display = 'none';
    errorDiv.style.display = 'none';

    // Set company info
    errorCompanyId.value = companyId;
    errorCompanyName.textContent = companyName;

    // Show modal
    errorModal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    // Setup form submission if not already done
    if (!errorForm.dataset.listenerAdded) {
        errorForm.addEventListener('submit', handleErrorReportSubmit);
        errorForm.dataset.listenerAdded = 'true';
    }
}

function closeErrorReportModal() {
    const errorModal = document.getElementById('errorReportModal');
    if (errorModal) {
        errorModal.style.display = 'none';
        document.body.style.overflow = '';
        console.log('Error report modal closed');
    }
}

async function handleErrorReportSubmit(e) {
    e.preventDefault();
    console.log('Submitting error report...');

    const form = e.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);

    // Disable submit button
    submitButton.disabled = true;
    submitButton.textContent = 'Skickar...';

    try {
        // Get CSRF token from cookie
        const csrftoken = getCookie('csrftoken');

        const response = await fetch('/api/report-error/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                company_id: formData.get('company_id'),
                error_type: formData.get('error_type'),
                description: formData.get('description'),
                suggestion: formData.get('suggestion') || ''
            })
        });

        if (response.ok) {
            // Show success message
            form.style.display = 'none';
            document.getElementById('errorReportSuccess').style.display = 'block';
            console.log('Error report submitted successfully');
        } else {
            throw new Error('Server responded with error');
        }
    } catch (error) {
        console.error('Error submitting report:', error);
        // Show error message
        form.style.display = 'none';
        document.getElementById('errorReportError').style.display = 'block';
    } finally {
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.textContent = 'Skicka felanmälan';
    }
}

// Helper function to get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===== UI STATE =====
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
    document.querySelector('.desktop-view').style.display = 'none';
    document.querySelector('.mobile-view').style.display = 'none';
    document.getElementById('pagination').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';

    if (isMobile) {
        document.querySelector('.mobile-view').style.display = 'block';
    } else {
        document.querySelector('.desktop-view').style.display = 'block';
    }

    document.getElementById('pagination').style.display = 'flex';
}

function showError() {
    document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'block';
    document.querySelector('.desktop-view').style.display = 'none';
    document.querySelector('.mobile-view').style.display = 'none';
    document.getElementById('pagination').style.display = 'none';
}

// ===== HELP MODAL FUNCTIONS =====

/**
 * Open the help modal
 */
function openHelpModal() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
}

/**
 * Close the help modal
 */
function closeHelpModal() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    }
}

// ===== COMPANY SUGGESTION MODAL FUNCTIONS =====

/**
 * Open the company suggestion modal
 */
function openSuggestionModal() {
    const modal = document.getElementById('suggestionModal');
    const form = document.getElementById('suggestionForm');
    const successDiv = document.getElementById('suggestionSuccess');
    const errorDiv = document.getElementById('suggestionError');

    if (modal && form) {
        // Reset form and show it
        form.reset();
        form.style.display = 'block';
        successDiv.style.display = 'none';
        errorDiv.style.display = 'none';

        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close the company suggestion modal
 */
function closeSuggestionModal() {
    const modal = document.getElementById('suggestionModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

/**
 * Handle company suggestion form submission
 */
async function handleSuggestionSubmit(e) {
    e.preventDefault();

    const form = document.getElementById('suggestionForm');
    const formData = new FormData(form);
    const successDiv = document.getElementById('suggestionSuccess');
    const errorDiv = document.getElementById('suggestionError');

    // Get form values
    const companyName = formData.get('company_name');
    const website = formData.get('website');
    const additionalInfo = formData.get('additional_info') || '';

    // Get CSRF token
    const csrftoken = getCookie('csrftoken');

    try {
        const response = await fetch('/api/report-error/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                error_type: 'suggestion_new_company',
                company_name: companyName,
                company_website: website,
                additional_info: additionalInfo
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Show success message
            form.style.display = 'none';
            errorDiv.style.display = 'none';
            successDiv.style.display = 'block';
        } else {
            // Show error message
            form.style.display = 'none';
            successDiv.style.display = 'none';
            errorDiv.style.display = 'block';
            console.error('Error submitting suggestion:', data.error);
        }
    } catch (error) {
        // Show error message
        form.style.display = 'none';
        successDiv.style.display = 'none';
        errorDiv.style.display = 'block';
        console.error('Error submitting suggestion:', error);
    }
}

// ===== EVENT LISTENERS FOR MODALS =====

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    const helpModal = document.getElementById('helpModal');
    const suggestionModal = document.getElementById('suggestionModal');

    if (event.target === helpModal) {
        closeHelpModal();
    }
    if (event.target === suggestionModal) {
        closeSuggestionModal();
    }
});

// Close modals with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const helpModal = document.getElementById('helpModal');
        const suggestionModal = document.getElementById('suggestionModal');

        if (helpModal && helpModal.style.display === 'block') {
            closeHelpModal();
        }
        if (suggestionModal && suggestionModal.style.display === 'block') {
            closeSuggestionModal();
        }
    }
});

// Attach event listener to suggestion form
document.addEventListener('DOMContentLoaded', function() {
    const suggestionForm = document.getElementById('suggestionForm');
    if (suggestionForm) {
        suggestionForm.addEventListener('submit', handleSuggestionSubmit);
    }
});
