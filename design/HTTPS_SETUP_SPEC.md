# SpendSense — HTTPS Setup Specification

This document captures the full implementation plan for Commit 1.2 — HTTPS Local Setup.
All decisions are locked based on answers provided. No implementation proceeds without
this document being reviewed first.

---

## Decisions Locked

| Question | Decision |
|---|---|
| nginx installed? | ✅ Yes — already on Mac via Homebrew |
| iPhone HTTPS locally? | Both — HTTPS on desktop, HTTP acceptable on local WiFi for mobile during dev |
| Production HTTPS focus | Railway / Render (automatic, recommended) |
| Service architecture | Separate ports with independent HTTPS per service |

---

## Target Architecture

### Local Development

```
Browser (Mac)
    ↓
https://localhost:8443  (nginx → Streamlit on 8501)
https://localhost:8444  (nginx → FastAPI on 8000)

iPhone (same WiFi, development only)
    ↓
http://192.168.x.x:8501  (Streamlit direct, no TLS)
http://192.168.x.x:8000  (FastAPI direct, no TLS)
```

### Why Separate Ports

- Simpler nginx config — each service is fully independent
- No path-based routing complexity (`/api` prefix on every FastAPI call)
- FastAPI Swagger docs continue to work without path prefix changes
- Streamlit WebSocket handling is isolated — no risk of nginx path conflicts
- Each service can be restarted independently without affecting the other

### Port Map

| Service | Internal Port | HTTPS Port | HTTP (iPhone dev) |
|---|---|---|---|
| Streamlit frontend | 8501 | 8443 | 8501 |
| FastAPI backend | 8000 | 8444 | 8000 |
| nginx | — | 8443, 8444 | — |

> Ports 8443 and 8444 are used instead of 443 to avoid requiring sudo on Mac.
> Standard HTTPS port 443 requires root privileges to bind. 8443 is the conventional
> alternative for local dev HTTPS.

---

## Files to Create / Modify

```
expenditure-tracker/
├── nginx/
│   ├── spendsense-frontend.conf    ← nginx config for Streamlit (port 8443)
│   ├── spendsense-backend.conf     ← nginx config for FastAPI (port 8444)
│   ├── certs/
│   │   ├── .gitkeep                ← keeps folder in git, certs are gitignored
│   │   ├── spendsense.crt          ← gitignored, generated locally
│   │   └── spendsense.key          ← gitignored, NEVER committed
│   └── generate_certs.sh           ← one-command cert generation script
├── .gitignore                      ← add nginx/certs/*.crt, nginx/certs/*.key
├── start.sh                        ← add nginx startup + HTTPS port info
└── README.md                       ← add HTTPS section (local + production)
```

---

## Step 1 — Self-Signed Certificate

### Single Certificate Covering Both Services

One cert pair covers both ports — same `localhost` domain, no need for separate certs.

### generate_certs.sh

Script placed at `nginx/generate_certs.sh`. Run once per machine:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/spendsense.key \
  -out nginx/certs/spendsense.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

### Key Parameters Explained

| Parameter | Value | Why |
|---|---|---|
| `-x509` | — | Self-signed (no CA) |
| `-nodes` | — | No passphrase on key (nginx needs to read it at startup without prompting) |
| `-days 365` | — | Valid for 1 year |
| `-newkey rsa:2048` | — | 2048-bit RSA key — secure and fast |
| `-subj "/CN=localhost"` | — | Common name matches the hostname |
| `subjectAltName` | `DNS:localhost,IP:127.0.0.1` | Modern browsers require this — CN alone is no longer sufficient |

### Why No Local IP in the Cert

The Mac's local IP (`192.168.x.x`) is **not included** in `subjectAltName` — this is
intentional. iPhone access in local dev uses HTTP directly to the service ports (8501,
8000), bypassing nginx entirely. iOS would reject a self-signed cert anyway without
a manual profile installation, so HTTP is the pragmatic choice for mobile dev.

### Mac Keychain Trust (Optional but Recommended)

To remove the "Your connection is not private" browser warning permanently on Mac:

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  nginx/certs/spendsense.crt
```

This is a one-time step per machine. Not scripted into `generate_certs.sh` because
it requires sudo and a human decision to trust the cert.

---

## Step 2 — nginx Configuration

### spendsense-frontend.conf (Streamlit on 8443)

Key directives:
- Listen on `8443` with SSL
- Point to `nginx/certs/spendsense.crt` and `.key`
- Proxy to `http://127.0.0.1:8501`
- WebSocket upgrade headers — **critical for Streamlit**
- `proxy_read_timeout 86400` — Streamlit holds long-lived connections

```
WebSocket headers required:
  proxy_http_version 1.1
  proxy_set_header Upgrade $http_upgrade
  proxy_set_header Connection "upgrade"
```

