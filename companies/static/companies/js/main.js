/**
 * AI Companies Explorer - Main JavaScript Module
 * Contains reusable functions for UI interactions
 */

// ============================================
// Filter Functions
// ============================================

/**
 * Toggle visibility of filter section on mobile
 */
function toggleFilters() {
    const filterContent = document.getElementById('filterContent');
    if (filterContent) {
        filterContent.classList.toggle('active');
    }
}

// ============================================
// Detail Card Functions
// ============================================

/**
 * Show detail card for a specific company
 * @param {number} companyId - The ID of the company to display
 */
function toggleDetailCard(companyId) {
    showDetail(companyId);
}

/**
 * Show detail card with company information
 * @param {number} companyId - The ID of the company to display
 */
function showDetail(companyId) {
    // Get company data from global companyData object
    if (typeof companyData === 'undefined') {
        console.error('companyData is not defined');
        return;
    }

    const company = companyData[companyId];
    if (!company) {
        console.error(`Company with ID ${companyId} not found`);
        return;
    }

    // Populate detail card elements
    const elements = {
        name: document.getElementById('detailName'),
        description: document.getElementById('detailDescription'),
        type: document.getElementById('detailType'),
        city: document.getElementById('detailCity'),
        employees: document.getElementById('detailEmployees'),
        municipality: document.getElementById('detailMunicipality'),
        orgNumber: document.getElementById('detailOrgNumber'),
        logo: document.getElementById('detailLogo'),
        sectors: document.getElementById('detailSectors'),
        capabilities: document.getElementById('detailCapabilities'),
        website: document.getElementById('detailWebsite')
    };

    // Set text content
    if (elements.name) elements.name.textContent = company.name || '—';
    if (elements.description) elements.description.textContent = company.description || 'Ingen beskrivning tillgänglig';
    if (elements.type) elements.type.textContent = company.type || '—';
    if (elements.city) elements.city.textContent = company.city || '—';
    if (elements.employees) elements.employees.textContent = company.employees || '—';
    if (elements.municipality) elements.municipality.textContent = company.municipality || '—';
    if (elements.orgNumber) elements.orgNumber.textContent = company.org_number || '—';

    // Handle logo
    if (elements.logo) {
        if (company.logo_url) {
            elements.logo.src = company.logo_url;
            elements.logo.style.display = 'block';
        } else {
            elements.logo.style.display = 'none';
        }
    }

    // Render sectors as chips (now a string instead of array)
    if (elements.sectors) {
        if (company.sectors && company.sectors !== '—') {
            elements.sectors.innerHTML = `<span class="chip">${escapeHtml(company.sectors)}</span>`;
        } else {
            elements.sectors.textContent = '—';
        }
    }

    // Render capabilities as chips (now a string instead of array)
    if (elements.capabilities) {
        if (company.capabilities && company.capabilities !== '—') {
            elements.capabilities.innerHTML = `<span class="chip">${escapeHtml(company.capabilities)}</span>`;
        } else {
            elements.capabilities.textContent = '—';
        }
    }

    // Render website link
    if (elements.website) {
        if (company.website) {
            elements.website.innerHTML = `<a href="${escapeHtml(company.website)}" target="_blank" class="link">${escapeHtml(company.website)}</a>`;
        } else {
            elements.website.textContent = '—';
        }
    }

    // Update report error button to open the report panel
    const reportLink = document.getElementById('detailReportError');
    if (reportLink) {
        reportLink.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            openReportPanel(companyId);
        };
    }

    // Highlight the active row
    document.querySelectorAll('tbody tr').forEach(tr => tr.classList.remove('active'));
    const activeRow = document.querySelector(`tr[data-company-id="${companyId}"]`);
    if (activeRow) {
        activeRow.classList.add('active');
    }

    // Show the detail card and overlay
    const detailCard = document.getElementById('detailCard');
    const detailOverlay = document.getElementById('detailOverlay');

    if (detailCard) detailCard.classList.add('active');
    if (detailOverlay) detailOverlay.classList.add('active');

    // Prevent body scrolling when modal is open
    document.body.style.overflow = 'hidden';
}

/**
 * Close the detail card
 */
function closeDetail() {
    const detailCard = document.getElementById('detailCard');
    const detailOverlay = document.getElementById('detailOverlay');

    if (detailCard) detailCard.classList.remove('active');
    if (detailOverlay) detailOverlay.classList.remove('active');

    // Remove active state from all rows
    document.querySelectorAll('tbody tr').forEach(tr => tr.classList.remove('active'));

    // Restore body scrolling
    document.body.style.overflow = 'auto';
}

// ============================================
// Search Functions
// ============================================

/**
 * Initialize auto-submit search with debounce
 * @param {string} selector - CSS selector for the search input
 * @param {number} delay - Debounce delay in milliseconds (default: 500)
 */
function initAutoSearch(selector = '.search-box', delay = 500) {
    let searchTimeout;
    const searchBox = document.querySelector(selector);

    if (searchBox) {
        searchBox.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.form) {
                    this.form.submit();
                }
            }, delay);
        });
    }
}

