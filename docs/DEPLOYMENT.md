# Deployment Guide

> How to deploy Kiri to production.

## Requirements

- Debian 11+ server (1GB+ RAM)
- Python 3.12+
- Node.js 20+ (for Tailwind CSS)
- Nginx
- Domain with Cloudflare DNS

## Quick Deploy

```bash
# Clone and setup
git clone https://github.com/Nwokike/kiri.git
cd kiri
uv sync

# Environment
cp .env.example .env
# Edit .env with your keys

# Database
uv run python manage.py migrate

# Static files
uv run python manage.py tailwind_build
uv run python manage.py collectstatic --noinput

# Start services
sudo systemctl start kiri gunicorn huey
```

## Services

| Service | Command | Port |
|---------|---------|------|
| Gunicorn | `gunicorn kiri_project.wsgi` | 8000 |
| Huey | `uv run python manage.py run_huey` | - |
| Nginx | `systemctl start nginx` | 80/443 |

## Environment Variables

See `.env.example` for all required variables:

- `SECRET_KEY` - Django secret
- `GEMINI_API_KEY` - AI classification
- `GROQ_API_KEY` - AI fallback
- `R2_*` - Cloudflare R2 storage
- `KIRI_BOT_*` - GitHub bot for Traffic Controller

## GitHub Actions

Pushing to `main` triggers automatic deployment:
1. SSH into server
2. Pull latest code
3. Update dependencies
4. Run migrations
5. Collect static files
6. Restart services (zero-downtime)

## Monitoring

```bash
# View logs
journalctl -u kiri -f
journalctl -u huey -f

# Check status
systemctl status kiri gunicorn huey nginx
```
