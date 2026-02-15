let deferredPrompt;
const installBtn = document.getElementById('pwa-install-btn');

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBtn) {
        installBtn.classList.remove('hidden');
        // Small delay to trigger CSS transition
        setTimeout(() => {
            installBtn.classList.add('visible');
        }, 100);
    }
});

if (installBtn) {
    installBtn.addEventListener('click', async (e) => {
        if (!deferredPrompt) {
            console.log('Install prompt not available');
            return;
        }

        // Hide the app provided install promotion
        installBtn.classList.remove('visible');
        setTimeout(() => installBtn.classList.add('hidden'), 300);

        try {
            // Show the prompt
            deferredPrompt.prompt();
            // Wait for the user to respond to the prompt
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User ${outcome === 'accepted' ? 'accepted' : 'dismissed'} the install prompt`);
        } catch (err) {
            console.error('Install prompt error:', err);
        } finally {
            deferredPrompt = null;
        }
    });
}
