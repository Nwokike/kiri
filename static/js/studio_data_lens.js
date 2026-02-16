/**
 * Kiri Studio Data Lens
 * Provides no-code spreadsheet-like preview for CSV/JSON files.
 * Includes AI-powered insights for data patterns.
 */

class DataLens {
    constructor() {
        this.containerId = 'data-lens-container';
        this.insightId = 'data-lens-insights';
        this.table = null;
    }

    /**
     * Initialize the Data Lens interface
     */
    async open(filename, content) {
        const extension = filename.split('.').pop().toLowerCase();

        // Switch to Plots/Data tab
        if (window.switchTab) window.switchTab('plots');

        const container = document.getElementById('plots-container');
        container.innerHTML = `
            <div id="data-lens-wrapper" class="flex flex-col h-full bg-[#1e1e1e] text-[#ccc] p-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-sm font-semibold flex items-center gap-2">
                        <i class="fas fa-table text-[#0D7C3D]"></i> Data Lens: ${filename}
                    </h3>
                    <div id="${this.insightId}" class="text-xs text-[#A1A1AA] animate-pulse">
                        <i class="fas fa-robot"></i> AI Analyzing schema...
                    </div>
                </div>
                <div id="${this.containerId}" class="flex-1 overflow-hidden rounded border border-[#333]"></div>
            </div>
        `;

        try {
            let data = [];
            if (extension === 'csv') {
                data = this._parseCSV(content);
            } else if (extension === 'json') {
                data = JSON.parse(content);
                if (!Array.isArray(data)) data = [data];
            }

            // Init Tabulator (Lightweight Grid)
            this.table = new Tabulator(`#${this.containerId}`, {
                data: data,
                autoColumns: true,
                layout: "fitColumns",
                pagination: "local",
                paginationSize: 20,
                placeholder: "No Data Available",
                theme: "dark"
            });

            // Trigger AI Analysis proactively
            this._runAIAnalysis(filename, data.slice(0, 10));

        } catch (e) {
            container.innerHTML = `<div class="p-8 text-red-500">Error loading Data Lens: ${e.message}</div>`;
        }
    }

    _parseCSV(text) {
        const lines = text.split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        return lines.slice(1).filter(l => l.trim()).map(line => {
            const values = line.split(',');
            const obj = {};
            headers.forEach((h, i) => obj[h] = values[i]?.trim());
            return obj;
        });
    }

    async _runAIAnalysis(filename, sample) {
        const insightEl = document.getElementById(this.insightId);
        if (!window.studioAI) return;

        const result = await window.studioAI.analyzeData(JSON.stringify(sample));

        if (result && result.result) {
            insightEl.classList.remove('animate-pulse');
            insightEl.innerHTML = `
                <div class="flex flex-col gap-1">
                    <span class="text-[#0D7C3D] font-bold"><i class="fas fa-check-circle"></i> AI Insights:</span>
                    <span class="text-[#ccc]">${result.result.summary || "Schema detected."}</span>
                    <div class="flex gap-2 mt-1">
                        ${(result.result.suggestions || []).map(s => `
                            <button onclick="window.dataLens.insertSnippet('${s.code}')" class="px-2 py-0.5 bg-[#2D2D2D] hover:bg-[#3D3D3D] rounded border border-[#444] text-[10px] transition-colors">
                                <i class="fas fa-plus"></i> ${s.label}
                            </button>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            insightEl.innerText = "Schema Analysis Complete.";
        }
    }

    insertSnippet(code) {
        if (window.editor) {
            const position = window.editor.getPosition();
            window.editor.executeEdits("data-lens", [{
                range: new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column),
                text: code
            }]);
            alert("Code snippet inserted!");
        }
    }
}

window.dataLens = new DataLens();
