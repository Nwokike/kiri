/**
 * Kiri Studio Core Logic (Mobile Optimized) - UPDATED
 * Handles UI, Worker Communication, GitHub Sync, and File Actions.
 * Requires window.KIRI_CONFIG.
 */

// Global State
let editor, term, fitAddon, worker;
let isRunning = false;
let currentFile = 'main.py';
let fileCache = {};
let connectedRepo = null;
let contextTargetFile = null;

document.addEventListener('DOMContentLoaded', () => {
    initTerminal();
    initMonaco();
    initWorker();
    checkRepoParam();
    setupEventListeners();
});

// --- Worker Logic ---
function initWorker() {
    if (!window.Worker) {
        term.writeln('\x1b[31mError: Web Workers not supported in this browser.\x1b[0m');
        return;
    }

    const isPy = window.KIRI_CONFIG.studioType === 'py';
    const workerPath = isPy ? window.KIRI_CONFIG.workerPyUrl : window.KIRI_CONFIG.workerJsUrl;

    // CRITICAL FIX: Pyodide needs 'classic' (for importScripts),
    // WebContainers / ESM-based workers need 'module'.
    const workerType = isPy ? 'classic' : 'module';

    try {
        worker = new Worker(workerPath, { type: workerType });
    } catch (e) {
        term.writeln(`\x1b[31mWorker Init Error: ${e.message}\x1b[0m`);
        return;
    }

    worker.onmessage = (e) => {
        const { type, text, msg, files, content, filename, url } = e.data;

        if (type === 'stdout') term.write(text);
        else if (type === 'stderr') term.write(`\x1b[31m${text}\x1b[0m`);
        else if (type === 'image') handlePlot(content);
        else if (type === 'preview_ready') handlePreview(url);
        else if (type === 'status') updateStatus(msg);
        else if (type === 'ready') handleReady();
        else if (type === 'files') renderFileList(files);
        else if (type === 'file_content') {
            updateEditor(filename, content);
            if (window.pendingDataLensFile === filename && window.dataLens) {
                window.dataLens.open(filename, content);
                window.pendingDataLensFile = null;
            }
        }
        else if (type === 'sync_files_ready') performSync(e.data.files);
        else if (type === 'repo_loaded') {
            term.writeln('\x1b[32m✔ Repository Loaded.\x1b[0m');
            worker.postMessage({ cmd: 'list_files' });
            // --- PHASE 6: SEMANTIC INDEXING ---
            if (window.semanticSearch && e.data.files) {
                window.semanticSearch.indexRepository(e.data.files);
            }
        }
        else if (type === 'finish') setRunState(false);
        else if (type === 'start') setRunState(true);
    };

    worker.onerror = (e) => {
        // Some browsers provide lineno; fall back gracefully.
        const lineno = e.lineno || e.lineNumber || 'unknown';
        term.writeln(`\x1b[31mWorker Error: ${e.message} (Line ${lineno})\x1b[0m`);
        setRunState(false);
    };
}

// --- Preview & Plot Logic ---
function handlePreview(url) {
    const container = document.getElementById('plots-container');
    container.innerHTML = '';
    const iframe = document.createElement('iframe');
    iframe.src = url;
    iframe.className = 'w-full h-full bg-white rounded shadow-lg border border-gray-700';
    iframe.style.minHeight = '400px';
    container.appendChild(iframe);
    switchTab('plots');
}

function handlePlot(content) {
    const container = document.getElementById('plots-container');
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${content}`;
    img.className = 'w-full rounded bg-white p-2 shadow-lg mb-4';
    container.appendChild(img);
    img.scrollIntoView({ behavior: 'smooth' });
    switchTab('plots');
}

// --- GitHub Sync ---
function openGitHubModal() { document.getElementById('github-modal').classList.remove('hidden'); }

function updateGitHubUI() {
    if (connectedRepo) {
        document.getElementById('github-btn-text').innerText = 'Sync';
        document.getElementById('gh-repo-link').href = `https://github.com/${connectedRepo}`;
        document.getElementById('gh-repo-link').innerText = connectedRepo;
        document.getElementById('gh-state-new').classList.add('hidden');
        document.getElementById('gh-state-connected').classList.remove('hidden');
    }
}

function syncToGitHub(isNew) {
    document.getElementById('gh-loading').classList.remove('hidden');
    window.pendingSyncIsNew = isNew;
    worker.postMessage({ cmd: 'get_sync_files' });
}

