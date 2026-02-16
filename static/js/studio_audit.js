/**
 * Kiri Studio Proactive Audit
 * Scans code for Logic & Security issues.
 * Displays results in the LENS tab.
 */

class ProactiveAudit {
    constructor() {
        this.container = null;
        this.isAuditing = false;
    }

    init() {
        this.container = document.getElementById('plots-container');
        // Trigger audit on editor change (debounced)
        let auditTimeout;
        if (window.editor) {
            window.editor.onDidChangeModelContent(() => {
                clearTimeout(auditTimeout);
                auditTimeout = setTimeout(() => this.runAudit(), 5000);
            });
        }
    }

    async runAudit() {
        if (this.isAuditing || !window.studioAI) return;
        this.isAuditing = true;

        const code = window.editor.getValue();
        if (code.length < 20) {
            this.isAuditing = false;
            return;
        }

        const res = await window.studioAI.askAssistant("audit this code for potential logic flaws and security risks. return a concise list.", code);

        if (res && res.result) {
            this._renderResults(res.result.message || res.result);
        }
        this.isAuditing = false;
    }

    _renderResults(text) {
        if (!this.container) return;

        // If Data Lens is currently showing a grid, don't overwrite it
        if (window.dataLens && window.dataLens.activeGrid) return;

        const html = `
            <div class="p-6 space-y-4 fade-in">
                <div class="flex items-center gap-2 text-[#0D7C3D] mb-4">
                    <i class="fas fa-shield-alt"></i>
                    <h3 class="text-xs font-bold uppercase tracking-widest">Proactive Insights</h3>
                </div>
                <div class="bg-[#252526] border border-[#333] rounded-xl p-4 text-xs text-gray-400 font-sans leading-relaxed">
                    ${text.replace(/\n/g, '<br>')}
                </div>
                <div class="flex gap-2">
                    <button onclick="window.magicBar.open()" class="text-[10px] bg-[#0D7C3D]/10 text-[#0D7C3D] px-3 py-1.5 rounded-lg border border-[#0D7C3D]/20 hover:bg-[#0D7C3D]/20 transition-all">
                        Fix with Magic
                    </button>
                    <button onclick="window.switchTab('terminal')" class="text-[10px] bg-white/5 text-gray-400 px-3 py-1.5 rounded-lg border border-white/10 hover:bg-white/10 transition-all">
                        Dismiss
                    </button>
                </div>
            </div>
        `;
        this.container.innerHTML = html;
        // Optional: notification dot on the LENS tab
        const tab = document.getElementById('tab-plots');
        if (tab) tab.classList.add('relative');
        if (tab && !tab.querySelector('.notice-dot')) {
            const dot = document.createElement('span');
            dot.className = 'notice-dot absolute top-1 right-1 w-1.5 h-1.5 bg-[#0D7C3D] rounded-full animate-ping';
            tab.appendChild(dot);
        }
    }
}

window.proactiveAudit = new ProactiveAudit();
setTimeout(() => window.proactiveAudit.init(), 2000);
