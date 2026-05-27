#!/bin/bash
# =============================================================================
# SpendSense — Self-Signed Certificate Generator
# Commit 1.2: HTTPS Local Setup
#
# Generates a self-signed TLS certificate for local development only.
# One cert pair covers both services:
#   - Streamlit frontend  → https://localhost:8443
#   - FastAPI backend     → https://localhost:8444
#
# DO NOT use these certs in production.
# Production HTTPS is handled automatically by Railway / Render.
# =============================================================================

set -e  # exit immediately on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$SCRIPT_DIR/certs"
CERT_FILE="$CERTS_DIR/spendsense.crt"
KEY_FILE="$CERTS_DIR/spendsense.key"

echo ""
echo "🔐 SpendSense — Generating self-signed TLS certificate..."
echo ""

# Ensure certs directory exists
mkdir -p "$CERTS_DIR"

# Warn if certs already exist
if [ -f "$CERT_FILE" ] || [ -f "$KEY_FILE" ]; then
    echo "⚠️  Existing certificate found at:"
    echo "   $CERT_FILE"
    echo "   $KEY_FILE"
    echo ""
    read -r -p "   Overwrite? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "❌ Aborted — existing certificate kept."
        exit 0
    fi
    echo ""
fi

# Generate self-signed certificate
openssl req \
    -x509 \
    -nodes \
    -days 365 \
    -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo ""
echo "✅ Certificate generated successfully!"
echo ""
echo "   Certificate : $CERT_FILE"
echo "   Private key : $KEY_FILE"
echo "   Valid for   : 365 days"
echo "   Covers      : localhost, 127.0.0.1"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OPTIONAL — Trust this certificate in Mac Keychain"
echo "  (removes the 'Your connection is not private' browser warning)"
echo ""
echo "  Run:"
echo "    sudo security add-trusted-cert -d -r trustRoot \\"
echo "      -k /Library/Keychains/System.keychain \\"
echo "      \"$CERT_FILE\""
echo ""
echo "  This is a one-time step per machine."
echo "  You will be prompted for your Mac password."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Next step: run ./start.sh to start SpendSense with HTTPS."
echo ""