async function performSync(files) {
    const repoName = document.getElementById('repo-name-input').value;
    const isNew = window.pendingSyncIsNew;

    try {
        const resp = await fetch(window.KIRI_CONFIG.apiSyncUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.KIRI_CONFIG.csrfToken },
            body: JSON.stringify({
                files: files,
                create_new: isNew,
                repo_name: repoName,
                repo_full_name: connectedRepo,
                studio_type: window.KIRI_CONFIG.studioType
            })
        });
        const data = await resp.json();

        if (data.status === 'success') {
            const full_name = data.repo_url.split('github.com/')[1];
            connectedRepo = full_name;
            updateGitHubUI();
            alert(data.message);
            document.getElementById('github-modal').classList.add('hidden');
        } else {
            alert("Error: " + data.error);
        }
    } catch (err) { alert("Network Error: " + err); }
    document.getElementById('gh-loading').classList.add('hidden');
}

// --- File Actions & Menu ---

function renderFileList(files) {
    const listEl = document.getElementById('file-list');
    listEl.innerHTML = '';
    files.sort().forEach(file => {
        const div = document.createElement('div');
        // Mobile-friendly row with explicit Action Button
        div.className = `group flex items-center justify-between px-3 py-2.5 text-sm cursor-pointer border-b border-[#333]/30 hover:bg-[#2D2D2D] transition-colors ${file === currentFile ? 'bg-[#37373D] text-white' : 'text-[#CCCCCC]'}`;

        div.innerHTML = `
            <div class="flex items-center gap-3 overflow-hidden flex-1" onclick="openFile('${file}')">
                <i class="far fa-file text-[#A1A1AA]"></i>
                <span class="truncate font-medium">${file}</span>
            </div>
            <button onclick="showFileMenu(event, '${file}')" class="p-2 text-gray-400 hover:text-white rounded-full hover:bg-white/10 active:bg-white/20 transition-all opacity-100 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100">
                <i class="fas fa-ellipsis-v text-xs"></i>
            </button>
        `;
        listEl.appendChild(div);
    });
}

function openFile(file) {
    currentFile = file;
    worker.postMessage({ cmd: 'read', filename: file });
    worker.postMessage({ cmd: 'list_files' }); // Refresh highlighting

    // --- PHASE 6: DATA LENS HOOK ---
    const ext = file.split('.').pop().toLowerCase();
    if (['csv', 'json'].includes(ext) && window.dataLens) {
        // We need the content to open Data Lens. 
        // We'll wait for the 'file_content' message from the worker.
        window.pendingDataLensFile = file;
    }

    // On mobile, auto-close sidebar after selection
    if (window.innerWidth < 768) toggleSidebar();
}

function showFileMenu(e, filename) {
    e.preventDefault();
    e.stopPropagation();
    contextTargetFile = filename;

    const menu = document.getElementById('file-action-menu');
    const btnRect = e.currentTarget.getBoundingClientRect();

    // Position menu near the button (Popover style)
    // Prevent going off-screen bottom
    const menuHeight = 160;
    let top = btnRect.bottom + 5;
    if (top + menuHeight > window.innerHeight) {
        top = btnRect.top - menuHeight - 5;
    }

    menu.style.left = `${btnRect.left - 180}px`; // Align to right of button roughly
    menu.style.top = `${top}px`;
    menu.classList.remove('hidden');
}

async function handleContextAction(action) {
    if (!contextTargetFile) return;
    const menu = document.getElementById('file-action-menu');
    menu.classList.add('hidden');

    if (action === 'run') {
        openFile(contextTargetFile);
        setTimeout(() => {
            worker.postMessage({ cmd: 'run', code: editor.getValue(), filename: contextTargetFile });
            switchTab('terminal');
        }, 300);

    } else if (action === 'delete') {
        if (confirm(`Delete ${contextTargetFile}?`)) {
            worker.postMessage({ cmd: 'delete', filename: contextTargetFile });
        }
    } else if (action === 'rename') {
        const newName = prompt("Rename file to:", contextTargetFile);
        if (newName && newName !== contextTargetFile) {
            // NOTE: Proper rename support should be implemented server/worker-side.
            // For now, recommend manual create/delete flow to avoid race conditions.
            alert("Rename not supported yet. Create new file and delete old.");
        }
    } else if (action === 'publish') {
        document.getElementById('pub-title').value = contextTargetFile.replace(/\.(md|py|js|jsx)$/, '').replace(/_/g, ' ');
        document.getElementById('publish-modal').classList.remove('hidden');
        worker.postMessage({ cmd: 'read', filename: contextTargetFile });
    }
}

