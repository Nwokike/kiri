window.dataLayer = window.dataLayer || [];
function gtag() { dataLayer.push(arguments); }
gtag('js', new Date());

const analyticsId = document.querySelector('meta[name="analytics-id"]')?.content;
if (analyticsId) {
    gtag('config', analyticsId);
}
