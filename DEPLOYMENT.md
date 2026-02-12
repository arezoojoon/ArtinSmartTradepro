# Artin Smart Trade — Production Deployment Guide

This document describes how to deploy the platform from scratch on a clean Ubuntu 22.04+ server with Docker.

## 1. Prerequisites

- Ubuntu 22.04 LTS (or compatible) with at least 4 CPU / 8 GB RAM
- Docker Engine 24+ and Docker Compose plugin 2.20+
- DNS records pointing `trade.artinsmartagent.com` (and `api.` if desired) to the server IP
- TLS certificates (managed by Let’s Encrypt/Certbot or uploaded to `deploy/nginx/certs`)
- Optional: Cloudflare in front of the domain (set SSL mode to **Full (strict)** for best results)

## 2. Repository Setup

```bash
cd /app
rm -rf /app/ArtinSmartTrade && git clone git@github.com:arezoojoon/ArtinSmartTradepro.git ArtinSmartTrade
cd ArtinSmartTrade
```

> **Important:** ensure the working tree is clean before building images.

## 3. Populate Environment Variables

Copy and edit the production template:

```bash
cp deploy/.env.prod.example .env.prod
```

Fill **all** placeholders in `.env.prod`. Minimum required values:

| Section | Variables | Notes |
| --- | --- | --- |
| Core App | `ENVIRONMENT`, `APP_URL`, `FRONTEND_URL`, `NEXT_PUBLIC_API_URL` | Use the public HTTPS URLs |
| Security | `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, `STRIPE_WEBHOOK_SECRET` | Must be long random strings |
| Database | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Docker Compose injects these into Postgres |
| MinIO / S3 | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `S3_*` | Needed even if features not yet used |
| AI | `GEMINI_API_KEY_1…3` | At least one key required |
| WhatsApp / WAHA | `WHATSAPP_TOKEN`, `WAHA_API_URL`, etc. | Leave blank only if feature disabled |

**Never** deploy with empty values; Compose will treat them as blank strings and the API will fail to start.

## 4. Build & Start the Stack

From the repo root:

```bash
docker compose -f deploy/docker-compose.prod.yml pull  # optional, if using registry
sudo docker compose -f deploy/docker-compose.prod.yml up -d --build
```

Services started:

- `artin_db` (Postgres 16)
- `artin_redis`
- `artin_minio`
- `artin_api` (FastAPI + Gunicorn) — runs `scripts/init_db.py` plus finance/execution/operations initializers automatically
- `artin_frontend` (Next.js production build)
- `artin_nginx` (reverse proxy serving frontend + `/api`)

## 5. Post-Deploy Verification

1. Check container health:
   ```bash
   docker compose -f deploy/docker-compose.prod.yml ps
   docker compose -f deploy/docker-compose.prod.yml logs -f api
   ```
2. API smoke test from the server:
   ```bash
   curl -f http://localhost:8000/health
   python tests/verify_deployment.py
   ```
3. Frontend health:
   ```bash
   curl -I http://localhost:3000
   ```
4. External check: browse to `https://trade.artinsmartagent.com` and ensure no redirect loop.

## 6. Zero-Downtime Redeploy

```bash
sudo docker compose -f deploy/docker-compose.prod.yml pull
sudo docker compose -f deploy/docker-compose.prod.yml up -d --build
sudo docker image prune -f
```

## 7. Troubleshooting

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `WARN ... variable is not set. Defaulting to blank string.` | `.env.prod` missing values | Populate all required vars and rerun `docker compose up -d --build` |
| `ERR_TOO_MANY_REDIRECTS` in browser | Cloudflare Flexible SSL or incorrect origin redirect logic | Use Cloudflare **Full (strict)** _or_ ensure Nginx only redirects when real scheme is HTTP (already handled in `deploy/nginx/conf.d/app.conf`) |
| Frontend shows maintenance page | Frontend container disabled or not proxied | Ensure `frontend` service is running and Nginx proxies `/` to it |
| Pydantic warning "Field model_used conflict with protected namespace" | Older code without ConfigDict override | Already resolved; if you see it, ensure latest backend is deployed |
| `DB not ready` in entrypoint | Postgres failed health check | Inspect `docker compose logs db`, fix credentials/storage |

## 8. Backup & Maintenance

- Back up PostgreSQL volume `pg_data` and MinIO bucket periodically.
- Rotate `SECRET_KEY`, `MINIO_ROOT_PASSWORD`, and access keys every 90 days.
- Monitor `artin_api` logs for `wait_for_db` retries or AI job failures.

## 9. Clean Teardown

```bash
sudo docker compose -f deploy/docker-compose.prod.yml down -v
sudo rm -rf postgres_data redis_data minio_data app_data  # only if you intend to wipe data
```

---
Need help? Check `tests/verify_deployment.py` for reference API flows or ping the engineering team.
