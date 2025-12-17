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
    bransch: [],      // Changed to array for multi-select
    tillampning: [],
    anstallda: [],    // Changed to array for multi-select
    omsattning: [],   // Changed to array for multi-select
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
           (currentFilters.bransch && currentFilters.bransch.length > 0) ||
           (currentFilters.tillampning && currentFilters.tillampning.length > 0) ||
           (currentFilters.anstallda && currentFilters.anstallda.length > 0) ||
           (currentFilters.omsattning && currentFilters.omsattning.length > 0) ||
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

    // Bransch pills (multi-select)
    if (currentFilters.bransch && currentFilters.bransch.length > 0) {
        currentFilters.bransch.forEach(bransch => {
            pills.push(createFilterPill(`Bransch: ${bransch}`, () => {
                currentFilters.bransch = currentFilters.bransch.filter(b => b !== bransch);
                const checkbox = document.querySelector(`input[name="bransch"][value="${bransch}"]`);
                if (checkbox) checkbox.checked = false;
                currentPage = 1;
                loadCompanies();
            }));
        });
    }

    // Tillämpning pills (multi-select)
    if (currentFilters.tillampning && currentFilters.tillampning.length > 0) {
        currentFilters.tillampning.forEach(tillampning => {
            pills.push(createFilterPill(`Tillämpning: ${tillampning}`, () => {
                currentFilters.tillampning = currentFilters.tillampning.filter(t => t !== tillampning);
                const checkbox = document.querySelector(`input[name="tillampning"][value="${tillampning}"]`);
                if (checkbox) checkbox.checked = false;
                currentPage = 1;
                loadCompanies();
            }));
        });
    }

    // Anställda pills (multi-select)
    if (currentFilters.anstallda && currentFilters.anstallda.length > 0) {
        currentFilters.anstallda.forEach(anstallda => {
            pills.push(createFilterPill(`Anställda: ${anstallda}`, () => {
                currentFilters.anstallda = currentFilters.anstallda.filter(a => a !== anstallda);
                const checkbox = document.querySelector(`input[name="anstallda"][value="${anstallda}"]`);
                if (checkbox) checkbox.checked = false;
                currentPage = 1;
                loadCompanies();
            }));
        });
    }

    // Omsättning pills (multi-select)
    if (currentFilters.omsattning && currentFilters.omsattning.length > 0) {
        currentFilters.omsattning.forEach(omsattning => {
            pills.push(createFilterPill(`Omsättning: ${omsattning}`, () => {
                currentFilters.omsattning = currentFilters.omsattning.filter(o => o !== omsattning);
                const checkbox = document.querySelector(`input[name="omsattning"][value="${omsattning}"]`);
                if (checkbox) checkbox.checked = false;
                currentPage = 1;
                loadCompanies();
            }));
        });
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

// Toggle expandable filter sections
function toggleFilterSection(sectionName) {
    const section = document.querySelector(`.filter-section[data-filter="${sectionName}"]`);
    if (!section) return;

    const content = section.querySelector('.filter-content');
    if (!content) return;

    section.classList.toggle('expanded');
    content.classList.toggle('expanded');
}

// Attach event listeners to filter checkboxes (called after dynamic population)
function attachFilterEventListeners() {
    // Bransch checkboxes
    document.querySelectorAll('input[name="bransch"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                if (!currentFilters.bransch.includes(this.value)) {
                    currentFilters.bransch.push(this.value);
                }
            } else {
                currentFilters.bransch = currentFilters.bransch.filter(b => b !== this.value);
            }
            currentPage = 1;
            loadCompanies();
        });
    });

    // Tillämpning checkboxes
    document.querySelectorAll('input[name="tillampning"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                if (!currentFilters.tillampning.includes(this.value)) {
                    currentFilters.tillampning.push(this.value);
                }
            } else {
                currentFilters.tillampning = currentFilters.tillampning.filter(t => t !== this.value);
            }
            currentPage = 1;
            loadCompanies();
        });
    });

    // Anställda checkboxes
    document.querySelectorAll('input[name="anstallda"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                if (!currentFilters.anstallda.includes(this.value)) {
                    currentFilters.anstallda.push(this.value);
                }
            } else {
                currentFilters.anstallda = currentFilters.anstallda.filter(a => a !== this.value);
            }
            currentPage = 1;
            loadCompanies();
        });
    });

    // Omsättning checkboxes
    document.querySelectorAll('input[name="omsattning"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                if (!currentFilters.omsattning.includes(this.value)) {
                    currentFilters.omsattning.push(this.value);
                }
            } else {
                currentFilters.omsattning = currentFilters.omsattning.filter(o => o !== this.value);
            }
            currentPage = 1;
            loadCompanies();
        });
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

    // Attach listeners for all filter checkboxes (tillämpning is hardcoded, others are dynamic)
    attachFilterEventListeners();

    document.getElementById('clearFilters').addEventListener('click', () => {
        // Rensa filter
        currentFilters = {
            stockholm: false,
            arbetsgivare: false,
            bransch: [],      // Array for multi-select
            tillampning: [],
            anstallda: [],    // Array for multi-select
            omsattning: [],   // Array for multi-select
            tag: ''
        };

        // Rensa sökning
        currentSearch = '';

        // Återställ UI
        document.getElementById('searchInput').value = '';
        document.getElementById('stockholmFilter').checked = false;
        document.getElementById('arbetsgivareFilter').checked = false;
        // Uncheck all checkboxes
        document.querySelectorAll('input[name="bransch"]').forEach(cb => cb.checked = false);
        document.querySelectorAll('input[name="tillampning"]').forEach(cb => cb.checked = false);
        document.querySelectorAll('input[name="anstallda"]').forEach(cb => cb.checked = false);
        document.querySelectorAll('input[name="omsattning"]').forEach(cb => cb.checked = false);

        // Collapse all filter sections
        document.querySelectorAll('.filter-section').forEach(section => {
            section.classList.remove('expanded');
            const content = section.querySelector('.filter-content');
            if (content) {
                content.classList.remove('expanded');
            }
        });

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

        // Populate Bransch checkboxes
        const branschContainer = document.getElementById('branschCheckboxContainer');
        const branschGroup = document.createElement('div');
        branschGroup.className = 'checkbox-group-vertical';
        data.bransch.forEach(option => {
            const label = document.createElement('label');
            label.className = 'filter-checkbox';
            label.innerHTML = `
                <input type="checkbox" name="bransch" value="${option}">
                <span>${option}</span>
            `;
            branschGroup.appendChild(label);
        });
        branschContainer.appendChild(branschGroup);

        // NOTE: Tillämpning uses checkboxes (hardcoded in HTML), no need to populate from API

        // Populate Anställda checkboxes
        const anstalldaContainer = document.getElementById('anstalldaCheckboxContainer');
        const anstalldaGroup = document.createElement('div');
        anstalldaGroup.className = 'checkbox-group-vertical';
        data.anstallda.forEach(option => {
            const label = document.createElement('label');
            label.className = 'filter-checkbox';
            label.innerHTML = `
                <input type="checkbox" name="anstallda" value="${option}">
                <span>${option}</span>
            `;
            anstalldaGroup.appendChild(label);
        });
        anstalldaContainer.appendChild(anstalldaGroup);

        // Populate Omsättning checkboxes
        const omsattningContainer = document.getElementById('omsattningCheckboxContainer');
        const omsattningGroup = document.createElement('div');
        omsattningGroup.className = 'checkbox-group-vertical';
        data.omsattning.forEach(option => {
            const label = document.createElement('label');
            label.className = 'filter-checkbox';
            label.innerHTML = `
                <input type="checkbox" name="omsattning" value="${option}">
                <span>${option}</span>
            `;
            omsattningGroup.appendChild(label);
        });
        omsattningContainer.appendChild(omsattningGroup);

        // After populating, attach event listeners to new checkboxes
        attachFilterEventListeners();
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
        // Add bransch filters (multi-select)
        if (currentFilters.bransch && currentFilters.bransch.length > 0) {
            currentFilters.bransch.forEach(b => {
                params.append('bransch', b);
            });
        }
        // Add tillampning filters (multi-select)
        if (currentFilters.tillampning && currentFilters.tillampning.length > 0) {
            currentFilters.tillampning.forEach(t => {
                params.append('tillampning', t);
            });
        }
        // Add anstallda filters (multi-select)
        if (currentFilters.anstallda && currentFilters.anstallda.length > 0) {
            currentFilters.anstallda.forEach(a => {
                params.append('anstallda', a);
            });
        }
        // Add omsattning filters (multi-select)
        if (currentFilters.omsattning && currentFilters.omsattning.length > 0) {
            currentFilters.omsattning.forEach(o => {
                params.append('omsattning', o);
            });
        }
        if (currentFilters.tag) {
            params.append('tag', currentFilters.tag);
        }

        const response = await fetch(`${API_COMPANIES}?${params}`);
        let data = await response.json();

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
    // Add to bransch filter array if not already present
    if (!currentFilters.bransch.includes(bransch)) {
        currentFilters.bransch.push(bransch);
    }
    // Check the corresponding checkbox
    const checkbox = document.querySelector(`input[name="bransch"][value="${bransch}"]`);
    if (checkbox && !checkbox.checked) {
        checkbox.checked = true;
    }
    currentPage = 1;
    loadCompanies();
}

function filterByTillampning(tillampning) {
    // Add to tillampning filter array if not already present
    if (!currentFilters.tillampning.includes(tillampning)) {
        currentFilters.tillampning.push(tillampning);
    }
    // Check the corresponding checkbox
    const checkbox = document.querySelector(`input[name="tillampning"][value="${tillampning}"]`);
    if (checkbox && !checkbox.checked) {
        checkbox.checked = true;
    }
    // Expand the tillampning filter section if not already expanded
    const tillampningSection = document.querySelector('.filter-section[data-filter="tillampning"]');
    if (tillampningSection && !tillampningSection.classList.contains('expanded')) {
        toggleFilterSection('tillampning');
    }
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
        let headerText = col.label || COLUMN_LABELS[col.column_name] || col.column_name;
        // Override "AI-inriktning" to "AI/ML-tillämpning"
        if (col.column_name === 'ai_capabilities') {
            headerText = 'AI/ML-tillämpning';
        }
        th.textContent = headerText;
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
                // Render tillämpningar as colored tags instead of AI-inriktning
                const tillampningar = [];
                const tillampningMapping = {
                    'tillampning_optimering_automation': 'Optimering & Automation',
                    'tillampning_sprak_ljud': 'Språk & Ljud',
                    'tillampning_prognos_prediktion': 'Prognos & Prediktion',
                    'tillampning_infrastruktur_data': 'Infrastruktur & Data',
                    'tillampning_insikt_analys': 'Insikt & Analys',
                    'tillampning_visuell_ai': 'Visuell AI'
                };

                Object.entries(tillampningMapping).forEach(([field, label]) => {
                    if (company[field] === true) {
                        tillampningar.push(label);
                    }
                });

                if (tillampningar.length > 0) {
                    td.innerHTML = tillampningar.slice(0, 3).map(t =>
                        `<span class="tag-pill tag-tillampning" data-tillampning="${t}">${t}</span>`
                    ).join('');
                    if (tillampningar.length > 3) {
                        td.innerHTML += `<span class="tag-pill tag-more">+${tillampningar.length - 3}</span>`;
                    }
                    // Add click handlers to tillampning pills
                    td.querySelectorAll('.tag-pill.tag-tillampning').forEach(pill => {
                        pill.onclick = (e) => {
                            e.stopPropagation();
                            filterByTillampning(pill.getAttribute('data-tillampning'));
                        };
                    });
                } else {
                    td.textContent = '—';
                }
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
    // AI-inriktning removed as requested

    // Tillämpningar (NEW - colored clickable boxes)
    const tillampningMapping = {
        'tillampning_optimering_automation': 'Optimering & Automation',
        'tillampning_sprak_ljud': 'Språk & Ljud',
        'tillampning_prognos_prediktion': 'Prognos & Prediktion',
        'tillampning_infrastruktur_data': 'Infrastruktur & Data',
        'tillampning_insikt_analys': 'Insikt & Analys',
        'tillampning_visuell_ai': 'Visuell AI'
    };

    let tillampningarHtml = '';
    Object.entries(tillampningMapping).forEach(([field, label]) => {
        if (company[field] === true) {
            tillampningarHtml += `<span class="modal-tag-tillampning" data-tillampning="${label}">${label}</span>`;
        }
    });

    if (tillampningarHtml) {
        basicInfoHtml += `<div class="modal-field-block"><strong>Tillämpningar:</strong><div class="modal-tags">${tillampningarHtml}</div></div>`;
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
        ${logoHtml}
        <h2>${companyName}</h2>
        ${websiteHtml}
        ${basicInfoHtml}
        ${descriptionHtml}
        ${scbDataHtml}
        <button class="modal-report-icon" onclick="openErrorReportModal(${company.id}, '${companyName.replace(/'/g, "\\'")}')" title="Rapportera fel">
            <span class="material-symbols-outlined">report</span>
            <span class="modal-report-text">Rapportera fel</span>
        </button>
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

    // Add click handlers to Tillämpning tags in modal (NEW)
    const tillampningTags = modalBody.querySelectorAll('.modal-tag-tillampning');
    tillampningTags.forEach(tag => {
        tag.onclick = () => {
            const tillampning = tag.getAttribute('data-tillampning');
            closeCompanyModal();
            // Check the corresponding checkbox
            const checkbox = document.querySelector(`input[name="tillampning"][value="${tillampning}"]`);
            if (checkbox && !checkbox.checked) {
                checkbox.checked = true;
                // Add to filter array
                if (!currentFilters.tillampning.includes(tillampning)) {
                    currentFilters.tillampning.push(tillampning);
                }
                // Reload companies with new filter
                currentPage = 1;
                loadCompanies();
            }
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

// ============================================
// DATABASE INSIGHTS MODAL & CHARTS
// ============================================

// State for charts
let chartInstances = {};

/**
 * Open Database Insights Modal
 */
function openDatabaseModal() {
    const modal = document.getElementById('databaseModal');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    // Fetch stats and render charts
    fetchDatabaseStats();
}

/**
 * Close Database Insights Modal
 */
function closeDatabaseModal() {
    const modal = document.getElementById('databaseModal');
    modal.style.display = 'none';
    document.body.style.overflow = '';

    // Destroy existing charts to free memory
    Object.values(chartInstances).forEach(chart => {
        if (chart) chart.destroy();
    });
    chartInstances = {};
}

/**
 * Release Notes Modal
 */
function openReleaseNotesModal() {
    const modal = document.getElementById('releaseNotesModal');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeReleaseNotesModal() {
    const modal = document.getElementById('releaseNotesModal');
    modal.style.display = 'none';
    document.body.style.overflow = '';
}

// Close release notes modal when clicking outside
window.onclick = function(event) {
    const releaseModal = document.getElementById('releaseNotesModal');
    if (event.target === releaseModal) {
        closeReleaseNotesModal();
    }
}

// Close release notes modal on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const releaseModal = document.getElementById('releaseNotesModal');
        if (releaseModal && releaseModal.style.display === 'block') {
            closeReleaseNotesModal();
        }
    }
});

/**
 * Fetch Database Statistics from API
 */
async function fetchDatabaseStats() {
    try {
        const response = await fetch('/api/database-stats/');
        const data = await response.json();

        // Update overview stats
        document.getElementById('statTotalCompanies').textContent = data.total_companies;
        // Note: "37 Variabler data" and "22 817 Celler data" are hardcoded in HTML

        // Render charts
        renderGeographicChart(data.geographic);
        renderBranschChart(data.bransch);
        renderApplicationsChart(data.applications);
        renderRevenueChart(data.revenue);
        renderEmployeesChart(data.employees);

    } catch (error) {
        console.error('Error fetching database stats:', error);
    }
}

/**
 * Chart Color Palette (Editorial Theme)
 */
const chartColors = {
    primary: '#00401A',      // Moss green
    secondary: '#990000',    // Wine red
    tertiary: '#1C1C1C',     // Nearly black
    palette: [
        '#00401A', '#990000', '#1C1C1C',
        '#5A5A5A', '#E0E0E0', '#425e44',
        '#8B0000', '#2F4F2F', '#696969'
    ]
};

/**
 * Default Chart Options (Editorial Style)
 */
const defaultChartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                font: {
                    family: "'Source Serif 4', serif",
                    size: 12
                },
                padding: 15,
                usePointStyle: true,
            }
        },
        tooltip: {
            backgroundColor: 'rgba(28, 28, 28, 0.9)',
            titleFont: {
                family: "'Playfair Display', serif",
                size: 14,
                weight: 'bold'
            },
            bodyFont: {
                family: "'Source Serif 4', serif",
                size: 12
            },
            padding: 12,
            cornerRadius: 0, // Sharp corners
        }
    }
};

