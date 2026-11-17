#!/usr/bin/env bash
# Start the local static server for the Rusa browser demo.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"

echo "Serving $(pwd) on http://localhost:${PORT}/"
echo "Open that URL in Chrome/Edge (WebGPU) or any modern browser (CPU/WASM)."
echo

# Open a browser if one is available and we are on a desktop session.
if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
  ( sleep 1
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:${PORT}/" >/dev/null 2>&1 || true
    elif command -v open >/dev/null 2>&1; then open "http://localhost:${PORT}/" || true
    fi ) &
fi

exec python3 serve.py --port "${PORT}"
