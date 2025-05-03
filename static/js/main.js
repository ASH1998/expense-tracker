/**
 * ExpenseTracker Main JavaScript File
 */

document.addEventListener('DOMContentLoaded', function() {
    // Theme Toggle Functionality
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = themeToggleBtn.querySelector('i');
    
    // Check for saved theme preference or use device preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkMode)) {
        document.body.setAttribute('data-bs-theme', 'dark');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
    } else {
        document.body.setAttribute('data-bs-theme', 'light');
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
    }
    
    // Toggle theme when button is clicked
    themeToggleBtn.addEventListener('click', function() {
        const currentTheme = document.body.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Update theme
        document.body.setAttribute('data-bs-theme', newTheme);
        
        // Update icon
        if (newTheme === 'dark') {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        } else {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        }
        
        // Save preference
        localStorage.setItem('theme', newTheme);
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Currency formatter
    window.formatCurrency = function(amount, currency = 'INR') {
        const formatter = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        });
        
        return formatter.format(amount);
    };
    
    // Date formatter
    window.formatDate = function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    };
    
    // Save session state
    window.saveSessionState = function() {
        // Save current page and any filtered states
        const currentPage = window.location.pathname;
        sessionStorage.setItem('lastPage', currentPage);
    };
    
    // Load session state
    window.loadSessionState = function() {
        // Retrieve and apply saved state if navigating back
        const lastPage = sessionStorage.getItem('lastPage');
        if (lastPage && document.referrer) {
            // Apply any saved filters or states
        }
    };
    
    // Call loadSessionState on page load
    window.loadSessionState();
    
    // Save state on page unload
    window.addEventListener('beforeunload', function() {
        window.saveSessionState();
    });
});