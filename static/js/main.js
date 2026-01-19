// Main JavaScript for Kiri Research Labs
// Extracted from base.html for better maintainability

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initSidebar();
    initProfileDropdown();
});

// ============================================================================
// Theme Toggle
// ============================================================================

function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const iconLight = document.getElementById('theme-icon-light');
    const iconDark = document.getElementById('theme-icon-dark');

    function updateThemeIcons() {
        if (document.documentElement.classList.contains('dark')) {
            iconLight?.classList.add('hidden');
            iconDark?.classList.remove('hidden');
        } else {
            iconLight?.classList.remove('hidden');
            iconDark?.classList.add('hidden');
        }
    }

    themeToggle?.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
        updateThemeIcons();
    });

    // Init theme icons on load
    updateThemeIcons();
}

// ============================================================================
// Sidebar
// ============================================================================

function initSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const mainContent = document.getElementById('main-content');
    const isMobile = () => window.innerWidth < 768;

    function openMobileSidebar() {
        sidebar?.classList.remove('hidden');
        sidebar?.classList.add('mobile-open');
        sidebarOverlay?.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeMobileSidebar() {
        sidebar?.classList.remove('mobile-open');
        sidebarOverlay?.classList.add('hidden');
        document.body.style.overflow = '';
        setTimeout(() => {
            if (isMobile()) sidebar?.classList.add('hidden');
        }, 300);
    }

    sidebarToggle?.addEventListener('click', () => {
        if (isMobile()) {
            if (sidebar?.classList.contains('mobile-open')) {
                closeMobileSidebar();
            } else {
                openMobileSidebar();
            }
        } else {
            sidebar?.classList.toggle('expanded');
            if (mainContent) {
                mainContent.style.paddingLeft = sidebar?.classList.contains('expanded') ? '220px' : '56px';
            }
        }
    });

    sidebarOverlay?.addEventListener('click', closeMobileSidebar);

    // Auto-expand sidebar on hover (desktop only)
    if (!isMobile() && sidebar) {
        sidebar.addEventListener('mouseenter', () => {
            sidebar.classList.add('expanded');
            if (mainContent) mainContent.style.paddingLeft = '220px';
        });
        sidebar.addEventListener('mouseleave', () => {
            if (!sidebar.dataset.pinned) {
                sidebar.classList.remove('expanded');
                if (mainContent) mainContent.style.paddingLeft = '56px';
            }
        });
    }
}

// ============================================================================
// Profile Dropdown
// ============================================================================

function initProfileDropdown() {
    const profileToggle = document.getElementById('profile-dropdown-toggle');
    const profileDropdown = document.getElementById('profile-dropdown');

    profileToggle?.addEventListener('click', (e) => {
        e.stopPropagation();
        profileDropdown?.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
        if (profileDropdown && profileToggle &&
            !profileDropdown.contains(e.target) &&
            !profileToggle.contains(e.target)) {
            profileDropdown.classList.add('hidden');
        }
    });
}
