// PyStudio Engine (Python 3.11 + WASM)
// Handles Execution, File System, Plotting, and Git Sync

importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js");

let pyodide = null;
let micropip = null;
let mountPoint = "/home/pyodide";
let initError = null;

// --- Matplotlib Hook ---
// Intercepts plt.show() to render images in the browser
const MATPLOTLIB_PATCH = `
import sys, base64, io, os
import js
def _custom_show():
    try:
        import matplotlib.pyplot as plt
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.clf()
        js.postMessage(dict(type='image', content=img_str))
    except Exception as e:
        print(f"Plot Error: {e}")
`;

async function startEngine() {
    try {
        self.postMessage({ type: 'status', msg: 'Loading Kernel...' });
        pyodide = await loadPyodide();
        
        self.postMessage({ type: 'status', msg: 'Loading Libraries...' });
        await pyodide.loadPackage(["micropip", "openssl"]); // openssl for some requests
        micropip = pyodide.pyimport("micropip");

        // Mount OPFS (Persistent Storage)
        try {
            const root = await navigator.storage.getDirectory();
            await pyodide.mountNativeFS(mountPoint, root);
        } catch (e) { console.warn("OPFS Mount Warning:", e); }

        // Initialize Plotting & Zip Support
        await pyodide.runPythonAsync(MATPLOTLIB_PATCH);
        await pyodide.runPythonAsync(`import zipfile, io, os, shutil`);

        self.postMessage({ type: 'status', msg: 'Ready' });
        self.postMessage({ type: 'ready' });
        await listFiles();

    } catch (err) {
        initError = err;
        self.postMessage({ type: 'stderr', text: `Critical Engine Error: ${err.message}` });
        self.postMessage({ type: 'status', msg: 'Error' });
    }
}

// --- File Operations ---

async function listFiles() {
    if (!pyodide) return;
    try {
        // Filter out hidden files and system dirs
        const files = pyodide.runPython(`
import os
[f for f in os.listdir('${mountPoint}') if not f.startswith('.')]
        `);
        self.postMessage({ type: 'files', files: files.toJs() });
        files.destroy();
    } catch (e) { console.error(e); }
}

async function saveFile(filename, content) {
    if (typeof content === 'string') {
        pyodide.globals.set("filename_js", filename);
        pyodide.globals.set("content_js", content);
        pyodide.runPython(`with open(f"${mountPoint}/{filename_js}", "w") as f: f.write(content_js)`);
        pyodide.globals.delete("filename_js");
        pyodide.globals.delete("content_js");
    } else {
        // Binary Write (ArrayBuffer)
        const view = new Uint8Array(content);
        pyodide.FS.writeFile(`${mountPoint}/${filename}`, view);
    }
}

async function readFile(filename) {
    pyodide.globals.set("filename_js", filename);
    // Try reading as text, fallback handled by UI logic if needed
    return pyodide.runPython(`with open(f"${mountPoint}/{filename_js}", "r") as f: f.read()`);
}

// --- GitHub Sync Operations ---

async function exportAllFiles() {
    // Reads all text files to send to GitHub API
    // Binary files are skipped in this MVP sync
    const jsonStr = pyodide.runPython(`
import os, json
files_map = {}
for f in os.listdir('${mountPoint}'):
    path = f"${mountPoint}/{f}"
    if not f.startswith('.') and os.path.isfile(path):
        try:
            with open(path, "r", encoding='utf-8') as r:
                files_map[f] = r.read()
        except:
            pass # Skip binary
json.dumps(files_map)
    `);
    return JSON.parse(jsonStr);
}

async function unzipProject(zipBuffer) {
    // Unzips a GitHub archive into OPFS
    pyodide.globals.set("zip_bytes", new Uint8Array(zipBuffer));
    pyodide.runPython(`
import zipfile, io, os, shutil

# Clear current directory first (optional, but cleaner)
# for f in os.listdir('${mountPoint}'):
#     path = f"${mountPoint}/{f}"
#     if os.path.isfile(path): os.remove(path)

z = zipfile.ZipFile(io.BytesIO(zip_bytes.tobytes()))
for name in z.namelist():
    # GitHub zips usually have a root folder "repo-main/file.py"
    # We strip that root folder to get flat files
    parts = name.split('/')
    if len(parts) > 1 and not name.endswith('/'):
        clean_name = "/".join(parts[1:]) 
        if clean_name:
             # Ensure dest dir exists if nested (basic flat support for now)
             # For MVP flat file system, we replace / with _ or ignore folders
             flat_name = clean_name.replace('/', '_') 
             with z.open(name) as source, open(f"${mountPoint}/{flat_name}", "wb") as target:
                 target.write(source.read())
`);
    pyodide.globals.delete("zip_bytes");
    await listFiles();
}


// --- Main Message Handler ---

self.onmessage = async (event) => {
    const { cmd, code, filename, content, buffer } = event.data;
    
    if (!pyodide && cmd !== 'status') return;

    try {
        if (cmd === 'run') {
            self.postMessage({ type: 'start' });
            if (filename) await saveFile(filename, code);

            pyodide.setStdout({ batched: (text) => self.postMessage({ type: 'stdout', text }) });
            pyodide.setStderr({ batched: (text) => self.postMessage({ type: 'stderr', text }) });

            self.postMessage({ type: 'status', msg: 'Install...' });
            await pyodide.loadPackagesFromImports(code);

            // Ensure matplotlib patch is active
            const hasPlt = pyodide.runPython(`'matplotlib.pyplot' in sys.modules`);
            if (hasPlt) pyodide.runPython(`import matplotlib.pyplot as plt; plt.show = _custom_show`);
            
            self.postMessage({ type: 'status', msg: 'Running...' });
            await pyodide.runPythonAsync(code);
            
            await listFiles();
            self.postMessage({ type: 'status', msg: 'Ready' });
            self.postMessage({ type: 'finish' });
            
        } else if (cmd === 'save') {
            await saveFile(filename, content);
            await listFiles();
            
        } else if (cmd === 'read') {
            const fileContent = await readFile(filename);
            self.postMessage({ type: 'file_content', filename, content: fileContent });
            
        } else if (cmd === 'delete') {
             pyodide.runPython(`import os; os.remove(f"${mountPoint}/${filename}")`);
             await listFiles();
             
        } else if (cmd === 'get_sync_files') {
            const files = await exportAllFiles();
            self.postMessage({ type: 'sync_files_ready', files });
            
        } else if (cmd === 'load_repo_zip') {
            self.postMessage({ type: 'status', msg: 'Unzipping...' });
            await unzipProject(buffer);
            self.postMessage({ type: 'status', msg: 'Ready' });
            self.postMessage({ type: 'repo_loaded' });
        }

    } catch (err) {
        self.postMessage({ type: 'stderr', text: err.toString() });
        self.postMessage({ type: 'status', msg: 'Error' });
        self.postMessage({ type: 'finish' }); // Ensure UI unblocks
    }
};

startEngine();