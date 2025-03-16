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
from typing import List, Optional

# Process type for type hints
ProcessType = Optional[subprocess.Popen[str]]

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
processes: List[ProcessType] = []

def print_color(color: str, message: str) -> None:
    """
    Print a colored message to terminal.
    
    Args:
        color: ANSI color code string
        message: Text to print
    """
    print(f"{color}{message}{NC}")

def find_project_root() -> Path:
    """
    Find the project root directory by looking for setup.py.
    
    Returns:
        Path: Project root directory path
    """
    current_dir = Path(__file__).resolve().parent
    
    root_dir = current_dir
    while True:
        if (root_dir / 'setup.py').exists():
            return root_dir
        
        if root_dir.name == 'diagram_generator' and (root_dir.parent.name == 'python' and 
                                                    (root_dir.parent.parent / 'setup.py').exists()):
            return root_dir.parent.parent
        
        parent = root_dir.parent
        if parent == root_dir:  # Reached filesystem root
            break
        root_dir = parent
    
    cwd = Path.cwd()
    if (cwd / 'setup.py').exists():
        return cwd
    
    if (cwd / 'frontend').exists() and (cwd / 'frontend' / 'package.json').exists():
        return cwd
    
    print(f"Warning: Could not find project root directory. Using current directory: {cwd}")
    return cwd

def find_npm() -> Optional[str]:
    """
    Find the npm executable path.
    
    Returns:
        str or None: Path to npm executable if found, None otherwise
    """
    if sys.platform == 'win32':
        possible_paths = [
            "npm.cmd",  # Check PATH first
            os.path.expandvars(r"%APPDATA%\npm\npm.cmd"),
            os.path.expandvars(r"%ProgramFiles%\nodejs\npm.cmd"),
            os.path.expandvars(r"%ProgramFiles(x86)%\nodejs\npm.cmd"),
            r"C:\Program Files\nodejs\npm.cmd",
            r"C:\Program Files (x86)\nodejs\npm.cmd",
        ]
    else:
        possible_paths = [
            "npm",  # Check PATH first
            "/usr/local/bin/npm",
            "/usr/bin/npm",
            "/opt/homebrew/bin/npm",  # Common macOS Homebrew location
        ]

    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, "--version"], 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            print_color(GREEN, f"Found npm {result.stdout.strip()} at: {path}")
            return path
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    return None

def find_available_port(start_port: int, max_attempts: int = 100) -> Optional[int]:
    """
    Find the next available port starting from the given port.
    
    Args:
        start_port: Initial port to check
        max_attempts: Maximum number of ports to try
    
    Returns:
        int or None: Available port number, or None if no ports found
    """
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return None

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    return find_available_port(port, max_attempts=1) is None

def cleanup() -> None:
    """Terminate all child processes on exit."""
    print_color(CYAN, "\nStopping servers...")
    for process in processes:
        if process and process.poll() is None:
            try:
                if sys.platform == 'win32':
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
            except Exception:
                pass
    print_color(CYAN, "Servers stopped.")

def open_browser(url: str, delay: int = 2) -> None:
    """Open a browser tab after a delay."""
    def _open_browser():
        time.sleep(delay)
        webbrowser.open(url)
    
    thread = threading.Thread(target=_open_browser)
    thread.daemon = True
    thread.start()

def start_backend(project_root: Path, port: int = BACKEND_PORT) -> ProcessType:
    """
    Start the backend FastAPI server using uvicorn.
    
    Args:
        project_root: Project root directory path
        port: Port number to run the server on
    
    Returns:
        ProcessType: Started process handle or None if startup failed
    """
    print_color(GREEN, f"Starting backend server on http://localhost:{port}...")
    
    cmd = [sys.executable, "-m", "uvicorn", "diagram_generator.backend.main:app", "--reload", f"--port={port}"]
    
    try:
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
    except Exception as e:
        print_color(YELLOW, f"Error starting backend server: {str(e)}")
        return None

