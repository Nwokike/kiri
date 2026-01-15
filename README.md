# Kiri

**The Operating System for Modern Research** | [kiri.ng](https://kiri.ng)

---

## About

Kiri is a platform that democratizes access to research tools and knowledge, bridging the gap between advanced research and practical application.

### Key Features

- **🔬 Library** — Curated research papers and technical write-ups
- **🚀 Projects** — Showcase of innovative tools with instant previews
- **👥 Community** — Space for researchers and developers to collaborate
- **⚡ Traffic Controller** — Run projects instantly in your browser

### Platform Highlights

- Premium dark/light UI with PWA support
- AI-powered content discovery (Gemini 3.0 Flash)
- Mobile-first responsive design
- Zero-cost project previews via WebContainers, Binder, and Colab

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design overview |
| [Deployment](docs/DEPLOYMENT.md) | Server setup guide |
| [Traffic Controller](docs/TRAFFIC_CONTROLLER.md) | Project preview system |

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
