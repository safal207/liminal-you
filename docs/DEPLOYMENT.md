Deployment Guide (v0.2)

Overview
- Backend: FastAPI on Uvicorn/Gunicorn
- Frontend: React (Vite) static assets
- Reverse proxy: Nginx (TLS termination, static, proxy /api)
- Optional: LiminalDB (WebSocket at ws://liminaldb:8001)
- Monitoring: Prometheus + Grafana (optional)

Docker Compose (production)
- Use docker-compose.prod.yml:

  - Service `backend`: runs Gunicorn/Uvicorn
  - Service `frontend`: builds static and serves via Nginx
  - Service `nginx`: reverse proxies to backend and serves static
  - Service `liminaldb` (optional): external or internal

Nginx
- Terminates TLS, proxies `/api` to backend, serves `/` from built frontend
- Add gzip, caching headers for static assets

Environment
- Create `backend/.env` from `.env.example`
- Key vars: LIMINALDB_ENABLED, LIMINALDB_URL, STORAGE_BACKEND, JWT_SECRET, CORS

CI/CD (GitHub Actions)
- Backend: build & push Docker image, run pytest
- Frontend: install, build, run vitest, publish artifacts
- Optionally deploy to server via SSH or to a registry with auto-pull

Monitoring (optional)
- Expose backend metrics via a `/metrics` endpoint (Starlette Exporter) and scrape by Prometheus
- Dashboards in Grafana for latency, errors, throughput

Quick Steps
1) Build images: `docker compose -f docker-compose.prod.yml build`
2) Configure DNS and TLS certs (letsencrypt/Certbot)
3) Start: `docker compose -f docker-compose.prod.yml up -d`
4) Verify:
   - Frontend: https://your-domain/
   - Backend: https://your-domain/api/docs
   - LiminalDB: ws://liminaldb:8001 (if used)

