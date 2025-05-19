/**
 * Main JavaScript for the API
 * Handles dynamic functionality and UI interactions
 *
 * Author: Cameron Murphy
 * Date: May 18th 2025
 */

// Initialize on document load
document.addEventListener('DOMContentLoaded', function() {
    // Set current year for footer
    window.now = {
        year: new Date().getFullYear()
    };

    // Initialize tooltips
    initializeTooltips();

    // Initialize weather refresh
    initializeWeatherRefresh();

    // Handle copy functionality
    initializeCopyButtons();

    // Handle search functionality
    initializeSearch();

    // Handle sorting functionality
    initializeSorting();

    // Initialize animation on scroll
    initializeAnimations();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/**
 * Initialize auto-refresh for weather data
 */
function initializeWeatherRefresh() {
    // Check if we're on a page that should refresh weather data
    const weatherContainer = document.getElementById('weather-cards-container');
    const refreshButton = document.getElementById('refresh-weather');

    if (weatherContainer || refreshButton) {
        // Auto-refresh weather data every 30 minutes
        setInterval(function() {
            if (refreshButton) {
                refreshButton.click();
            } else {
                location.reload();
            }
        }, 30 * 60 * 1000); // 30 minutes
    }

    // Manual refresh button
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            const spinner = this.querySelector('.spinner-border');
            const icon = this.querySelector('.fa-sync-alt');

            // Show spinner
            if (spinner) spinner.style.display = 'inline-block';
            if (icon) icon.style.display = 'none';

            // Refresh the page
            setTimeout(function() {
                location.reload();
            }, 500);
        });
    }
}

/**
 * Initialize copy buttons for blog content
 */
function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');

    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const textArea = document.getElementById(targetId);

            if (textArea) {
                textArea.select();
                document.execCommand('copy');

                // Change button text temporarily
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
                this.classList.remove('btn-primary');
                this.classList.add('btn-success');

                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.classList.remove('btn-success');
                    this.classList.add('btn-primary');
                }, 2000);
            }
        });
    });
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInput = document.getElementById('location-search');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const cards = document.querySelectorAll('.weather-card');

            cards.forEach(card => {
                const locationName = card.getAttribute('data-location').toLowerCase();
                if (locationName.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
}

/**
 * Initialize sorting functionality
 */
function initializeSorting() {
    const sortTempBtn = document.getElementById('sort-temp-btn');
    const sortAlphaBtn = document.getElementById('sort-alpha-btn');
    const container = document.getElementById('weather-cards-container');

    if (sortTempBtn && sortAlphaBtn && container) {
        sortTempBtn.addEventListener('click', function() {
            const cards = Array.from(document.querySelectorAll('.weather-card'));

            cards.sort((a, b) => {
                const tempA = parseFloat(a.getAttribute('data-temperature'));
                const tempB = parseFloat(b.getAttribute('data-temperature'));
                return tempB - tempA; // Sort high to low
            });

            // Reappend in sorted order
            cards.forEach(card => container.appendChild(card));

            // Update active state
            sortTempBtn.classList.add('active');
            sortAlphaBtn.classList.remove('active');
        });

        sortAlphaBtn.addEventListener('click', function() {
            const cards = Array.from(document.querySelectorAll('.weather-card'));

            cards.sort((a, b) => {
                const locationA = a.getAttribute('data-location');
                const locationB = b.getAttribute('data-location');
                return locationA.localeCompare(locationB);
            });

            // Re-append in a sorted order
            cards.forEach(card => container.appendChild(card));

            // Update active state
            sortAlphaBtn.classList.add('active');
            sortTempBtn.classList.remove('active');
        });
    }
}

/**
 * Initialize animations for elements
 */
function initializeAnimations() {
    // Only run on larger screens
    if (window.innerWidth > 768) {
        // Animate elements when they enter the viewport
        const animatedElements = document.querySelectorAll('.card');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animatedElements.forEach(element => {
            observer.observe(element);
        });
    }
}

/**
 * Format temperature for display
 * @param {number} temp - Temperature in Celsius
 * @returns {string} Formatted temperature string
 */
function formatTemperature(temp) {
    return `${temp.toFixed(1)}°C`;
}

/**
 * Format date and time for display
 * @param {Date} date - Date object
 * @returns {string} Formatted date and time string
 */
function formatDateTime(date) {
    return date.toLocaleString('en-GB', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * Get class name based on weather condition
 * @param {string} condition - Weather condition
 * @returns {string} CSS class name
 */
function getWeatherClass(condition) {
    const conditionLower = condition.toLowerCase();

    if (conditionLower.includes('thunder')) return 'weather-thunderstorm';
    if (conditionLower.includes('drizzle')) return 'weather-drizzle';
    if (conditionLower.includes('rain')) return 'weather-rain';
    if (conditionLower.includes('snow')) return 'weather-snow';
    if (conditionLower.includes('clear')) return 'weather-clear';
    if (conditionLower.includes('cloud')) return 'weather-clouds';
    if (conditionLower.includes('fog') ||
        conditionLower.includes('mist') ||
        conditionLower.includes('haze')) return 'weather-fog';

    return '';
}

/**
 * Format wind direction based on degrees
 * @param {number} degrees - Wind direction in degrees
 * @returns {string} Direction arrow
 */
function getWindDirectionArrow(degrees) {
    // Define direction boundaries with their arrows
    const directions = [
        { min: 337.5, max: 22.5, arrow: '↓' },    // North
        { min: 22.5, max: 67.5, arrow: '↙' },     // Northeast
        { min: 67.5, max: 112.5, arrow: '←' },    // East
        { min: 112.5, max: 157.5, arrow: '↖' },   // Southeast
        { min: 157.5, max: 202.5, arrow: '↑' },   // South
        { min: 202.5, max: 247.5, arrow: '↗' },   // Southwest
        { min: 247.5, max: 292.5, arrow: '→' },   // West
        { min: 292.5, max: 337.5, arrow: '↘' }    // Northwest
    ];

    // Normalize degrees to 0-360 range
    const normDegrees = ((degrees % 360) + 360) % 360;

    // Find matching direction
    for (const dir of directions) {
        if (dir.min > dir.max) { // Handle north case that wraps around
            if (normDegrees >= dir.min || normDegrees <= dir.max) {
                return dir.arrow;
            }
        } else if (normDegrees >= dir.min && normDegrees < dir.max) {
            return dir.arrow;
        }
    }

    return '↓'; // Default fallback
}