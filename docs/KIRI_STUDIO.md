# Kiri Studio - Technical Reference

> **v1.0 (Beta)** | Client-Side IDE for "Vibe Coding"

## Overview
Kiri Studio is a zero-server, client-side IDE integrated into the Kiri platform. It leverages **WebAssembly (WASM)** and **WebContainers** to provide a full execution environment directly in the user's browser, eliminating the need for backend container orchestration (Docker/Kubernetes).

## Core Architecture

```mermaid
flowchart TD
    User[User Browser]
    
    subgraph KiriStudio[Kiri Studio (Client-Side)]
        UI[Monaco Editor]
        Term[xterm.js Terminal]
        
        subgraph Runtimes
            PY[Pyodide (WASM)]
            WC[WebContainer (Node.js)]
        end
        
        FS[Virtual File System]
    end
    
    Backend[Kiri Django Server]
    
    User --> UI
    UI -->|Code| FS
    FS -->|Mount| WC
    FS -->|Read| PY
    
    WC -->|Output| Term
    PY -->|Output| Term
    
    Backend -->|Context| KiriStudio
```

## Supported Runtimes

### 1. Python (Pyodide)
*   **Engine:** CPython compiled to WebAssembly (v0.25.0).
*   **Capabilities:** Standard library, `pip` install (pure python wheels), async/await.
*   **Use Case:** Data analysis, scripts, algorithm demos.
*   **Memory:** Runs within browser tab limit (~1-2GB).

### 2. Node.js (WebContainers)
*   **Engine:** Node.js running directly in browser via StackBlitz engine.
*   **Capabilities:** Full Node.js API, `npm install`, network stack, HTTP servers.
*   **Use Case:** React apps, Express servers, full-stack JS demos (Lane A projects).
*   **Security:** Requires `COOP: same-origin` and `COEP: require-corp` headers (handled by `SecurityHeadersMiddleware`).

## Backend Integration

### 1. Security Headers (`middleware.py`)
To enable `SharedArrayBuffer` for WebContainers, the `/studio/` path is protected by stricter isolation headers:
```python
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

### 2. Database Cache (`settings.py`)
To maximize available RAM for the client-side runtimes, the Django backend uses `DatabaseCache` (SQLite) instead of RAM-heavy `LocMemCache`.

### 3. URL Structure
*   **Path:** `/studio/`
*   **Arguments:** `?repo=username/repo` (Loads project context)

## Future Roadmap
*   [ ] GitHub Gist Sync (Save functionality)
*   [ ] Multi-file support in Pyodide
*   [ ] Persist virtual FS to IndexedDB
