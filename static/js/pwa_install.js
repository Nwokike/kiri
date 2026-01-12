let deferredPrompt;
const installBtn = document.getElementById('pwa-install-btn');

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later.
    deferredPrompt = e;
    // Update UI to notify the user they can add to home screen
    if (installBtn) {
        installBtn.classList.remove('hidden');
        installBtn.classList.add('flex'); // Assuming flex layout
    }
});

if (installBtn) {
    installBtn.addEventListener('click', async (e) => {
        if (!deferredPrompt) {
            console.log('Install prompt not available');
            return;
        }

        // Hide the app provided install promotion
        installBtn.classList.add('hidden');
        installBtn.classList.remove('flex');

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
