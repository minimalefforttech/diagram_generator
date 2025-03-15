"""PlantUML API endpoints for rendering diagrams."""

import os
import subprocess
import base64
import tempfile
import logging
import shutil
import glob
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body, Request
from pydantic import BaseModel
from typing import Optional

from diagram_generator.backend.api.logs import log_info, log_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/plantuml", tags=["plantuml"])

class PlantUMLRequest(BaseModel):
    """Request model for PlantUML diagram generation."""
    code: str
    format: str = "png"  # png or svg

def find_java_installation() -> Optional[str]:
    """Find Java installation path on Windows."""
    # First check if java is in PATH
    java_path = shutil.which('java')
    if java_path:
        return java_path
        
    # Common Java installation directories on Windows
    search_paths = [
        r"C:\Program Files\Java\*\bin\java.exe",
        r"C:\Program Files (x86)\Java\*\bin\java.exe",
        r"C:\Program Files\Eclipse Adoptium\*\bin\java.exe",
        r"C:\Program Files\Eclipse Foundation\*\bin\java.exe",
        r"C:\Program Files\Zulu\*\bin\java.exe",
        r"C:\Program Files\Amazon Corretto\*\bin\java.exe",
        r"C:\Program Files\Microsoft\*\bin\java.exe",
        os.path.expandvars(r"%JAVA_HOME%\bin\java.exe"),
        os.path.expanduser(r"~\scoop\apps\openjdk*\current\bin\java.exe"),
        os.path.expanduser(r"~\scoop\apps\zulu*\current\bin\java.exe"),
    ]
    
    for pattern in search_paths:
        try:
            matches = glob.glob(pattern)
            if matches:
                # Use the most recently modified Java installation
                return max(matches, key=os.path.getmtime)
        except Exception as e:
            logger.debug(f"Error checking Java path {pattern}: {e}")
            continue
            
    return None

def check_java_installation():
    """Check if Java is installed and available."""
    java_path = find_java_installation()
    if not java_path:
        error_msg = (
            "Java is not installed or not found. To fix this:\n"
            "1. Install Java (JRE or JDK) from https://adoptium.net\n"
            "2. Add Java to your system PATH, or\n"
            "3. Set JAVA_HOME environment variable\n\n"
            "After installing, you may need to restart your application."
        )
        log_error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )
    
    try:
        # Verify Java version
        result = subprocess.run(
            [java_path, "-version"],
            capture_output=True,
            text=True,
            shell=True  # Required for Windows
        )
        log_info(f"Found Java installation", {"path": java_path, "version": result.stderr.strip()})
        return java_path
    except Exception as e:
        error_msg = f"Error verifying Java installation: {str(e)}"
        log_error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/render")
async def render_plantuml(request: Request, plantuml_req: PlantUMLRequest = Body(...)):
    """
    Render a PlantUML diagram using the local JAR file.
    Returns a base64 encoded image.
    """
    try:
        # Log incoming request
        log_info(f"PlantUML render request received", {
            "client_host": request.client.host,
            "format": plantuml_req.format,
            "code_preview": plantuml_req.code[:100] + "..."
        })
        
        # Check Java installation first
        java_path = check_java_installation()
        
        # Get project root directory to find the JAR file
        project_root = Path(__file__).resolve().parents[4]  # Go up 4 levels
        plantuml_jar = project_root / "frontend" / "public" / "plantuml.jar"
        
        log_info(f"Looking for PlantUML JAR", {"path": str(plantuml_jar)})
        
        if not plantuml_jar.exists():
            error_msg = f"PlantUML JAR file not found at {plantuml_jar}"
            log_error(error_msg)
            raise HTTPException(
                status_code=500, 
                detail=error_msg
            )
        
        log_info(f"PlantUML JAR found", {"path": str(plantuml_jar)})
        
        # Create a temporary directory for the input and output files
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "input.puml"
            
            # Write the PlantUML code to the input file
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(plantuml_req.code)
            
            # Build the command for subprocess
            cmd = [
                str(java_path),  # Use the found Java executable
                "-jar",
                str(plantuml_jar),
                f"-t{plantuml_req.format}",  # Output format
                "-output", str(temp_dir),  # Output directory
                str(input_file)  # Input file
            ]
            
            log_info(f"Running PlantUML command", {"command": ' '.join(cmd)})
            
            try:
                # Run PlantUML jar with subprocess.run (synchronous)
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    shell=True  # Required for Windows
                )
                
                if result.stdout:
                    log_info(f"PlantUML stdout", {"output": result.stdout})
                
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if e.stderr else str(e)
                log_error(f"PlantUML rendering error: {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=f"PlantUML rendering failed: {error_msg}"
                )
            
            # Look for the output file - PlantUML might name it differently
            output_file = Path(temp_dir) / f"output.{plantuml_req.format}"
            if not output_file.exists():
                output_file = Path(temp_dir) / f"input.{plantuml_req.format}"
            
            if not output_file.exists():
                # List all files in temp directory for debugging
                all_files = list(Path(temp_dir).glob('*'))
                log_error(f"PlantUML output file not found", {"files_in_temp": [str(f) for f in all_files]})
                raise HTTPException(
                    status_code=500,
                    detail="PlantUML output file not found"
                )
            
            log_info(f"Found output file", {"path": str(output_file)})
            
            # Read and encode the generated image
            with open(output_file, "rb") as f:
                image_data = f.read()
            
            # Convert to base64
            base64_data = base64.b64encode(image_data).decode("utf-8")
            content_type = "image/png" if plantuml_req.format == "png" else "image/svg+xml"
            
            log_info(f"Successfully encoded image as base64", {"bytes": len(image_data)})
            
            return {
                "image": f"data:{content_type};base64,{base64_data}",
                "format": plantuml_req.format
            }
            
    except HTTPException:
        raise  # Re-raise HTTP exceptions as is
    except Exception as e:
        error_msg = f"Error rendering PlantUML diagram: {str(e)}"
        log_error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )