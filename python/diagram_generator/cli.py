#!/usr/bin/env python
"""
Command-line interface for the Diagram Generator application.
This module provides a unified way to start both the backend and frontend servers.
"""

import os
import sys
import subprocess
import signal
import time
import argparse
import webbrowser
from pathlib import Path
import threading
import atexit

# Default ports
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

# ANSI colors for terminal output
CYAN = '\033[0;36m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
GRAY = '\033[1;30m'
NC = '\033[0m'  # No Color

# Store process handles for cleanup
processes = []


def print_color(color, message):
    """Print colored message to terminal."""
    print(f"{color}{message}{NC}")


def find_project_root():
    """Find the project root directory."""
    # Get the directory of the current script
    current_dir = Path(__file__).resolve().parent
    
    # First try: Check if we're in development mode
    # Navigate up to find the project root (where setup.py is)
    root_dir = current_dir
    while True:
        # Check if we found the project root
        if (root_dir / 'setup.py').exists():
            return root_dir
        
        # Check if we're in the python/diagram_generator directory structure
        if root_dir.name == 'diagram_generator' and (root_dir.parent.name == 'python' and 
                                                    (root_dir.parent.parent / 'setup.py').exists()):
            return root_dir.parent.parent
        
        # Move up one directory
        parent = root_dir.parent
        if parent == root_dir:  # Reached filesystem root
            break
        root_dir = parent
    
    # Second try: Use the current working directory
    cwd = Path.cwd()
    if (cwd / 'setup.py').exists():
        return cwd
    
    # Third try: Check if frontend directory exists in current directory
    if (cwd / 'frontend').exists() and (cwd / 'frontend' / 'package.json').exists():
        return cwd
    
    # Last resort: Use the current directory and hope for the best
    print(f"Warning: Could not find project root directory. Using current directory: {cwd}")
    return cwd


def is_port_in_use(port):
    """Check if a port is already in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def cleanup():
    """Terminate all child processes on exit."""
    print_color(CYAN, "\nStopping servers...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            try:
                if sys.platform == 'win32':
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
            except Exception:
                pass
    print_color(CYAN, "Servers stopped.")


def open_browser(url, delay=2):
    """Open a browser tab after a delay."""
    def _open_browser():
        time.sleep(delay)
        webbrowser.open(url)
    
    thread = threading.Thread(target=_open_browser)
    thread.daemon = True
    thread.start()


def start_backend(project_root, port=BACKEND_PORT):
    """Start the backend server."""
    if is_port_in_use(port):
        print_color(YELLOW, f"⚠️ Port {port} is already in use. Backend may already be running.")
        return None
    
    print_color(GREEN, f"Starting backend server on http://localhost:{port}...")
    
    # Determine the command to run
    cmd = [sys.executable, "-m", "uvicorn", "diagram_generator.backend.main:app", "--reload", f"--port={port}"]
    
    # Start the backend process
    process = subprocess.Popen(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    processes.append(process)
    return process


def start_frontend(project_root, port=FRONTEND_PORT):
    """Start the frontend development server."""
    if is_port_in_use(port):
        print_color(YELLOW, f"⚠️ Port {port} is already in use. Frontend may already be running.")
        return None
    
    frontend_dir = project_root / 'frontend'
    
    # Check if frontend directory exists
    if not frontend_dir.exists():
        print_color(YELLOW, f"⚠️ Frontend directory not found at {frontend_dir}")
        return None
    
    # Check if node_modules exists, install if not
    if not (frontend_dir / 'node_modules').exists():
        print_color(CYAN, "Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
    
    print_color(GREEN, f"Starting frontend server on http://localhost:{port}...")
    
    # Start the frontend process
    try:
        # Check if npm is available
        npm_path = "npm"
        if sys.platform == 'win32':
            # On Windows, try to find npm in common locations
            possible_paths = [
                "npm.cmd",  # Check if npm.cmd is in PATH
                r"C:\Program Files\nodejs\npm.cmd",
                r"C:\Program Files (x86)\nodejs\npm.cmd",
            ]
            
            for path in possible_paths:
                try:
                    subprocess.run([path, "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    npm_path = path
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
        
        print_color(GREEN, f"Using npm: {npm_path}")
        
        # Run npm command
        process = subprocess.Popen(
            [npm_path, "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            shell=True if sys.platform == 'win32' else False
        )
    except Exception as e:
        print_color(YELLOW, f"Error starting frontend: {str(e)}")
        print_color(YELLOW, "Make sure Node.js and npm are installed and in your PATH")
        return None
    
    processes.append(process)
    return process


def monitor_process(process, prefix):
    """Monitor a process and print its output with a prefix."""
    if process is None:
        return
    
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"{GRAY}[{prefix}] {line.rstrip()}{NC}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Diagram Generator CLI")
    parser.add_argument('--backend-only', action='store_true', help='Start only the backend server')
    parser.add_argument('--frontend-only', action='store_true', help='Start only the frontend server')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    parser.add_argument('--backend-port', type=int, default=BACKEND_PORT, help=f'Backend port (default: {BACKEND_PORT})')
    parser.add_argument('--frontend-port', type=int, default=FRONTEND_PORT, help=f'Frontend port (default: {FRONTEND_PORT})')
    
    args = parser.parse_args()
    
    # Register cleanup handler
    atexit.register(cleanup)
    
    try:
        # Find project root
        project_root = find_project_root()
        
        print_color(CYAN, "Starting Diagram Generator application...")
        
        # Start backend if requested
        backend_process = None
        if not args.frontend_only:
            backend_process = start_backend(project_root, args.backend_port)
        
        # Start frontend if requested
        frontend_process = None
        if not args.backend_only:
            frontend_process = start_frontend(project_root, args.frontend_port)
        
        # Open browser if requested
        if not args.no_browser and frontend_process is not None:
            open_browser(f"http://localhost:{args.frontend_port}")
        
        # Display running information
        print_color(CYAN, "\nApplication is running!")
        if backend_process is not None:
            print_color(CYAN, f"- Backend: http://localhost:{args.backend_port}")
        if frontend_process is not None:
            print_color(CYAN, f"- Frontend: http://localhost:{args.frontend_port}")
        print_color(YELLOW, "\nPress Ctrl+C to stop the servers.\n")
        
        # Monitor processes
        backend_thread = None
        frontend_thread = None
        
        if backend_process is not None:
            backend_thread = threading.Thread(
                target=monitor_process,
                args=(backend_process, "Backend")
            )
            backend_thread.daemon = True
            backend_thread.start()
        
        if frontend_process is not None:
            frontend_thread = threading.Thread(
                target=monitor_process,
                args=(frontend_process, "Frontend")
            )
            frontend_thread.daemon = True
            frontend_thread.start()
        
        # Wait for processes to complete
        if backend_thread:
            backend_thread.join()
        if frontend_thread:
            frontend_thread.join()
        
    except KeyboardInterrupt:
        print_color(CYAN, "\nReceived keyboard interrupt. Shutting down...")
    except Exception as e:
        print_color(YELLOW, f"\nError: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
