/**
 * Kiri Project Import Logic
 * Handles the multi-step flow: Platform Selection -> Repository List.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('projectImport', (initialPlatforms = []) => ({
        loading: false,
        search: '',
        repos: [],
        error: null,

        // State
        selectedPlatform: null, // 'github', 'huggingface', or null
        platforms: initialPlatforms, // Passed from Django template

        get activePlatform() {
            if (!this.selectedPlatform) return null;
            return this.platforms.find(p => p.id === this.selectedPlatform);
        },

        async selectPlatform(platformId) {
            const platform = this.platforms.find(p => p.id === platformId);
            if (!platform) return;

            if (!platform.connected) {
                // If not connected, redirect to OAuth flow
                window.location.href = platform.connect_url;
                return;
            }

            this.selectedPlatform = platformId;
            await this.fetchRepos();
        },

        async fetchRepos(force = false) {
            if (!this.selectedPlatform) return;

            this.loading = true;
            this.error = null;

            const endpoint = `/projects/api/user-repos/?platform=${this.selectedPlatform}`;
            const url = force ? `${endpoint}&refresh=true` : endpoint;

            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(`Failed to fetch repositories: ${response.statusText}`);

                const data = await response.json();
                this.repos = data.repos || [];
            } catch (err) {
                this.error = 'Could not load repositories from ' + this.selectedPlatform + '. Please try again.';
                console.error('[Kiri] Project Import Error:', err);
            } finally {
                this.loading = false;
            }
        },

        get filteredRepos() {
            const query = this.search.toLowerCase().trim();
            if (!query) return this.repos;

            return this.repos.filter(repo =>
                repo.name.toLowerCase().includes(query) ||
                (repo.description && repo.description.toLowerCase().includes(query))
            );
        },

        getPlatformIcon(platform) {
            const icons = {
                github: 'fab fa-github',
                huggingface: 'fas fa-robot text-[#FFD21E]'
            };
            return icons[platform] || 'fas fa-code-branch';
        },

        importRepo(repo) {
            if (!repo?.url) return;

            const params = new URLSearchParams({
                repo_url: repo.url,
                name: repo.name || '',
                description: repo.description || '',
                import_mode: 'true'
            });

            window.location.href = `/projects/submit/?${params.toString()}`;
        },

        reset() {
            this.selectedPlatform = null;
            this.repos = [];
            this.search = '';
        }
    }));
});