async function submitPublication() {
    const title = document.getElementById('pub-title').value;
    const attachCode = document.getElementById('pub-attach-code').checked;
    const content = editor.getValue();

    try {
        const resp = await fetch(window.KIRI_CONFIG.apiPublishUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.KIRI_CONFIG.csrfToken
            },
            body: JSON.stringify({
                title: title,
                content: content,
                repo_url: connectedRepo ? `https://github.com/${connectedRepo}` : '',
                script_content: attachCode ? content : ''
            })
        });

        const data = await resp.json();
        if (data.status === 'success') {
            if (confirm('Draft created! Open in editor?')) window.open(data.url, '_blank');
            document.getElementById('publish-modal').classList.add('hidden');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (err) { alert('Network error: ' + err); }
}

// --- Repo Loading ---
async function checkRepoParam() {
    const params = new URLSearchParams(window.location.search);
    const repo = params.get('repo');

    if (repo) {
        connectedRepo = repo.replace('https://github.com/', '');
        updateGitHubUI();
        term.writeln(`\r\n\x1b[33m⬇ Pulling ${connectedRepo}...\x1b[0m`);
        try {
            const apiUrl = `${window.KIRI_CONFIG.apiProxyUrl}?repo=${encodeURIComponent(repo)}`;
            const resp = await fetch(apiUrl);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const blob = await resp.blob();
            const buffer = await blob.arrayBuffer();
            worker.postMessage({ cmd: 'load_repo_zip', buffer: buffer }, [buffer]);
        } catch (err) {
            term.writeln(`\x1b[31mError pulling repo: ${err.message}\x1b[0m`);
        }
    } else {
        if (window.KIRI_CONFIG.studioType === 'py') {
            setTimeout(() => worker.postMessage({ cmd: 'save', filename: 'main.py', content: 'print("Hello Kiri!")' }), 1000);
        } else {
            setTimeout(() => worker.postMessage({ cmd: 'load_repo_zip', buffer: null }), 1000);
        }
    }
}

// --- Helpers ---
function updateEditor(filename, content) {
    if (filename === currentFile && editor.getValue() !== content) {
        editor.setValue(content);
        document.getElementById('current-filename').innerText = filename;
    }
}

function updateStatus(msg) {
    const el = document.getElementById('runtime-status');
    if (!el) return;
    el.querySelector('span').innerText = msg;
    if (msg === 'Ready') {
        el.classList.replace('text-yellow-500', 'text-green-500');
        el.classList.remove('animate-pulse');
    }
}

function handleReady() {
    updateStatus('Ready');
    term.writeln(`\x1b[32m✔ Environment Ready.\x1b[0m`);
    document.getElementById('run-btn').disabled = false;

    // --- PHASE 6: INITIALIZE SERVICES ---
    if (window.voiceCoding) window.voiceCoding.init();
    if (window.magicBar) window.magicBar.init();

    const searchInput = document.getElementById('ai-search-input');
    if (searchInput && window.semanticSearch) {
        searchInput.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value;
                if (!query) return;

                term.writeln(`\r\n\x1b[35m🔍 Semantic Search: "${query}"...\x1b[0m`);
                const results = await window.semanticSearch.search(query);

                if (results.length > 0) {
                    term.writeln(`\x1b[32mTop Matches:\x1b[0m`);
                    results.forEach(r => {
                        term.writeln(` - ${r.filename} (Similarity: ${(r.score * 100).toFixed(1)}%)`);
                    });
                } else {
                    term.writeln(`\x1b[31mNo relevant code found.\x1b[0m`);
                }
            }
        });
    }
}

function setRunState(running) {
    isRunning = running;
    const btn = document.getElementById('run-btn');
    if (running) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        btn.disabled = true;
    } else {
        btn.innerHTML = '<i class="fas fa-play text-xs"></i> <span class="hidden sm:inline">Run</span>';
        btn.disabled = false;
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (window.innerWidth < 1280) {
        const isHidden = sidebar.classList.contains('-translate-x-full');
        if (isHidden) {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.remove('hidden');
            setTimeout(() => overlay.classList.add('opacity-100'), 10);
        } else {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.remove('opacity-100');
            setTimeout(() => overlay.classList.add('hidden'), 300);
        }
    } else {
        sidebar.classList.toggle('collapsed');
        setTimeout(() => {
            if (editor) editor.layout();
        }, 300);
    }
}

function toggleSidePanel() {
    const panel = document.getElementById('side-panel');
    panel.classList.toggle('collapsed');
    panel.classList.toggle('active');

    setTimeout(() => {
        if (editor) editor.layout();
        if (fitAddon) fitAddon.fit();
    }, 300);
}

