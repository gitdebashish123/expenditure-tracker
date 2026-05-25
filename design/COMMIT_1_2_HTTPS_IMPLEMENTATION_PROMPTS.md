# SpendSense — HTTPS Implementation Prompts

Prompts prepared for Commit 1.2 — HTTPS Local Setup.
Each prompt is self-contained and can be executed independently in sequence.
Do not skip steps — each builds on the previous.

Reference document: `design/HTTPS_SETUP_SPEC.md`

---

## Pre-flight Check (Run Before Any Prompt)

Before starting, verify the environment is ready:

```bash
nginx -v                  # expect 1.25+
openssl version           # expect OpenSSL 3.x
lsof -i :8443             # expect no output (port free)
lsof -i :8444             # expect no output (port free)
brew info nginx           # note the config path
curl http://localhost:8501  # expect Streamlit response
curl http://localhost:8000  # expect FastAPI response
```

---

## Prompt 1 — Create Certificate Generation Script

```
We are implementing Commit 1.2 (HTTPS Local Setup) for SpendSense.

Context:
- Project root: /Users/debashish/Desktop/ai-projects/expenditure-tracker
- nginx is installed via Homebrew on Mac
- We use separate HTTPS ports: 8443 (Streamlit) and 8444 (FastAPI)
- iPhone uses HTTP directly (no cert needed for mobile)
- One cert pair covers both services

Task:
Create the file nginx/generate_certs.sh with the following requirements:
1. Use openssl to generate a self-signed RSA 2048-bit certificate
2. Valid for 365 days
3. CN=localhost
4. subjectAltName must include DNS:localhost and IP:127.0.0.1
5. Output files to nginx/certs/spendsense.crt and nginx/certs/spendsense.key
6. Use -nodes flag (no passphrase — nginx reads the key at startup without prompting)
7. After generation, print a success message and remind the user to optionally
   trust the cert in Mac Keychain with the exact sudo security command
8. Make the script executable (chmod +x)

Do not generate the certs yet — only create the script.
Do not modify any other files in this step.
```

---

## Prompt 2 — Create Certs Directory Placeholder

```
We are implementing Commit 1.2 (HTTPS Local Setup) for SpendSense.

Context:
- Project root: /Users/debashish/Desktop/ai-projects/expenditure-tracker
- The nginx/certs/ directory must exist in git but cert files must be gitignored

Task:
1. Create the file nginx/certs/.gitkeep (empty file — keeps directory in git)
2. Update .gitignore to add the following entries under a new
   "# TLS certificates" comment section:
     nginx/certs/*.crt
     nginx/certs/*.key
     nginx/certs/*.pem

Do not create any cert files.
Do not modify any other files in this step.
```

---

## Prompt 3 — Create nginx Config for Streamlit Frontend

```
We are implementing Commit 1.2 (HTTPS Local Setup) for SpendSense.

Context:
- Project root: /Users/debashish/Desktop/ai-projects/expenditure-tracker
- Streamlit runs internally on http://127.0.0.1:8501
- nginx will proxy HTTPS on port 8443 → Streamlit on 8501
- Cert files are at nginx/certs/spendsense.crt and nginx/certs/spendsense.key
- Streamlit uses WebSockets — this is critical and must be handled correctly

Task:
Create the file nginx/spendsense-frontend.conf with:
1. server block listening on port 8443 with ssl
2. ssl_certificate pointing to nginx/certs/spendsense.crt (use absolute path)
3. ssl_certificate_key pointing to nginx/certs/spendsense.key (use absolute path)
4. ssl_protocols TLSv1.2 TLSv1.3 only
5. ssl_ciphers set to HIGH:!aNULL:!MD5
6. location / block proxying to http://127.0.0.1:8501
7. WebSocket support headers (these are non-negotiable for Streamlit):
     proxy_http_version 1.1
     proxy_set_header Upgrade $http_upgrade
     proxy_set_header Connection "upgrade"
     proxy_set_header Host $host
8. proxy_read_timeout 86400 (Streamlit holds long-lived connections)
9. proxy_buffering off (required for Streamlit streaming responses)
10. Add a comment block at the top explaining this config is for local dev only

Do not create the backend config in this step.
Do not modify any other files in this step.
```

---

## Prompt 4 — Create nginx Config for FastAPI Backend

