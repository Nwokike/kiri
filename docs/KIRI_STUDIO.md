# Kiri Studio Architecture

Kiri Studio is not a single IDE, but a unified interface for **Intelligence on the Edge**. It consists of two specialized runtime environments that share a common UI.

## 1. PyStudio 
* **Target:** Applied Research, Data Science, Education.
* **Engine:** `Pyodide` (Python 3.11 via WebAssembly).
* **Key Features:**
    * **OPFS Storage:** Mounts a persistent virtual hard drive to `/home/pyodide`.
    * **Matplotlib Hook:** Intercepts `plt.show()` to render plots in the IDE tab.
    * **Micropip:** Auto-installs pure Python wheels (Pandas, Numpy, Scikit-learn).
* **Worker:** `static/js/studio.py.worker.js`

## 2. JS Studio
* **Target:** Frontend Development, Full-Stack Node.js.
* **Engine:** `WebContainers` (Node.js via WebAssembly).
* **Key Features:**
    * **Virtual Network:** Runs a TCP network inside the browser tab.
    * **Live Preview:** Renders the user's localhost server (port 3000/5173) in an iframe.
    * **NPM Integration:** Full access to the npm registry.
* **Worker:** `static/js/studio.js.worker.js`

## The Shared UI Layer
Both studios share the same HTML shell (`kiri_studio.html`) but load different workers based on the URL parameter:
* `/studio/py/?repo=...` -> Loads PyStudio Worker
* `/studio/js/?repo=...` -> Loads JS Studio Worker

## GitHub Integration (Vibe Coding)
Both studios share the "Magic Sync" capability:
1.  **Pull:** Worker downloads/unzips the GitHub repo into the virtual FS.
2.  **Push:** Worker zips the modified FS -> API pushes to GitHub -> Updates Kiri Project.