function switchTab(tab) {
    const sidePanel = document.getElementById('side-panel');
    if (sidePanel) {
        sidePanel.classList.remove('collapsed');
        sidePanel.classList.add('active');
    }

    document.getElementById('view-terminal').classList.add('hidden');
    document.getElementById('view-plots').classList.add('hidden');
    document.getElementById(`view-${tab}`).classList.remove('hidden');

    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('text-[#0D7C3D]', 'border-[#0D7C3D]');
        b.classList.add('text-[#A1A1AA]', 'border-transparent');
    });

    const activeTab = document.getElementById(`tab-${tab}`);
    if (activeTab) {
        activeTab.classList.add('text-[#0D7C3D]', 'border-[#0D7C3D]');
        activeTab.classList.remove('text-[#A1A1AA]', 'border-transparent');
    }

    if (tab === 'terminal' && fitAddon) fitAddon.fit();
    setTimeout(() => {
        if (editor) editor.layout();
    }, 300);
}

function createNewFile() {
    const defaultName = window.KIRI_CONFIG.studioType === 'py' ? "script.py" : "index.js";
    const name = prompt("Filename:", defaultName);
    if (name) worker.postMessage({ cmd: 'save', filename: name, content: '' });
}

// --- Init Libs ---
function initTerminal() {
    term = new Terminal({ theme: { background: '#1E1E1E', foreground: '#CCCCCC', cursor: '#0D7C3D' }, fontFamily: '"JetBrains Mono", monospace', fontSize: 13 });
    fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    term.open(document.getElementById('terminal'));
    fitAddon.fit();
    window.addEventListener('resize', () => {
        setTimeout(() => {
            if (fitAddon) fitAddon.fit();
        }, 100);
    });
}

function initMonaco() {
    require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });
    require(['vs/editor/editor.main'], function () {
        editor = monaco.editor.create(document.getElementById('monaco-editor'), {
            value: "",
            language: window.KIRI_CONFIG.studioType === 'py' ? 'python' : 'javascript',
            theme: 'vs-dark',
            fontSize: 14,
            fontFamily: '"JetBrains Mono", monospace',
            automaticLayout: true,
            minimap: { enabled: false }
        });

        let saveTimeout;
        editor.onDidChangeModelContent(() => {
            document.getElementById('unsaved-indicator').classList.remove('hidden');
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                if (worker && currentFile) {
                    worker.postMessage({ cmd: 'save', filename: currentFile, content: editor.getValue() });
                    document.getElementById('unsaved-indicator').classList.add('hidden');
                }
            }, 1000);
        });

        // --- PHASE 6: GHOST TEXT INTEGRATION ---
        if (window.studioAI) {
            monaco.languages.registerInlineCompletionsProvider(window.KIRI_CONFIG.studioType === 'py' ? 'python' : 'javascript', {
                provideInlineCompletions: async function (model, position, context, token) {
                    // Extract context: lines leading up to the cursor
                    const textUntilPosition = model.getValueInRange({
                        startLineNumber: Math.max(1, position.lineNumber - 30),
                        startColumn: 1,
                        endLineNumber: position.lineNumber,
                        endColumn: position.column
                    });

                    // Basic sanity check: don't trigger on tiny inputs
                    if (textUntilPosition.trim().length < 5) return { items: [] };

                    // Call the AI Orchestrator (Ghost Lane)
                    const prediction = await window.studioAI.completeCode(textUntilPosition, window.KIRI_CONFIG.studioType);

                    if (prediction && prediction.result && prediction.result.code) {
                        return {
                            items: [{
                                insertText: prediction.result.code,
                                range: new monaco.Range(
                                    position.lineNumber, position.column,
                                    position.lineNumber, position.column
                                )
                            }]
                        };
                    }
                    return { items: [] };
                },
                freeInlineCompletions: true
            });
        }
    });
}

function setupEventListeners() {
    document.getElementById('run-btn').addEventListener('click', () => {
        if (!worker || isRunning) return;
        term.clear();
        switchTab('terminal');
        worker.postMessage({ cmd: 'run', code: editor.getValue(), filename: currentFile });
    });

    // Update cursor position in UI
    if (editor) {
        editor.onDidChangeCursorPosition((e) => {
            const pos = document.getElementById('cursor-pos');
            if (pos) pos.innerText = `${e.position.lineNumber}:${e.position.column}`;
        });
    }

    // Bind Globals
    window.switchTab = switchTab;
    window.toggleSidebar = toggleSidebar;
    window.createNewFile = createNewFile;
    window.openGitHubModal = openGitHubModal;
    window.syncToGitHub = syncToGitHub;
    window.performSync = performSync;
    window.showFileMenu = showFileMenu;
    window.handleContextAction = handleContextAction;
    window.openFile = openFile;
    window.submitPublication = submitPublication;

    // Close menu on click elsewhere
    document.addEventListener('click', () => {
        const menu = document.getElementById('file-action-menu');
        if (menu) menu.classList.add('hidden');
    });
}
