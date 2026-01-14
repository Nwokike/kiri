/* About Page Micro-interactions - 2026 Premium Aesthetic */

document.addEventListener('DOMContentLoaded', () => {
    // Scroll Reveal implementation
    const reveals = document.querySelectorAll('.reveal');

    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const revealPoint = 150;

        reveals.forEach(reveal => {
            const revealTop = reveal.getBoundingClientRect().top;
            if (revealTop < windowHeight - revealPoint) {
                reveal.classList.add('active');
            }
        });
    };

    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // Initial check

    // Platform card hover interactions
    const cards = document.querySelectorAll('.platform-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            // Potential for sound effects or cursor changes
        });
    });

});
