/**
 * Kiri Studio Global Magic Bar
 * Triggered by Ctrl+K.
 * Intent-driven autonomous coding.
 */

class MagicBar {
    constructor() {
        this.isOpen = false;
        this.overlay = null;
        this.input = null;
    }

    init() {
        window.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                this.toggle();
            }
            if (e.key === 'Escape' && this.isOpen) this.close();
        });
        this._createUI();
    }

    _createUI() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'fixed inset-0 bg-black/60 backdrop-blur-md z-[100] hidden flex items-start justify-center pt-[15vh] transition-all duration-300';
        this.overlay.id = 'magic-bar-overlay';

        this.overlay.innerHTML = `
            <div class="w-full max-w-2xl bg-[#252526] border border-[#333] shadow-2xl rounded-xl overflow-hidden animate-in fade-in zoom-in duration-200">
                <div class="flex items-center px-4 py-3 bg-[#1e1e1e] border-b border-[#333]">
                    <i class="fas fa-magic text-[#0D7C3D] mr-3"></i>
                    <input type="text" id="magic-bar-input" placeholder="What magic do you want to perform?" 
                        class="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder-gray-500 font-sans">
                    <span class="text-[10px] text-gray-500 font-mono bg-[#333] px-2 py-0.5 rounded ml-2">ESC to close</span>
                </div>
                <div id="magic-bar-results" class="max-h-[60vh] overflow-y-auto p-2 space-y-1 hidden">
                    <!-- Suggestions will appear here -->
                </div>
                <div id="magic-bar-loading" class="p-8 text-center hidden">
                    <i class="fas fa-circle-notch fa-spin text-[#0D7C3D] text-2xl"></i>
                    <p class="text-xs text-gray-400 mt-2">Invoking AI agents...</p>
                </div>
            </div>
        `;

        document.body.appendChild(this.overlay);
        this.input = document.getElementById('magic-bar-input');

        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.execute();
        });
    }

    toggle() {
        if (this.isOpen) this.close();
        else this.open();
    }

    open() {
        this.isOpen = true;
        this.overlay.classList.remove('hidden');
        this.input.focus();
        this.input.value = '';
    }

    close() {
        this.isOpen = false;
        this.overlay.classList.add('hidden');
    }

    async execute() {
        const intent = this.input.value;
        if (!intent || !window.studioAI) return;

        const resultsEl = document.getElementById('magic-bar-results');
        const loadingEl = document.getElementById('magic-bar-loading');

        resultsEl.classList.add('hidden');
        loadingEl.classList.remove('hidden');

        try {
            const context = window.editor ? window.editor.getValue() : '';
            const res = await window.studioAI.askAssistant(intent, context);

            if (res && res.result) {
                this._insertCode(res.result.code || res.result);
                this.close();
            } else {
                alert("Magic failed. Try a different spell.");
            }
        } catch (e) {
            console.error("Magic Bar Error:", e);
        } finally {
            loadingEl.classList.add('hidden');
        }
    }

    _insertCode(code) {
        if (window.editor) {
            const selection = window.editor.getSelection();
            const range = new monaco.Range(selection.startLineNumber, selection.startColumn, selection.endLineNumber, selection.endColumn);
            window.editor.executeEdits("magic", [{ range, text: code, forceMoveMarkers: true }]);
        }
    }
}

window.magicBar = new MagicBar();
