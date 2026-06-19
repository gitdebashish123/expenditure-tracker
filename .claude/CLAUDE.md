# Wallet Mantra — Project Context for Claude

> **Note**: This file is supplementary. The canonical project guidance lives in `/CLAUDE.md` at the repo root. Refer there for commands, architecture, and conventions.

## Active Frontend

The React frontend (`frontend/react/`) is the **primary UI**, served by Nginx on port 80 (Docker) or Vite dev server on port 5173. `frontend/app.py` (Streamlit) is a legacy file kept for reference and is no longer actively developed.