Without the WebSocket headers Streamlit loads the initial page but then
disconnects — the UI appears frozen and widgets stop responding.

### spendsense-backend.conf (FastAPI on 8444)

Key directives:
- Listen on `8444` with SSL
- Same cert pair as frontend
- Proxy to `http://127.0.0.1:8000`
- No WebSocket headers needed (FastAPI uses standard HTTP)
- CORS note: `allow_origins` in `main.py` must include `https://localhost:8443`
  once HTTPS is active

### What Changes in main.py CORS Config

Currently:
```python
allow_origins=["*"]   # too permissive
```

After HTTPS setup:
```python
allow_origins=[
    "http://localhost:8501",      # direct HTTP (dev, iPhone)
    "https://localhost:8443",     # HTTPS via nginx (Mac browser)
]
```

This is a code change that must happen alongside the nginx config — documented here
so it is not forgotten.

---

## Step 3 — start.sh Updates

### What Changes

- Check if nginx is running before starting app services
- Load nginx config (if not already loaded)
- Print both HTTP and HTTPS URLs in the startup banner

### Updated Startup Banner

```
✅ SpendSense is running!

🔒 HTTPS (Mac browser):
   Frontend:  https://localhost:8443
   API docs:  https://localhost:8444/docs

📱 HTTP (iPhone / local network):
   Frontend:  http://192.168.x.x:8501
   API:       http://192.168.x.x:8000

⚠️  First time? Run: bash nginx/generate_certs.sh
```

### nginx Startup Check Logic

```
if nginx config not loaded:
    nginx -c /path/to/spendsense-frontend.conf
    nginx -c /path/to/spendsense-backend.conf
else:
    nginx -s reload
fi
```

---

## Step 4 — README Documentation

### New Section: "HTTPS Setup"

Structure:

```
## HTTPS Setup

### Local Development (Mac)

Prerequisites
  - nginx installed (brew install nginx)
  - openssl available (pre-installed on Mac)

Setup (one-time per machine)
  1. Generate self-signed cert
  2. (Optional) Trust cert in Mac Keychain
  3. Load nginx configs
  4. Access via https://localhost:8443

iPhone Access (local dev)
  - Use HTTP directly: http://192.168.x.x:8501
  - No cert setup needed on iPhone

### Production HTTPS — Railway / Render

Railway (recommended)
  - HTTPS is automatic on every deploy
  - No nginx, no certbot, no configuration
  - Certificate provisioned and renewed by platform

Render
  - Same as Railway — automatic HTTPS
  - Custom domain support available on free tier

Verifying HTTPS
  - Browser padlock check
  - curl --insecure command for local
  - curl command for production

### Troubleshooting

Common issues:
  - Streamlit blank screen → WebSocket headers missing in nginx config
  - Browser warning → cert not trusted in Keychain
  - iPhone refused → expected, use HTTP on local network
  - Port 443 permission denied → use 8443 instead (no sudo needed)
```

---

## .gitignore Additions

```gitignore
# TLS certificates — never commit private keys
nginx/certs/*.crt
nginx/certs/*.key
nginx/certs/*.pem
```

The `nginx/certs/` directory itself is committed (via `.gitkeep`) so the
folder structure exists when someone clones the repo. Only the generated
cert files are excluded.

---

## Pre-Implementation Checklist

Before writing any code, confirm:

- [ ] nginx version: `nginx -v` (expect 1.25+)
- [ ] openssl available: `openssl version`
- [ ] Ports 8443 and 8444 are free: `lsof -i :8443` and `lsof -i :8444`
- [ ] Homebrew nginx config location confirmed: `brew info nginx`
- [ ] Frontend currently accessible at `http://localhost:8501` ✅
- [ ] Backend currently accessible at `http://localhost:8000` ✅

---

## Rollback Plan

If nginx setup causes issues:

1. Stop nginx: `nginx -s stop`
2. App continues to work on original HTTP ports (8501, 8000) — unchanged
3. Remove nginx configs from load path
4. No database or application code is affected by this change

nginx is purely additive — it sits alongside the existing setup. The HTTP ports
remain open throughout, so there is zero risk of breaking the running app.

---

## Implementation Order

1. `nginx/generate_certs.sh` — cert generation script
2. `nginx/certs/.gitkeep` — folder placeholder
3. `.gitignore` — add cert exclusions
4. `nginx/spendsense-frontend.conf` — Streamlit proxy config
5. `nginx/spendsense-backend.conf` — FastAPI proxy config
6. `backend/main.py` — update CORS `allow_origins`
7. `start.sh` — add nginx startup + updated banner
8. `README.md` — add HTTPS section

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Spec complete — awaiting implementation approval*
