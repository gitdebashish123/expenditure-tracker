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

# Load .env file if it exists
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

# Sync dependencies (creates .venv automatically)
echo "📦 Syncing dependencies with uv..."
uv sync

# Create data directory
mkdir -p data

echo "⚡ Starting FastAPI backend on port 8000..."
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

echo "🎨 Starting Streamlit frontend on port 8501..."
uv run streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501 --theme.base dark &
FRONTEND_PID=$!

echo ""
echo "✅ SpendSense is running!"
echo ""
echo "📱 Mobile & Mac:    http://$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}'):8501"
echo "💻 Local:           http://localhost:8501"
echo "🔧 API Docs:        http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C and kill both processes
trap "echo ''; echo '⛔ Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