```
We are implementing Commit 1.2 (HTTPS Local Setup) for SpendSense.

Context:
- Project root: /Users/debashish/Desktop/ai-projects/expenditure-tracker
- FastAPI runs internally on http://127.0.0.1:8000
- nginx will proxy HTTPS on port 8444 → FastAPI on 8000
- Same cert pair as frontend: nginx/certs/spendsense.crt and .key
- FastAPI uses standard HTTP (no WebSocket headers needed)
- FastAPI Swagger docs must remain accessible at https://localhost:8444/docs

Task:
Create the file nginx/spendsense-backend.conf with:
1. server block listening on port 8444 with ssl
2. ssl_certificate and ssl_certificate_key (same cert as frontend, absolute paths)
3. ssl_protocols TLSv1.2 TLSv1.3 only
4. ssl_ciphers set to HIGH:!aNULL:!MD5
5. location / block proxying to http://127.0.0.1:8000
6. Standard proxy headers:
     proxy_set_header Host $host
     proxy_set_header X-Real-IP $remote_addr
     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for
     proxy_set_header X-Forwarded-Proto $scheme
7. No WebSocket headers (FastAPI does not need them here)
8. Add a comment block at the top explaining this config is for local dev only

Do not modify any other files in this step.
```

---

## Prompt 5 — Update CORS in backend/main.py

```
We are implementing Commit 1.2 (HTTPS Local Setup) for SpendSense.

Context:
- Project root: /Users/debashish/Desktop/ai-projects/expenditure-tracker
- The FastAPI backend currently has allow_origins=["*"] which is too permissive
- After HTTPS setup, the Streamlit frontend will run on two origins:
    - http://localhost:8501   (direct HTTP — used by iPhone on local network)
    - https://localhost:8443  (HTTPS via nginx — used by Mac browser)

Task:
In backend/main.py, update the CORSMiddleware configuration:
1. Replace allow_origins=["*"] with an explicit list:
     allow_origins=[
         "http://localhost:8501",
         "https://localhost:8443",
     ]
2. Keep allow_methods=["*"] and allow_headers=["*"] unchanged for now
   (these will be tightened in Sprint 5 — API Hardening)
3. Add a comment explaining the two origins and why both are needed

Do not modify any other files in this step.
```

---

## Prompt 6 — Update start.sh

```
We are implementing Commit 1.2 (HTTPS Local Setup) for SpendSense.

Context:
- Project root: /Users/debashish/Desktop/ai-projects/expenditure-tracker
- nginx configs are at nginx/spendsense-frontend.conf and nginx/spendsense-backend.conf
- Cert files are at nginx/certs/spendsense.crt and nginx/certs/spendsense.key
- Streamlit HTTPS: port 8443, HTTP: port 8501
- FastAPI HTTPS: port 8444, HTTP: port 8000
- iPhone uses HTTP directly on 8501/8000 — nginx is not involved for mobile

Task:
Update start.sh with the following additions in this order:
1. After the .env loading block, add a cert existence check:
   - If nginx/certs/spendsense.crt does not exist, print a warning:
     "⚠️  No TLS cert found. Run: bash nginx/generate_certs.sh"
   - Set a variable HTTPS_ENABLED=false
   - If cert exists, set HTTPS_ENABLED=true

2. After uv sync and before starting app services, add an nginx block:
   - If HTTPS_ENABLED=true:
     - Check if nginx is already running (pgrep nginx)
     - If not running: start nginx with both configs
     - If running: reload nginx (nginx -s reload)
     - Print "🔒 nginx started — HTTPS enabled"
   - If HTTPS_ENABLED=false:
     - Print "⚠️  Running without HTTPS (cert not found)"

3. Update the startup banner at the end to show both HTTP and HTTPS URLs:

   ✅ SpendSense is running!

   🔒 HTTPS (Mac browser):
      Frontend:  https://localhost:8443
      API Docs:  https://localhost:8444/docs

   📱 HTTP (iPhone / local network):
      Frontend:  http://<local-ip>:8501
      API:       http://<local-ip>:8000

   ⚠️  First time HTTPS setup? Run: bash nginx/generate_certs.sh

4. Update the trap (Ctrl+C handler) at the end to also stop nginx:
   nginx -s stop 2>/dev/null

Do not modify any other files in this step.
```

---

## Prompt 7 — Update README.md with HTTPS Section

