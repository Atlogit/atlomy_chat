#!/bin/bash

echo "Stopping debugging session..."

# Kill the FastAPI backend process
pkill -f "python.*app/run_server.py"

# Kill the Next.js development server
pkill -f "node.*next"

echo "Debugging session stopped."
