/**
 * Shared Alpine.js logic for the Kiri Tools App.
 * Handles common functionality like file uploads, clipboard, persistence, and sampling.
 */

window.toolSetup = function(overrides = {}) {
    return {
        input: '',
        file: null,
        output: '',
        error: '',
        statusMessage: '',
        copied: false,
        hideReset: false,
        hideSample: false,
        isProcessing: false,
        dragging: false,
        over: false,
        hideUpload: false,

        async handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            this.file = file;
            this.statusMessage = `Reading ${file.name}...`;
            this.error = '';

            // Handle specialized file processing if the tool provides a 'handleFiles' method
            if (typeof this.handleFiles === 'function') {
                this.handleFiles([file]);
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                this.input = e.target.result;
                this.statusMessage = `${file.name} loaded`;
                if (typeof this.convert === 'function') this.convert();
                if (typeof this.onFileLoaded === 'function') this.onFileLoaded(e.target.result);
            };
            reader.onerror = () => {
                this.error = 'Failed to read file';
                this.statusMessage = 'Load error';
            };
            reader.readAsText(file);
        },

        downloadFile(content, filename, mimeType) {
            if (!content) return;
            try {
                const blob = new Blob([content], { type: mimeType });
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.setAttribute("href", url);
                link.setAttribute("download", filename);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
                this.statusMessage = 'File downloaded';
            } catch (err) {
                this.error = 'Download failed';
            }
        },

        async copyToClipboard(text) {
            if (!text) return;
            try {
                await navigator.clipboard.writeText(text);
                this.copied = true;
                const oldMsg = this.statusMessage;
                this.statusMessage = '✓ Copied to clipboard';
                setTimeout(() => {
                    this.copied = false;
                    this.statusMessage = oldMsg;
                }, 2000);
            } catch (err) {
                this.error = 'Copy failed';
            }
        },

        resetTool() {
            this.input = '';
            this.output = '';
            this.error = '';
            this.statusMessage = 'Ready';
            if (this.$refs.fileInput) this.$refs.fileInput.value = '';
            if (typeof this.onReset === 'function') this.onReset();
        },

        loadSample() {
            this.statusMessage = 'Sample loading not implemented for this tool';
        },

        persist(key, propertyName, defaultValue = null) {
            const storageKey = `kiri_persist_${key}`;
            const saved = localStorage.getItem(storageKey);

            if (saved !== null) {
                try {
                    this[propertyName] = JSON.parse(saved);
                } catch (e) {
                    this[propertyName] = defaultValue !== null ? defaultValue : this[propertyName];
                }
            } else if (defaultValue !== null) {
                this[propertyName] = defaultValue;
            }

            this.$watch(propertyName, (val) => {
                localStorage.setItem(storageKey, JSON.stringify(val));
            });
        },

        clearPersist(key) {
            localStorage.removeItem(`kiri_persist_${key}`);
        },

        // Apply tool-specific overrides
        ...overrides
    }
}
