# Kiri Studio - Technical Reference

> **v1.2 (Stable)** | Client-Side IDE for "Vibe Coding"

## Overview
Kiri Studio is a zero-server, client-side IDE integrated into the Kiri platform. It leverages **WebAssembly (WASM)** and **Pyodide** to provide a full Python execution environment directly in the user's browser, eliminating the need for backend container orchestration.

## Core Architecture

```mermaid
flowchart TD
    User[User Browser]
    
    subgraph KiriStudio[Kiri Studio (Client-Side)]
        UI[Monaco Editor]
        Term[xterm.js Terminal]
        
        subgraph Runtimes
            PY[Pyodide (WASM)]
            WC[WebContainer (Draft)]
        end
        
        FS[Virtual File System]
    end
    
    Backend[Kiri Django Server]
    
    User --> UI
    UI -->|Code| FS
    FS -->|Read| PY
    
    PY -->|Output| Term
```

## Features

### 1. Python Runtime (Pyodide)
*   **Engine:** CPython compiled to WebAssembly.
*   **Capabilities:** Standard library, custom package loading, and SharedArrayBuffer for high performance.
*   **Isolation:** Runs entirely in a Web Worker (`pyodide_worker.js`) to keep the UI thread responsive.

### 2. Live Preview
*   **Static Assets**: Instant rendering of HTML/CSS/JS files.
*   **Hot Reload**: Virtual FS changes trigger immediate preview updates.

## Backend & Security Integration

### 1. Security Headers
To satisfy the requirements for `SharedArrayBuffer` and cross-origin resource fetching, Kiri implements:
- **Global CORP**: `Cross-Origin-Resource-Policy: cross-origin` allows fetching external assets.
- **Path-Specific COOP/COEP**: Applied to `/studio/` via `SecurityHeadersMiddleware`:
    - `Cross-Origin-Opener-Policy: same-origin`
    - `Cross-Origin-Embedder-Policy: require-corp`

### 2. Service Worker
The PWA Service Worker is **COEP-aware**, ensuring that cached responses are served with the proper headers to maintain the isolated context required for WASM.

## Roadmap
*   [x] COEP-aware Service Worker [x]
*   [x] Path-specific COOP/COEP isolation [x]
*   [x] SharedArrayBuffer performance [x]
*   [ ] Persistent Virtual FS to IndexedDB
*   [ ] Multi-file Pyodide support
