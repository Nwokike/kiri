/**
 * Kiri Studio Voice Coding
 * Integration with Groq Whisper for fast dictation.
 */

class VoiceCoding {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.btnId = 'voice-btn';
    }

    init() {
        this._injectUI();
    }

    _injectUI() {
        // Find terminal tab bar and inject mic icon
        const tabBar = document.querySelector('.tab-btn')?.parentElement;
        if (!tabBar) return;

        const micBtn = document.createElement('button');
        micBtn.id = this.btnId;
        micBtn.className = 'px-3 text-gray-400 hover:text-red-500 transition-colors';
        micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        micBtn.title = "Voice Code (Hold to speak)";

        micBtn.addEventListener('mousedown', () => this.startRecording());
        micBtn.addEventListener('mouseup', () => this.stopRecording());
        micBtn.addEventListener('mouseleave', () => { if (this.isRecording) this.stopRecording(); });

        tabBar.appendChild(micBtn);
    }

    async startRecording() {
        if (this.isRecording) return;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this._processVoice(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            document.getElementById(this.btnId).classList.replace('text-gray-400', 'text-red-500');
            document.getElementById(this.btnId).classList.add('animate-pulse');
        } catch (e) {
            console.error("Voice recording failed:", e);
            alert("Mic access denied or not available.");
        }
    }

    stopRecording() {
        if (!this.isRecording) return;
        this.mediaRecorder.stop();
        this.isRecording = false;
        document.getElementById(this.btnId).classList.replace('text-red-500', 'text-gray-400');
        document.getElementById(this.btnId).classList.remove('animate-pulse');
    }

    async _processVoice(blob) {
        if (!window.studioAI) return;

        console.log("[Voice] Transcribing...");
        const formData = new FormData();
        formData.append('file', blob, 'voice.webm');
        formData.append('task', 'transcribe');
        formData.append('requested_model', 'whisper-large-v3-turbo');

        try {
            const resp = await fetch('/projects/api/studio/ai/', {
                method: 'POST',
                headers: { 'X-CSRFToken': window.KIRI_CONFIG.csrfToken },
                body: formData
            });

            const data = await resp.json();
            if (data && data.text) {
                this._insertAtCursor(data.text);
            }
        } catch (e) {
            console.error("[Voice] Transcription Error:", e);
        }
    }

    _insertAtCursor(text) {
        if (window.editor) {
            const selection = window.editor.getSelection();
            const range = new monaco.Range(selection.startLineNumber, selection.startColumn, selection.endLineNumber, selection.endColumn);
            window.editor.executeEdits("voice", [{ range, text, forceMoveMarkers: true }]);
            window.editor.focus();
        }
    }
}

window.voiceCoding = new VoiceCoding();
