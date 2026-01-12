import { pipeline, env } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.0';

// Skip local model checks
env.allowLocalModels = false;
env.useBrowserCache = true;

const inputEl = document.getElementById('input-text');
const outputEl = document.getElementById('output-text');
const srcLangEl = document.getElementById('src-lang');
const tgtLangEl = document.getElementById('tgt-lang');
const loader = document.getElementById('loader');
const loaderText = document.getElementById('loader-text');
const progressBar = document.getElementById('progress-bar');

let translator = null;
let timeoutId = null;

async function loadModel() {
    if (translator) return;

    loader.classList.remove('hidden');
    loaderText.innerText = "Downloading Model (once)...";

    try {
        translator = await pipeline('translation', 'Xenova/nllb-200-distilled-600M', {
            progress_callback: (data) => {
                if (data.status === 'progress') {
                    const percent = Math.round(data.progress * 100);
                    progressBar.style.width = percent + '%';
                    if (percent < 100) loaderText.innerText = `Downloading ${data.file} (${percent}%)`;
                }
            }
        });
        loader.classList.add('hidden');
    } catch (err) {
        console.error(err);
        loaderText.innerText = "Error loading model. Check console.";
        loaderText.classList.add('text-error');
    }
}

async function translate() {
    const text = inputEl.value.trim();
    if (!text) return;

    if (!translator) await loadModel();

    loader.classList.remove('hidden');
    loaderText.innerText = "Translating...";
    progressBar.style.width = '100%';

    try {
        // NLLB uses specific language codes like 'eng_Latn', 'fra_Latn'
        // Mapping (Simplified for demo)
        const langMap = {
            'en': 'eng_Latn',
            'fr': 'fra_Latn',
            'es': 'spa_Latn',
            'de': 'deu_Latn',
            'it': 'ita_Latn',
            'pt': 'por_Latn',
            'zh': 'zho_Hans',
            'ja': 'jpn_Jpan'
        };

        const src_lang = langMap[srcLangEl.value];
        const tgt_lang = langMap[tgtLangEl.value];

        const result = await translator(text, {
            src_lang: src_lang,
            tgt_lang: tgt_lang,
        });

        outputEl.value = result[0].translation_text;
    } catch (err) {
        console.error(err);
        outputEl.value = "Translation Error: " + err.message;
    } finally {
        loader.classList.add('hidden');
    }
}

// Debounce translation
inputEl.addEventListener('input', () => {
    document.getElementById('char-count').innerText = inputEl.value.length + " chars";

    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
        if (inputEl.value.length > 2) {
            translate();
        }
    }, 800);
});

// Helper buttons
document.getElementById('clear-btn').addEventListener('click', () => {
    inputEl.value = '';
    outputEl.value = '';
});

document.getElementById('copy-btn').addEventListener('click', () => {
    navigator.clipboard.writeText(outputEl.value);
});

// Handle language change
srcLangEl.addEventListener('change', translate);
tgtLangEl.addEventListener('change', translate);