def start_frontend(project_root: Path, port: int = FRONTEND_PORT, backend_port: int = BACKEND_PORT) -> ProcessType:
    """
    Start the frontend Vite development server.
    
    Args:
        project_root: Project root directory path
        port: Port number to run the server on
        backend_port: Backend API server port for environment config
    
    Returns:
        ProcessType: Started process handle or None if startup failed
    
    Notes:
        - Installs npm dependencies if node_modules is missing
        - Sets VITE_API_BASE_URL environment variable for API connection
    """
    frontend_dir = project_root / 'frontend'
    
    if not frontend_dir.exists():
        print_color(YELLOW, f"❌ Frontend directory not found at {frontend_dir}")
        return None
    
    npm_path = find_npm()
    if not npm_path:
        print_color(YELLOW, "❌ Could not find npm executable.")
        print_color(YELLOW, "Please install Node.js from https://nodejs.org/")
        print_color(YELLOW, "Make sure npm is added to your system PATH")
        return None
    
    # Check and install dependencies
    if not (frontend_dir / 'node_modules').exists():
        print_color(CYAN, "Installing frontend dependencies...")
        try:
            subprocess.run(
                [npm_path, "install"],
                cwd=frontend_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print_color(YELLOW, f"❌ Failed to install dependencies: {e.stdout}")
            return None
    
    print_color(GREEN, f"Starting frontend server on http://localhost:{port}...")
    
    try:
        env = os.environ.copy()
        env["VITE_API_BASE_URL"] = f"http://localhost:{backend_port}"
        
        process = subprocess.Popen(
            [npm_path, "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            env=env,
            shell=sys.platform == 'win32'  # Use shell on Windows only
        )
        processes.append(process)
        return process
        
    except Exception as e:
        print_color(YELLOW, f"❌ Error starting frontend: {str(e)}")
        return None

def monitor_process(process: ProcessType, prefix: str) -> None:
    """
    Monitor a process and print its output with a prefix.
    
    Args:
        process: Process to monitor
        prefix: Text prefix for output lines (e.g., "Backend", "Frontend")
    """
    if process is None or process.stdout is None:
        return
    
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"{GRAY}[{prefix}] {line.rstrip()}{NC}")

def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(description="Diagram Generator CLI")
    parser.add_argument('--backend-only', action='store_true', help='Start only the backend server')
    parser.add_argument('--frontend-only', action='store_true', help='Start only the frontend server')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    parser.add_argument('--backend-port', type=int, default=BACKEND_PORT, help=f'Backend port (default: {BACKEND_PORT})')
    parser.add_argument('--frontend-port', type=int, default=FRONTEND_PORT, help=f'Frontend port (default: {FRONTEND_PORT})')
    
    args = parser.parse_args()
    atexit.register(cleanup)
    
    try:
        project_root = find_project_root()
        print_color(CYAN, "Starting Diagram Generator application...")
        
        # Initialize ports
        actual_backend_port = None
        actual_frontend_port = None
        
        # Start backend if requested
        backend_process = None
        if not args.frontend_only:
            actual_backend_port = find_available_port(args.backend_port)
            if actual_backend_port is None:
                print_color(YELLOW, "❌ Could not find an available port for the backend server.")
                return 1
            if actual_backend_port != args.backend_port:
                print_color(YELLOW, f"⚠️ Port {args.backend_port} is in use. Using port {actual_backend_port} instead.")
            backend_process = start_backend(project_root, actual_backend_port)
            if backend_process is None:
                return 1
        
        # Start frontend if requested
        frontend_process = None
        if not args.backend_only:
            actual_frontend_port = find_available_port(args.frontend_port)
            if actual_frontend_port is None:
                print_color(YELLOW, "❌ Could not find an available port for the frontend server.")
                return 1
            if actual_frontend_port != args.frontend_port:
                print_color(YELLOW, f"⚠️ Port {args.frontend_port} is in use. Using port {actual_frontend_port} instead.")
            frontend_process = start_frontend(project_root, actual_frontend_port, actual_backend_port or BACKEND_PORT)
            if frontend_process is None:
                return 1
        
        # Open browser if requested
        if not args.no_browser and frontend_process is not None:
            open_browser(f"http://localhost:{actual_frontend_port}")
        
        # Display running information
        print_color(CYAN, "\nApplication is running!")
        if backend_process is not None:
            print_color(CYAN, f"- Backend: http://localhost:{actual_backend_port}")
        if frontend_process is not None:
            print_color(CYAN, f"- Frontend: http://localhost:{actual_frontend_port}")
            print_color(CYAN, f"- API URL: http://localhost:{actual_backend_port}")
        print_color(YELLOW, "\nPress Ctrl+C to stop the servers.\n")
        
        # Monitor processes
        threads = []
        if backend_process is not None:
            thread = threading.Thread(target=monitor_process, args=(backend_process, "Backend"))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        if frontend_process is not None:
            thread = threading.Thread(target=monitor_process, args=(frontend_process, "Frontend"))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Wait for processes to complete
        for thread in threads:
            thread.join()
        
    except KeyboardInterrupt:
        print_color(CYAN, "\nReceived keyboard interrupt. Shutting down...")
    except Exception as e:
        print_color(YELLOW, f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