// ============================================
// Error Report Panel Functions
// ============================================

// Variable to track current company ID for error reporting
let currentReportCompanyId = null;

/**
 * Open the error report panel for a specific company
 * @param {number} companyId - The ID of the company to report an error for
 */
function openReportPanel(companyId) {
    currentReportCompanyId = companyId;

    const panel = document.getElementById('reportErrorPanel');
    if (panel) {
        panel.classList.remove('hidden');

        // Clear previous form data
        const subjectInput = document.getElementById('errorSubject');
        const descriptionInput = document.getElementById('errorDescription');
        if (subjectInput) subjectInput.value = '';
        if (descriptionInput) descriptionInput.value = '';

        // Prevent body scrolling when panel is open
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close the error report panel
 */
function closeReportPanel() {
    const panel = document.getElementById('reportErrorPanel');
    if (panel) {
        panel.classList.add('hidden');
        currentReportCompanyId = null;

        // Restore body scrolling
        document.body.style.overflow = 'auto';
    }
}

/**
 * Send error report to the server
 */
async function sendErrorReport() {
    if (!currentReportCompanyId) {
        console.error('No company ID set for error report');
        return;
    }

    const subjectInput = document.getElementById('errorSubject');
    const descriptionInput = document.getElementById('errorDescription');
    const sendButton = document.getElementById('sendErrorReport');

    if (!subjectInput || !descriptionInput) {
        console.error('Form inputs not found');
        return;
    }

    const subject = subjectInput.value.trim();
    const description = descriptionInput.value.trim();

    // Validate inputs
    if (!subject) {
        alert('Vänligen ange ett ämne');
        subjectInput.focus();
        return;
    }

    if (!description) {
        alert('Vänligen ange en beskrivning');
        descriptionInput.focus();
        return;
    }

    // Disable button during submission
    if (sendButton) {
        sendButton.disabled = true;
        sendButton.textContent = 'Skickar...';
    }

    try {
        // Get CSRF token
        const csrftoken = getCookie('csrftoken');

        // Send POST request
        const response = await fetch(`/companies/${currentReportCompanyId}/report-error/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                subject: subject,
                description: description
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Show success message
            const panelBody = document.querySelector('.report-panel-body');
            if (panelBody) {
                panelBody.innerHTML = `
                    <div style="text-align: center; padding: 2rem 0;">
                        <p style="font-size: 1.125rem; font-weight: 500; color: #059669; margin-bottom: 0.5rem;">
                            ✓ Tack! Din felanmälan har skickats.
                        </p>
                        <p style="color: var(--color-text-light); font-size: 0.875rem;">
                            Vi kommer att granska informationen.
                        </p>
                    </div>
                `;

                // Auto-close after 2 seconds
                setTimeout(() => {
                    closeReportPanel();
                    // Restore original content for next use
                    location.reload();
                }, 2000);
            }
        } else {
            // Show error message
            alert(`Fel: ${data.error || 'Kunde inte skicka felanmälan'}`);

            // Re-enable button
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.textContent = 'Skicka felanmälan';
            }
        }
    } catch (error) {
        console.error('Error sending report:', error);
        alert('Ett fel uppstod när felanmälan skulle skickas. Försök igen.');

        // Re-enable button
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.textContent = 'Skicka felanmälan';
        }
    }
}

/**
 * Get CSRF token from cookies
 * @param {string} name - Cookie name
 * @returns {string|null} - Cookie value or null
 */
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

// ============================================
// Utility Functions
// ============================================

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Close detail card on Escape key press
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDetail();
        }
    });
}

// ============================================
// Initialization
// ============================================

/**
 * Initialize all modules when DOM is ready
 */
function initApp() {
    // Initialize keyboard shortcuts
    initKeyboardShortcuts();

    // Initialize auto-search if search box exists
    if (document.querySelector('.search-box')) {
        initAutoSearch();
    }

    // Initialize error report panel
    initErrorReportPanel();
}

/**
 * Initialize error report panel event listeners
 */
function initErrorReportPanel() {
    const sendButton = document.getElementById('sendErrorReport');
    if (sendButton) {
        sendButton.addEventListener('click', sendErrorReport);
    }

    // Close panel on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const panel = document.getElementById('reportErrorPanel');
            if (panel && !panel.classList.contains('hidden')) {
                closeReportPanel();
            }
        }
    });

    // Close panel when clicking outside the card
    const panel = document.getElementById('reportErrorPanel');
    if (panel) {
        panel.addEventListener('click', function(e) {
            if (e.target === panel) {
                closeReportPanel();
            }
        });
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Export functions for global use
window.toggleFilters = toggleFilters;
window.toggleDetailCard = toggleDetailCard;
window.showDetail = showDetail;
window.closeDetail = closeDetail;
window.initAutoSearch = initAutoSearch;
window.openReportPanel = openReportPanel;
window.closeReportPanel = closeReportPanel;
window.sendErrorReport = sendErrorReport;
