# Kiri Research Labs

**The Post-Compute Research Lab** | [kiri.ng](https://kiri.ng)

![Kiri Platform](https://kiri.ng/static/images/logos/logo.png)

---

## 🔬 About

Kiri Research Labs is a technology and research-focused enterprise developing **Post-Compute** solutions. We build AI-driven platforms that bridge the gap between advanced research and practical application.

Kiri.ng serves as our central hub, featuring:
*   **Universal Translator**: Real-time speech-to-speech translation using Gemini 2.0 Flash.
*   **Project Showcase**: A portfolio of our "Hot" and "Featured" research initiatives.
*   **Publication Archive**: A repository of our technical papers and findings.

## 🚀 Key Features

*   **⚡ Progressive Web App (PWA)**: Installable on all devices with offline capabilities and a custom "Upside-Down" install experience.
*   **🤖 AI Integration**: Powered by Google's Gemini 2.0 Flash for lightning-fast multimodal processing.
*   **🔄 Background Processing**: Automated via `Huey` for tasks like daily database backups to Cloudflare R2 and GitHub stats syncing.
*   **🎨 Premium UI**: Built with Tailwind CSS v4 and a custom Design System for a "2026 Aesthetic".

## 🛠️ Tech Stack

*   **Backend**: Django 6.0 (Async) + HTMX
*   **Frontend**: Tailwind CSS v4 + Alpine.js + Transformers.js
*   **Database**: SQLite (Production-ready with daily R2 backups)
*   **Task Queue**: Huey (SQLite backend)
*   **Storage**: Cloudflare R2 (Media & Backups)
*   **Deployment**: Debian 11 + Gunicorn + Nginx + UV
*   **CI/CD**: GitHub Actions

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
5.  Zero-downtime service restart (`kiri`, `kiri-huey`, `nginx`).

### Manual Override

```bash
# SSH into server & run:
cd ~/kiri
git pull origin main
uv sync
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
sudo systemctl restart kiri kiri-huey
```

---

## 📄 License

**Copyright © 2024–2026 Kiri Research Labs. All rights reserved.**

This software is proprietary. Unauthorized copying, modification, distribution, or use is strictly prohibited. Use subject to license terms.
