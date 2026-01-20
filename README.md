# Kiri

**The Operating System for Modern Research** | [kiri.ng](https://kiri.ng)

---

## About

Kiri is a platform that democratizes access to research tools and knowledge, bridging the gap between advanced research and practical application.

### Key Features

- **🔬 Library** — Curated research papers and technical write-ups
- **🚀 Projects** — Showcase of innovative tools with instant previews
- **✨ Kiri Studio** — Client-side "Vibe Coding" IDE (Python + Node.js)
- **🤖 AI Advisor** — Automated architectural analysis for projects
- **👥 Community** — Space for researchers and developers to collaborate

### Platform Highlights

- Premium dark/light UI with PWA support
- AI-powered content discovery (Gemini 3.0 Flash)
- Mobile-first responsive design
- **Zero-server execution** via Pyodide (Wasm) and WebContainers

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design overview |
| [Deployment](docs/DEPLOYMENT.md) | Server setup guide |
| [Traffic Controller](docs/TRAFFIC_CONTROLLER.md) | Project preview system |
| [Kiri Studio](docs/KIRI_STUDIO.md) | Client-side IDE technical reference |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 6.0, HTMX |
| Frontend | Tailwind CSS v4 |
| Database | SQLite + R2 backups |
| Task Queue | Huey |
| Hosting | Debian + Nginx |

---

## License

**Copyright © 2026 Kiri Research Labs. All rights reserved.**

This software is proprietary. Unauthorized copying, modification, distribution, or use is strictly prohibited.
