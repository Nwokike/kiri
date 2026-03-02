document.addEventListener('alpine:init', () => {
    const platformsDataElem = document.getElementById('platforms-data');
    if (!platformsDataElem) return;

    const platformsData = JSON.parse(platformsDataElem.textContent);
    const urlsMeta = document.querySelector('meta[name="import-urls"]');
    const createManualUrl = urlsMeta ? urlsMeta.dataset.createManual : '';

    Alpine.data('repoImporterInit', () => repoImporter(platformsData, createManualUrl));
});

document.addEventListener('DOMContentLoaded', () => {
    const manualImportBtn = document.getElementById('manual-import-btn');
    if (manualImportBtn) {
        manualImportBtn.addEventListener('click', () => {
            const urlsMeta = document.querySelector('meta[name="import-urls"]');
            const createManualUrl = urlsMeta ? urlsMeta.dataset.createManual : '';
            const url = document.getElementById('manual-url').value.trim();
            if (!url) return;
            window.location.href = `${createManualUrl}?import_mode=true&repo_url=${encodeURIComponent(url)}`;
        });
    }
});

function repoImporter(platformsData, importManualUrlBase) {
    return {
        platform: 'github',
        platforms: platformsData,
        repos: [],
        searchQuery: '',
        loading: false,

        init() {
            if (this.platformObj.connected) {
                this.fetchRepos();
            }
        },

        get platformObj() {
            return this.platforms.find(p => p.id === this.platform);
        },

        get filteredRepos() {
            if (!this.searchQuery) return this.repos;
            const q = this.searchQuery.toLowerCase();
            return this.repos.filter(r =>
                r.name.toLowerCase().includes(q) ||
                r.full_name.toLowerCase().includes(q) ||
                (r.description && r.description.toLowerCase().includes(q))
            );
        },

        setPlatform(p) {
            this.platform = p;
            this.repos = [];
            this.searchQuery = '';
            if (this.platformObj.connected) {
                this.fetchRepos();
            }
        },

        async fetchRepos() {
            this.loading = true;
            try {
                const res = await fetch(`/projects/api/user-repos/?platform=${this.platform}`);
                const data = await res.json();
                if (res.ok) {
                    this.repos = data.repos;
                } else {
                    console.error(data.error);
                }
            } catch (e) {
                console.error('Fetch error:', e);
            } finally {
                this.loading = false;
            }
        },

        importRepo(repo) {
            const topicsStr = JSON.stringify(repo.topics || []);
            const submitUrl = `${importManualUrlBase}?import_mode=true&repo_url=${encodeURIComponent(repo.html_url)}&name=${encodeURIComponent(repo.name)}&description=${encodeURIComponent(repo.description)}&language=${encodeURIComponent(repo.language)}&topics=${encodeURIComponent(topicsStr)}`;
            window.location.href = submitUrl;
        }
    }
}
