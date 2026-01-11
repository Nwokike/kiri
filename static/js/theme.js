// Theme Toggle Logic
(function () {
    const themeToggle = document.getElementById('theme-toggle');
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    const html = document.documentElement;

    // Get saved theme or default to light
    function getTheme() {
        return localStorage.getItem('theme') || 'light';
    }

    // Apply theme
    function setTheme(theme) {
        if (theme === 'dark') {
            html.setAttribute('data-theme', 'dark');
            html.classList.add('dark');
            if (lightIcon) lightIcon.classList.add('hidden');
            if (darkIcon) darkIcon.classList.remove('hidden');
        } else {
            html.removeAttribute('data-theme');
            html.classList.remove('dark');
            if (lightIcon) lightIcon.classList.remove('hidden');
            if (darkIcon) darkIcon.classList.add('hidden');
        }
        localStorage.setItem('theme', theme);
    }

    // Initialize theme on load
    setTheme(getTheme());

    // Toggle theme on click
    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const currentTheme = getTheme();
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(newTheme);
        });
    }

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function () {
            mobileMenu.classList.toggle('hidden');
        });
    }
})();
