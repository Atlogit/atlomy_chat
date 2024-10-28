#!/bin/bash

# Kill any existing Python processes running the FastAPI server
pkill -f "uvicorn app.run_server:app"

# Kill any existing Node.js processes running the Next.js server
pkill -f "node.*next"

echo "Starting FastAPI backend in debug mode..."
export LOG_LEVEL=DEBUG
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn app.run_server:app --reload &

# Wait for FastAPI server to start
echo "Waiting for FastAPI server to start..."
sleep 5

echo "Navigating to next-app directory..."
cd next-app

echo "Installing dependencies..."
npm install

echo "Starting Next.js development server..."
npm run dev &

echo "Debugging environment is set up."
echo "FastAPI backend is running at http://localhost:8000"
echo "Next.js frontend is running at http://localhost:3000"
echo "To stop the servers run: ./stop_debug.sh"

# Wait for user input to keep the script running and the servers active
read -p "Press Enter to stop the debugging session..."

# Kill the servers when the user presses Enter
pkill -f "uvicorn app.run_server:app"
pkill -f "node.*next"

echo "Debugging session ended."