/**
 * 1. Geographic Distribution Chart (Bar)
 */
function renderGeographicChart(data) {
    const ctx = document.getElementById('geographicChart').getContext('2d');

    if (chartInstances.geographic) {
        chartInstances.geographic.destroy();
    }

    chartInstances.geographic = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.STAD || 'Okänd'),
            datasets: [{
                label: 'Antal företag',
                data: data.map(item => item.count),
                backgroundColor: chartColors.primary,
                borderColor: chartColors.tertiary,
                borderWidth: 1
            }]
        },
        options: {
            ...defaultChartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(28, 28, 28, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * 2. Bransch Distribution Chart (Horizontal Bar)
 */
function renderBranschChart(data) {
    const ctx = document.getElementById('branschChart').getContext('2d');

    if (chartInstances.bransch) {
        chartInstances.bransch.destroy();
    }

    // Take top 10 only
    const top10 = data.slice(0, 10);

    chartInstances.bransch = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(item => item.BRANSCHKLUSTER_V2 || 'Okänd'),
            datasets: [{
                label: 'Antal företag',
                data: top10.map(item => item.count),
                backgroundColor: chartColors.secondary,
                borderColor: chartColors.tertiary,
                borderWidth: 1
            }]
        },
        options: {
            ...defaultChartOptions,
            indexAxis: 'y', // Horizontal bars
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(28, 28, 28, 0.1)'
                    }
                },
                y: {
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 10
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * 3. Applications Distribution Chart (Doughnut)
 */
function renderApplicationsChart(data) {
    const ctx = document.getElementById('applicationsChart').getContext('2d');

    if (chartInstances.applications) {
        chartInstances.applications.destroy();
    }

    const labels = Object.keys(data);
    const values = Object.values(data);

    chartInstances.applications = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: chartColors.palette,
                borderColor: chartColors.tertiary,
                borderWidth: 2
            }]
        },
        options: {
            ...defaultChartOptions,
            cutout: '50%', // Donut hole size
        }
    });
}

