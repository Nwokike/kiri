// JS Studio Engine (Node.js + WebContainers)
// Handles Execution, File System, Server Preview, and ZIP Import

import { WebContainer } from 'https://cdn.jsdelivr.net/npm/@webcontainer/api@1.1.0/+esm';
import * as fflate from 'https://cdn.jsdelivr.net/npm/fflate@0.8.2/+esm';

let webcontainerInstance = null;
let currentProcess = null;

async function startEngine() {
    try {
        self.postMessage({ type: 'status', msg: 'Booting Node.js...' });
        
        webcontainerInstance = await WebContainer.boot();
        
        webcontainerInstance.on('server-ready', (port, url) => {
            self.postMessage({ type: 'preview_ready', url });
            self.postMessage({ type: 'stdout', text: `\r\n\x1b[32m✔ Server running on ${url}\x1b[0m\r\n` });
        });

        self.postMessage({ type: 'status', msg: 'Ready' });
        self.postMessage({ type: 'ready' });
        await listFiles();

    } catch (err) {
        self.postMessage({ type: 'stderr', text: `Critical Engine Error: ${err.message}` });
        if (err.message.includes('SharedArrayBuffer')) {
            self.postMessage({ type: 'stderr', text: '\n\rError: Cross-Origin Isolation missing. Check Headers.' });
        }
    }
}

// --- File Operations ---

async function listFiles(path = '.') {
    if (!webcontainerInstance) return;
    try {
        const entries = await webcontainerInstance.fs.readdir(path, { withFileTypes: true });
        const files = entries
            .filter(e => e.isFile() && !e.name.startsWith('.'))
            .map(e => e.name);
            
        self.postMessage({ type: 'files', files });
    } catch (e) { console.error(e); }
}

async function saveFile(filename, content) {
    if (!webcontainerInstance) return;
    await webcontainerInstance.fs.writeFile(filename, content);
}

async function readFile(filename) {
    if (!webcontainerInstance) return "";
    return await webcontainerInstance.fs.readFile(filename, 'utf-8');
}

// --- Sync & Import Operations ---

async function exportAllFiles() {
    if (!webcontainerInstance) return {};
    const filesMap = {};
    const entries = await webcontainerInstance.fs.readdir('.', { withFileTypes: true });
    
    for (const entry of entries) {
        if (entry.isFile() && !entry.name.startsWith('.') && entry.name !== 'node_modules' && !entry.name.endsWith('.lock')) {
            try {
                filesMap[entry.name] = await webcontainerInstance.fs.readFile(entry.name, 'utf-8');
            } catch (e) {}
        }
    }
    return filesMap;
}

async function mountProject(zipBuffer) {
    if (!zipBuffer) {
        // Fallback: Create default React Starter if no repo provided
        await saveFile('package.json', JSON.stringify({
            name: "kiri-react", type: "module",
            scripts: { "dev": "vite", "build": "vite build" },
            dependencies: { "react": "^18.2.0", "react-dom": "^18.2.0" },
            devDependencies: { "@vitejs/plugin-react": "^4.2.1", "vite": "^5.2.0" }
        }, null, 2));
        await saveFile('index.html', '<!doctype html><body><div id="root"></div><script type="module" src="/main.jsx"></script></body>');
        await saveFile('main.jsx', 'import React from "react"; import ReactDOM from "react-dom/client"; import App from "./App.jsx"; ReactDOM.createRoot(document.getElementById("root")).render(<App />);');
        await saveFile('App.jsx', 'export default function App() { return <div style={{padding:20}}><h1>🚀 Kiri JS Studio</h1><p>Edit App.jsx to see live updates!</p></div> }');
        await listFiles();
        return;
    }

    // Real Unzip using fflate
    const uint8Array = new Uint8Array(zipBuffer);
    const unzipped = fflate.unzipSync(uint8Array);
    
    // WebContainer mount tree
    const mountTree = {};
    
    for (const [path, data] of Object.entries(unzipped)) {
        // Strip top-level folder (e.g., 'repo-main/')
        const parts = path.split('/');
        if (parts.length > 1 && !path.endsWith('/')) {
            const filename = parts.slice(1).join('/'); // Flatten slightly?
            // For MVP simplicity in Studio UI, we only mount root files or flatten src/
            // But WebContainers support folders. Let's stick to root files + flat 'src_' for now 
            // or better: just write files one by one.
            
            // Note: writing one by one is slower but safer for flat file list UI
            // We will filter for files that are crucial (src, public, config)
            if (filename.startsWith('.')) continue;
            
            // Write directly to FS
            // Flattening deeply nested paths for the specific Kiri flat-view UI
            const flatName = filename.replace(/\//g, '_'); 
            webcontainerInstance.fs.writeFile(flatName, data);
        }
    }
    
    await listFiles();
}

// --- Execution ---

async function runCommand(commandString) {
    if (currentProcess) {
        // currentProcess.kill(); 
    }

    const args = commandString.split(' ');
    const cmd = args.shift();

    self.postMessage({ type: 'status', msg: 'Exec...' });
    
    try {
        const process = await webcontainerInstance.spawn(cmd, args);
        currentProcess = process;

        process.output.pipeTo(new WritableStream({
            write(data) { self.postMessage({ type: 'stdout', text: data }); }
        }));

        const exitCode = await process.exit;
        self.postMessage({ type: 'stdout', text: `\r\n[Exit Code ${exitCode}]\r\n` });
        self.postMessage({ type: 'finish' });
        
    } catch (e) {
        self.postMessage({ type: 'stderr', text: e.message });
        self.postMessage({ type: 'finish' });
    }
}

// --- Message Handler ---

self.onmessage = async (event) => {
    const { cmd, code, filename, content, buffer } = event.data;
    
    if (cmd === 'status') return;
    if (!webcontainerInstance && cmd !== 'status') return;

    try {
        if (cmd === 'run') {
            // Auto-detect install necessity
            const hasNodeModules = await webcontainerInstance.fs.readdir('node_modules').catch(() => false);
            if (!hasNodeModules) {
                self.postMessage({ type: 'stdout', text: '📦 Installing dependencies (first run only)...\r\n' });
                await runCommand('npm install');
            }
            await runCommand('npm run dev');
            
        } else if (cmd === 'save') {
            await saveFile(filename, content);
            await listFiles();
            
        } else if (cmd === 'read') {
            const fileContent = await readFile(filename);
            self.postMessage({ type: 'file_content', filename, content: fileContent });
            
        } else if (cmd === 'delete') {
             await webcontainerInstance.fs.rm(filename);
             await listFiles();
             
        } else if (cmd === 'get_sync_files') {
            const files = await exportAllFiles();
            self.postMessage({ type: 'sync_files_ready', files });
            
        } else if (cmd === 'load_repo_zip') {
            self.postMessage({ type: 'status', msg: 'Unpacking...' });
            await mountProject(buffer);
            self.postMessage({ type: 'status', msg: 'Ready' });
            self.postMessage({ type: 'repo_loaded' });
        }

    } catch (err) {
        self.postMessage({ type: 'stderr', text: err.toString() });
        self.postMessage({ type: 'status', msg: 'Error' });
    }
};

startEngine();