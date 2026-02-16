/**
 * Kiri Studio P2P Collaboration
 * Powered by Yjs and WebRTC.
 * Serverless Real-Time Collaboration.
 */

class PeerToPeer {
    constructor() {
        this.ydoc = null;
        this.provider = null;
        this.isSyncing = false;
    }

    async init(roomId) {
        if (this.isSyncing) return;

        console.log(`[P2P] Joining Room: ${roomId}`);

        const { Doc } = await import('https://cdn.jsdelivr.net/npm/yjs@13.6.10/+esm');
        const { WebRtcProvider } = await import('https://cdn.jsdelivr.net/npm/y-webrtc@10.3.0/+esm');
        const { MonacoBinding } = await import('https://cdn.jsdelivr.net/npm/y-monaco@0.1.4/+esm');

        this.ydoc = new Doc();
        this.provider = new WebRtcProvider(roomId, this.ydoc);

        const type = this.ydoc.getText('monaco');

        if (window.editor) {
            new MonacoBinding(type, window.editor.getModel(), new Set([window.editor]), this.provider.awareness);
            this.isSyncing = true;
            console.log("[P2P] Sync active.");
        }
    }
}

window.collab = new PeerToPeer();
// To join: window.collab.init('kiri-room-name')
