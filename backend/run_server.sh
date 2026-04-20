#!/bin/bash
# Simple script to run the backend API server

echo "Starting Lambda SAT Middleware API Server..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if Kissat is available (warning only)
if ! command -v kissat &> /dev/null; then
    echo "Warning: Kissat is not installed. Some features will be unavailable."
    echo "Install from: https://github.com/arminbiere/kissat"
    echo ""
fi

# Check if drat-trim is available (warning only)
if ! command -v drat-trim &> /dev/null; then
    echo "Warning: drat-trim is not installed. Proof checking will be unavailable."
    echo "Install from: https://github.com/marijnheule/drat-trim"
    echo ""
fi

# Run the server
python3 -m backend.api_server
