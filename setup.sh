#!/bin/bash
# Legacy entry point — delegates to Make for consistent env file and ports.
set -euo pipefail
cd "$(dirname "$0")"
echo "🐔 Starting local stack via Make (uses env.local-backend.example)..."
exec make quick-start
