# Kiri Research Labs

**The Post-Compute Research Lab** | [kiri.ng](https://kiri.ng)

A technology and research-focused enterprise developing software platforms, AI-driven solutions, and digital research tools for Africa.

---

## 🔬 About

Kiri Research Labs focuses on:
- **Edge AI Research** - Optimizing AI models for low-resource devices
- **NLP for African Languages** - Building models for Igbo, Yoruba, Pidgin
- **AI Safety** - Developing ethical AI systems for African contexts

## 🚀 Tech Stack

- **Backend**: Django 6.0 with HTMX
- **Package Manager**: uv
- **Authentication**: django-allauth
- **Static Files**: WhiteNoise + Tailwind CSS v4
- **Production**: Gunicorn + Nginx

## 🔧 Development

```bash
# Clone
git clone https://github.com/Nwokike/kiri.git
cd kiri

# Install dependencies
uv sync

# Run migrations
uv run python manage.py migrate

# Build CSS
npm install
npm run build:css

# Start server
uv run python manage.py runserver
```

## 🌍 Deployment

```bash
# On server
git pull origin main
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
sudo systemctl restart kiri
```

---

## 📄 License

Copyright © 2025–2026 Kiri Research Labs. All rights reserved.

This software is proprietary. See [LICENSE](LICENSE) for details.
