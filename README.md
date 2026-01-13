# Kiri

**The Operating System for Modern Research** | [kiri.ng](https://kiri.ng)

![Kiri Platform](https://kiri.ng/static/images/logos/logo.png)

---

## 🔬 About

Kiri is a platform designed to democratize access to research tools and knowledge. We bridge the gap between advanced research and practical application, fostering a community where ideas flow freely.

Key components:
*   **Library**: A curated collection of research papers, tutorials, and technical write-ups.
*   **Projects**: An open-source showcase of innovative tools and repositories from our community.
*   **Community**: A space for researchers and developers to connect and collaborate.

## 🚀 Key Features

*   **🎨 Premium UI**: A stunning, responsive interface featuring our signature Emerald Green & Gold brand colors.
*   **⚡ Progressive Web App (PWA)**: Fully installable with offline support and a native app-like experience.
*   **🌓 Dark Mode**: First-class dark mode support across the entire platform.
*   **🤖 AI Integration**: Powered by next-gen models for intelligent content discovery and interactions.
*   **📱 Mobile First**: deeply optimized mobile experience with bottom navigation and touch-friendly interactions.

## 🛠️ Tech Stack

*   **Backend**: Django 6.0 (Async) + HTMX
*   **Frontend**: Tailwind CSS v4 + Alpine.js
*   **Database**: SQLite (Production-ready with daily R2 backups)
*   **Task Queue**: Huey (SQLite backend)
*   **Storage**: Cloudflare R2 (Media & Backups)
*   **Deployment**: Debian 11 + Gunicorn + Nginx + UV

## 🔧 Development

```bash
# Clone the repository
git clone https://github.com/Nwokike/kiri.git
cd kiri

# Install dependencies (using uv)
uv sync

# Run migrations
uv run python manage.py migrate

# Generate CSS (Tailwind v4)
uv run python manage.py tailwind_build

# Start the development server
uv run python manage.py runserver
```

## 🌍 Deployment

Deployment is automated via GitHub Actions. Pushing to `main` triggers:
1.  Code sync via SSH.
2.  Dependency updates (`uv sync`).
3.  Database migrations.
4.  Static file collection.
5.  Zero-downtime service restart.

---

## 📄 License

**Copyright © 2026 Kiri Research Labs. All rights reserved.**

This software is proprietary. Unauthorized copying, modification, distribution, or use is strictly prohibited.
