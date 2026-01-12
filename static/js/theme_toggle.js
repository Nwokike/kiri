const toggleTheme = () => {
    if (document.documentElement.classList.contains('dark')) {
        document.documentElement.classList.remove('dark');
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.theme = 'light';
    } else {
        document.documentElement.classList.add('dark');
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.theme = 'dark';
    }

    // Update sidebar button icon if it exists
    const btn = document.getElementById('theme-toggle-sidebar');
    if (btn) {
        const isDark = document.documentElement.classList.contains('dark');
        btn.innerHTML = isDark
            ? '<i class="fas fa-sun"></i> <span>Light Mode</span>'
            : '<i class="fas fa-moon"></i> <span>Dark Mode</span>';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('theme-toggle-sidebar')?.addEventListener('click', toggleTheme);
    document.getElementById('mobile-theme-toggle')?.addEventListener('click', toggleTheme);
});
