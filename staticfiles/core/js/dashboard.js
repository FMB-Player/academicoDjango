/**
 * Dashboard specific JavaScript functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any dashboard-specific components
    initDashboardCharts();
    initDashboardTabs();
    initTooltips();
});

/**
 * Initialize charts on the dashboard
 */
function initDashboardCharts() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        return;
    }

    // Find all canvas elements with data-chart attribute
    document.querySelectorAll('canvas[data-chart]').forEach(canvas => {
        const chartType = canvas.getAttribute('data-chart') || 'line';
        const chartData = JSON.parse(canvas.getAttribute('data-chart-data') || '{}');
        const chartOptions = JSON.parse(canvas.getAttribute('data-chart-options') || '{}');

        // Default options
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        };

        // Merge default options with provided options
        const options = {
            ...defaultOptions,
            ...chartOptions
        };

        // Create the chart
        new Chart(canvas, {
            type: chartType,
            data: chartData,
            options: options
        });
    });
}

/**
 * Initialize tab functionality for dashboard tabs
 */
function initDashboardTabs() {
    const tabContainers = document.querySelectorAll('.tab-container');
    
    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('[data-tab]');
        const tabContents = container.querySelectorAll('.tab-content');

        // Set first tab as active by default
        if (tabs.length > 0) {
            tabs[0].classList.add('active');
            const firstTabId = tabs[0].getAttribute('data-tab');
            const firstContent = container.querySelector(`#${firstTabId}`);
            if (firstContent) firstContent.classList.add('active');
        }

        // Add click event to tabs
        tabs.forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                const tabId = this.getAttribute('data-tab');
                
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Show corresponding content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === tabId) {
                        content.classList.add('active');
                    }
                });
            });
        });
    });
}

/**
 * Initialize tooltips using Tippy.js if available
 */
function initTooltips() {
    // Check if Tippy is loaded
    if (typeof tippy === 'undefined') {
        return;
    }

    // Initialize tooltips for elements with data-tooltip attribute
    tippy('[data-tooltip]', {
        content(reference) {
            return reference.getAttribute('data-tooltip');
        },
        placement: 'top',
        theme: 'light',
        animation: 'scale',
        arrow: true,
        delay: [100, 0]
    });
}

/**
 * Update dashboard stats with AJAX
 * @param {string} url - The URL to fetch updated stats from
 */
function updateDashboardStats(url) {
    if (!url) return;
    
    fetch(url, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        // Update each stat element
        Object.entries(data).forEach(([key, value]) => {
            const element = document.getElementById(`stat-${key}`);
            if (element) {
                // Animate number if it's a numeric value
                if (typeof value === 'number') {
                    animateValue(element, 0, value, 1000);
                } else {
                    element.textContent = value;
                }
            }
        });
    })
    .catch(error => {
        console.error('Error fetching dashboard stats:', error);
    });
}

/**
 * Animate a numeric value
 * @param {HTMLElement} element - The element to animate
 * @param {number} start - Start value
 * @param {number} end - End value
 * @param {number} duration - Animation duration in milliseconds
 */
function animateValue(element, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();
    
    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const value = Math.floor(start + (range * progress));
        
        element.textContent = value.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }
    
    requestAnimationFrame(updateValue);
}
