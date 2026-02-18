#!/bin/bash
# Simple local dev server for testing
cd "$(dirname "$0")"
echo "Serving at http://localhost:8000"
python3 -m http.server 8000
