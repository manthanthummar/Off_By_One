# FarmSense Deployment Notes

Running log of deployment activities, environment configuration, and verification steps.

## Step 1: Project & Architecture Inspection
- **Backend Framework:** FastAPI (Python 3.11), Uvicorn ASGI server.
- **Backend Port:** `8000`.
- **Database:** SQLite fallback (`sqlite:///./farmsense.db`) / PostgreSQL with SQLAlchemy 2.0 and Alembic migrations.
- **Frontend Framework:** Next.js 14 App Router (React 18, TypeScript, Tailwind CSS, Lucide icons, Recharts).
- **Frontend Port:** `3000`.
- **Package Managers:** pip (Python), npm (Node.js).
- **Network Invariants:**
  - Client browser requests must reach the backend without CORS or mixed-content (HTTP vs HTTPS) blocks.
  - Servers must listen on `0.0.0.0` to permit external network traffic.

## Step 2: Sharing & Network Configuration
- Configured FastAPI CORS (`app/main.py`) with `allow_origin_regex=r"https?://.*"` to dynamically accept all incoming origins (local network IPs, tunnels, production domains) with credentials.
- Configured Next.js reverse-proxy rewrite (`frontend/next.config.js` -> `/api-proxy/:path*` to `http://127.0.0.1:8000/:path*`).
- Updated `frontend/src/lib/api.ts` to default client browser requests to `/api-proxy`, eliminating mixed-content errors and allowing single-URL full-stack access.
- Updated FastAPI Uvicorn binding to `0.0.0.0:8000`.
- Updated Next.js binding to `0.0.0.0:3000`.
- Verified local network IP: `10.192.187.131`.

## Step 3: Deployment & Public Tunneling
- Downloaded official Cloudflare Tunnel (`cloudflared`) binary.
- Configured HTTP/2 TCP transport protocol (`--protocol http2`) for long-running connection stability.
- **Live Public HTTPS URL:** `https://jazz-cardiac-gmbh-owned.trycloudflare.com`
- **Local Network URL:** `http://10.192.187.131:3000`
- **GitHub Repository:** `https://github.com/jeelkakadiya10-ship-it/temp-off-by-one`

## Step 4: Verification Matrix
All routes and proxied backend APIs were tested end-to-end via automated HTTP probe against the live tunnel URL:
- `GET /` -> HTTP 200 OK (FarmSense home rendered)
- `GET /api-proxy/health` -> HTTP 200 OK (`{"status":"ok","llm":false,"mqtt":false}`)
- `GET /api-proxy/farms` -> HTTP 200 OK (Farms list loaded)
- `GET /dashboard` -> HTTP 200 OK (Sensors & Weather charts)
- `GET /risks` -> HTTP 200 OK (Risk cards & reasoning drawer)
- `GET /plans` -> HTTP 200 OK (Action plans timeline)
- `GET /tasks` -> HTTP 200 OK (Kanban task board)
- `GET /escalations` -> HTTP 200 OK (Agronomist portal)
- `GET /trace` -> HTTP 200 OK (Agent execution telemetry)
- `GET /alerts` -> HTTP 200 OK (Farmer SMS feed)