#!/bin/bash
# SpendSense - Start Script (uv)
# Run from the expenditure-tracker/ directory

echo "🚀 Starting SpendSense Expenditure Tracker..."
echo ""

# Check for uv
if ! command -v uv &>/dev/null; then
    echo "❌ ERROR: uv not found. Install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# ── Load .env ────────────────────────────────────────────────────────────────
if [ -f ".env" ]; then
    echo "📋 Loading environment from .env..."
    set -a
    source .env
    set +a
else
    echo "⚠️  No .env file found. Copy .env.example to .env and fill in your values."
fi

# Check for API key (may have come from .env or pre-existing shell env)
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY not set."
    echo "   Add it to your .env file: ANTHROPIC_API_KEY=sk-ant-..."
    exit 1
fi

# ── TLS Certificate Check ────────────────────────────────────────────────────
CERT_FILE="nginx/certs/spendsense.crt"

if [ ! -f "$CERT_FILE" ]; then
    echo "⚠️  No TLS cert found. Run: bash nginx/generate_certs.sh"
    HTTPS_ENABLED=false
else
    HTTPS_ENABLED=true
fi

# ── Sync dependencies ────────────────────────────────────────────────────────
echo "📦 Syncing dependencies with uv..."
uv sync

# Create data directory
mkdir -p data

# ── nginx HTTPS Setup ────────────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_CONF="$PROJECT_DIR/nginx/spendsense-frontend.conf"
BACKEND_CONF="$PROJECT_DIR/nginx/spendsense-backend.conf"

if [ "$HTTPS_ENABLED" = true ]; then
    if pgrep -x nginx &>/dev/null; then
        # nginx already running — reload to pick up any config changes
        echo "🔄 nginx already running — reloading config..."
        nginx -s reload
    else
        # Start nginx with both service configs
        echo "🔒 Starting nginx for HTTPS..."
        nginx -c "$FRONTEND_CONF"
        nginx -c "$BACKEND_CONF"
    fi
    echo "🔒 nginx started — HTTPS enabled"
else
    echo "⚠️  Running without HTTPS (cert not found)"
fi

# ── Start Application Services ───────────────────────────────────────────────
echo ""
echo "⚡ Starting FastAPI backend on port 8000..."
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

echo "🎨 Starting Streamlit frontend on port 8501..."
uv run streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501 --theme.base dark &
FRONTEND_PID=$!

# ── Startup Banner ───────────────────────────────────────────────────────────
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "192.168.x.x")

echo ""
echo "✅ SpendSense is running!"
echo ""

if [ "$HTTPS_ENABLED" = true ]; then
    echo "🔒 HTTPS (Mac browser):"
    echo "   Frontend:  https://localhost:8443"
    echo "   API Docs:  https://localhost:8444/docs"
    echo ""
fi

echo "📱 HTTP (iPhone / local network):"
echo "   Frontend:  http://$LOCAL_IP:8501"
echo "   API:       http://$LOCAL_IP:8000"
echo ""

if [ "$HTTPS_ENABLED" = false ]; then
    echo "⚠️  First time HTTPS setup? Run: bash nginx/generate_certs.sh"
    echo ""
fi

echo "Press Ctrl+C to stop all services"

# ── Shutdown Handler ─────────────────────────────────────────────────────────
# Stops nginx, backend, and frontend cleanly on Ctrl+C
trap "
    echo ''
    echo '⛔ Stopping SpendSense...'
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    nginx -s stop 2>/dev/null && echo '🔒 nginx stopped' || true
    echo '👋 Done'
    exit
" INT

wait
