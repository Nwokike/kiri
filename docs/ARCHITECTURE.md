# Kiri Architecture: Intelligence Scalable to Zero

**Date:** February 15, 2026
**Version:** 1.2

## Core Philosophy
To maximize scalability and operate within the constraints of strict cloud environments, Kiri adopts an **"Intelligence on the Edge"** strategy. We minimize server-side state and delegate heavy execution to the client's browser (WASM) or ephemeral cloud runners.

## 1. Storage & Task Strategy

### 1.1 GitHub-First Storage
- **Source of Truth**: All user code and publications are stored in GitHub repositories.
- **Kiri Role**: Acts as a high-fidelity interface for discovery, viewing, and intelligent execution.

### 1.2 Native Task Management
- **Scheduler**: Kiri uses **Native Django Tasks** (@task) and a custom management command (`run_periodic_tasks.py`).
- **Intervals**:
  - **Frequent (30m)**: GitHub metadata/stats sync.
  - **Daily**: Database backups to R2, Hot project updates.
- **Cleanup**: Ephemeral `tmp/` directories are purged hourly via `cleanup_tmp_files`.

## 2. Security & Isolation

### 2.1 Cross-Origin Isolation
To enable high-performance WASM features (SharedArrayBuffer), Kiri implements:
- **Global CORP**: `Cross-Origin-Resource-Policy: cross-origin` set in `settings.py` to allow resource sharing across origins.
- **Path-Specific COOP/COEP**: Applied to `/studio/` and `/playground/` via `SecurityHeadersMiddleware` to enable a strict secure context.

## 3. Benefits
1.  **State-Scalability**: The "Intelligence Scalable to Zero" model ensures the platform remains performant without massive infrastructure costs.
2.  **Ownership**: Users own their data (in their GitHub), ensuring no platform lock-in.
3.  **Privacy/Security**: Client-side execution (Pyodide) prevents user code logic from hitting our servers unless necessary.

## 4. Implementation Reference
- **Middleware**: `kiri_project.middleware.SecurityHeadersMiddleware`
- **Native Tasks**: `kiri_project.tasks.py`
- **Periodic Runner**: `core.management.commands.run_periodic_tasks`
- **Services**: `projects.services.GitHubService` for all file interactions.