```
We are implementing Commit 1.2 (HTTPS Local Setup) for SpendSense.

Context:
- Project root: /Users/debashish/Desktop/ai-projects/expenditure-tracker
- Local HTTPS uses self-signed cert on ports 8443 (frontend) and 8444 (backend)
- iPhone uses HTTP directly in local dev
- Production HTTPS is automatic on Railway and Render (no configuration needed)

Task:
Add a new "## HTTPS Setup" section to README.md after the existing "## Setup (Mac)"
section. The new section must cover:

1. Local Development subsection:
   - Prerequisites: nginx (brew install nginx), openssl (pre-installed on Mac)
   - One-time setup steps:
       a. Generate cert: bash nginx/generate_certs.sh
       b. Optional: trust cert in Mac Keychain (include the exact sudo security command)
       c. Start app: ./start.sh (nginx starts automatically)
   - Access URLs:
       Frontend: https://localhost:8443
       API Docs: https://localhost:8444/docs
   - Note about browser warning on first visit (self-signed cert)
   - Note about cert renewal (re-run generate_certs.sh after 365 days)

2. iPhone / Mobile Access subsection:
   - Use HTTP directly on local network (no HTTPS needed for dev)
   - Find Mac IP: ipconfig getifaddr en0
   - Access: http://192.168.x.x:8501

3. Production HTTPS — Railway subsection:
   - HTTPS is fully automatic — zero configuration required
   - Platform provisions and renews the certificate
   - No nginx, no certbot, no configuration files needed
   - Step: push to GitHub → Railway auto-deploys → HTTPS active immediately
   - Verifying: browser padlock, or curl https://your-app.railway.app

4. Production HTTPS — Render subsection:
   - Same as Railway — automatic HTTPS on every deploy
   - Custom domain supported on free tier

5. Troubleshooting subsection with these specific entries:
   - "Streamlit blank screen after HTTPS" → WebSocket headers missing, check nginx config
   - "Browser shows security warning" → self-signed cert, click Advanced → Proceed
                                         or trust in Keychain
   - "iPhone connection refused" → expected for HTTPS, use HTTP on local network
   - "Port 8443/8444 already in use" → lsof -i :8443, kill the process

Keep the writing style consistent with the existing README.
Do not modify any other section of README.md.
Do not modify any other files in this step.
```

---

## Prompt 8 — Final Verification

```
We have completed Commit 1.2 (HTTPS Local Setup) for SpendSense.

Context:
- Project root: /Users/debashish/Desktop/ai-projects/expenditure-tracker

Task:
Perform a final audit across all files changed in this commit and verify:

1. nginx/generate_certs.sh
   - Is executable (chmod +x applied)
   - Contains subjectAltName with DNS:localhost and IP:127.0.0.1
   - Outputs to nginx/certs/spendsense.crt and .key
   - Prints Keychain trust command after generation

2. nginx/certs/.gitkeep
   - File exists (empty)

3. .gitignore
   - Contains nginx/certs/*.crt
   - Contains nginx/certs/*.key
   - Contains nginx/certs/*.pem

4. nginx/spendsense-frontend.conf
   - Listens on 8443 with ssl
   - Proxies to 127.0.0.1:8501
   - Contains all three WebSocket headers (Upgrade, Connection, proxy_http_version)
   - proxy_read_timeout 86400 present
   - proxy_buffering off present

5. nginx/spendsense-backend.conf
   - Listens on 8444 with ssl
   - Proxies to 127.0.0.1:8000
   - No WebSocket headers (not needed)
   - X-Forwarded-Proto header present

6. backend/main.py
   - allow_origins no longer contains "*"
   - Contains exactly: http://localhost:8501 and https://localhost:8443

7. start.sh
   - Checks for cert existence before starting
   - Starts or reloads nginx if cert exists
   - Updated banner shows both HTTPS and HTTP URLs
   - Ctrl+C trap includes nginx -s stop

8. README.md
   - HTTPS Setup section exists after Setup (Mac) section
   - Contains local dev, iPhone, Railway, Render, and Troubleshooting subsections

Report any gaps found. Fix any issues before marking this commit complete.
```

---

## Post-Implementation Manual Test

After all prompts are executed, run this manual test sequence:

```bash
# Step 1 — Generate cert
bash nginx/generate_certs.sh

# Step 2 — Start everything
./start.sh

# Step 3 — Test HTTPS frontend
curl -k https://localhost:8443
# expect: HTML response from Streamlit

# Step 4 — Test HTTPS backend
curl -k https://localhost:8444/health
# expect: {"status": "ok"} or similar

# Step 5 — Test HTTP still works (for iPhone)
curl http://localhost:8501
# expect: HTML response from Streamlit

# Step 6 — Test API docs accessible
open https://localhost:8444/docs
# expect: Swagger UI loads in browser

# Step 7 — Test Streamlit in browser
open https://localhost:8443
# expect: SpendSense dashboard loads, accept cert warning if not trusted

# Step 8 — Test Ctrl+C cleanup
# Press Ctrl+C in start.sh terminal
# expect: "Stopping..." message, nginx stops cleanly
pgrep nginx
# expect: no output (nginx stopped)
```

---

*Last updated: May 2026*
*Owner: Debashish*
*Status: Prompts ready — awaiting execution approval*