/**
 * 4. Revenue Distribution Chart (Pie)
 */
function renderRevenueChart(data) {
    const ctx = document.getElementById('revenueChart').getContext('2d');

    if (chartInstances.revenue) {
        chartInstances.revenue.destroy();
    }

    chartInstances.revenue = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(item => item.OMSÄTTNING_GRUPPERING_V2 || 'Okänd'),
            datasets: [{
                data: data.map(item => item.count),
                backgroundColor: chartColors.palette,
                borderColor: chartColors.tertiary,
                borderWidth: 2
            }]
        },
        options: defaultChartOptions
    });
}

/**
 * 5. Employee Distribution Chart (Bar)
 */
function renderEmployeesChart(data) {
    const ctx = document.getElementById('employeesChart').getContext('2d');

    if (chartInstances.employees) {
        chartInstances.employees.destroy();
    }

    chartInstances.employees = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.ANSTÄLLDA_GRUPPERING_V2 || 'Okänd'),
            datasets: [{
                label: 'Antal företag',
                data: data.map(item => item.count),
                backgroundColor: chartColors.primary,
                borderColor: chartColors.tertiary,
                borderWidth: 1
            }]
        },
        options: {
            ...defaultChartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(28, 28, 28, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ===== EVENT LISTENERS FOR MODALS =====

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    const helpModal = document.getElementById('helpModal');
    const suggestionModal = document.getElementById('suggestionModal');
    const databaseModal = document.getElementById('databaseModal');

    if (event.target === helpModal) {
        closeHelpModal();
    }
    if (event.target === suggestionModal) {
        closeSuggestionModal();
    }
    if (event.target === databaseModal) {
        closeDatabaseModal();
    }
});

// Close modals with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const helpModal = document.getElementById('helpModal');
        const suggestionModal = document.getElementById('suggestionModal');
        const databaseModal = document.getElementById('databaseModal');

        if (helpModal && helpModal.style.display === 'block') {
            closeHelpModal();
        }
        if (suggestionModal && suggestionModal.style.display === 'block') {
            closeSuggestionModal();
        }
        if (databaseModal && databaseModal.style.display === 'block') {
            closeDatabaseModal();
        }
    }
});

// Attach event listener to suggestion form and battery click
document.addEventListener('DOMContentLoaded', function() {
    const suggestionForm = document.getElementById('suggestionForm');
    if (suggestionForm) {
        suggestionForm.addEventListener('submit', handleSuggestionSubmit);
    }

    // Make battery clickable to open database insights modal
    const batteryContainer = document.querySelector('.battery-container');
    if (batteryContainer) {
        batteryContainer.addEventListener('click', openDatabaseModal);
    }
});
