#!/bin/bash
# Run both backend and frontend servers

# Set colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
GRAY='\033[1;30m'
NC='\033[0m' # No Color

echo -e "${CYAN}Starting Diagram Generator application...${NC}"

# Function to check if a port is in use
function is_port_in_use() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i:"$1" >/dev/null 2>&1
    return $?
  elif command -v netstat >/dev/null 2>&1; then
    netstat -tuln | grep ":$1 " >/dev/null 2>&1
    return $?
  else
    # If neither lsof nor netstat is available, assume port is free
    return 1
  fi
}

# Check if ports are already in use
BACKEND_PORT=8000
FRONTEND_PORT=5173

if is_port_in_use $BACKEND_PORT; then
  echo -e "${YELLOW}⚠️ Port $BACKEND_PORT is already in use. Backend may already be running.${NC}"
fi

if is_port_in_use $FRONTEND_PORT; then
  echo -e "${YELLOW}⚠️ Port $FRONTEND_PORT is already in use. Frontend may already be running.${NC}"
fi

# Navigate to project root
cd "$(dirname "$0")/.." || exit

# Check if Python virtual environment exists, create if not
if [ ! -d "venv" ]; then
  echo -e "${CYAN}Creating Python virtual environment...${NC}"
  python3 -m venv venv
fi

# Activate virtual environment
echo -e "${CYAN}Activating Python virtual environment...${NC}"
source venv/bin/activate

# Install backend in development mode if not already installed
if ! command -v diagram-generator-backend >/dev/null 2>&1; then
  echo -e "${CYAN}Installing backend in development mode...${NC}"
  pip install -e .
fi

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "frontend/node_modules" ]; then
  echo -e "${CYAN}Installing frontend dependencies...${NC}"
  (cd frontend && npm install)
fi

# Function to cleanup on exit
function cleanup() {
  echo -e "\n${CYAN}Stopping servers...${NC}"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo -e "${CYAN}Servers stopped.${NC}"
  exit 0
}

# Set up trap for cleanup on script termination
trap cleanup EXIT INT TERM

# Start backend server
echo -e "${GREEN}Starting backend server on http://localhost:$BACKEND_PORT...${NC}"
(cd python/diagram_generator && uvicorn backend.main:app --reload --port $BACKEND_PORT) > >(while read line; do echo -e "${GRAY}[Backend] $line${NC}"; done) 2>&1 &
BACKEND_PID=$!

# Start frontend server
echo -e "${GREEN}Starting frontend server on http://localhost:$FRONTEND_PORT...${NC}"
(cd frontend && npm run dev) > >(while read line; do echo -e "${GRAY}[Frontend] $line${NC}"; done) 2>&1 &
FRONTEND_PID=$!

# Display running information
echo -e "\n${CYAN}Application is running!${NC}"
echo -e "${CYAN}- Backend: http://localhost:$BACKEND_PORT${NC}"
echo -e "${CYAN}- Frontend: http://localhost:$FRONTEND_PORT${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop both servers.${NC}\n"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
