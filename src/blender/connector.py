"""Blender Connector - Manages connection to Blender"""
import subprocess
import sys
import os
import json
import tempfile
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BlenderConnector:
    """Manages connection to Blender"""
    
    def __init__(self, blender_path: Optional[str] = None):
        self.blender_path = blender_path or self._find_blender()
        self.temp_dir = tempfile.mkdtemp(prefix="ubm_")
        
    def _find_blender(self) -> str:
        """Try to find Blender executable"""
        common_paths = [
            "blender",  # In PATH
            r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender\blender.exe",
            "/usr/bin/blender",
            "/Applications/Blender.app/Contents/MacOS/Blender"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"Found Blender at: {path}")
                return path
            
            # Try 'which' / 'where'
            try:
                result = subprocess.run(
                    ["where" if os.name == "nt" else "which", path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    found_path = result.stdout.strip()
                    if found_path and os.path.exists(found_path):
                        logger.info(f"Found Blender via PATH: {found_path}")
                        return found_path
            except Exception:
                pass
        
        raise FileNotFoundError("Blender not found. Please install Blender or specify path.")
    
    def is_addon_installed(self) -> bool:
        """Check if UBM addon is installed in Blender"""
        # TODO: Check if addon is enabled
        return False
    
    def install_addon(self) -> bool:
        """Install the Blender addon"""
        addon_path = Path(__file__).parent.parent.parent / "addon"
        
        # Create install script
        script = f"""
import bpy
import sys

# Install addon
bpy.ops.preferences.addon_install(filepath="{addon_path}")
bpy.ops.preferences.addon_enable(module="ubm_addon")

print("UBM addon installed and enabled")
"""
        
        try:
            result = subprocess.run(
                [self.blender_path, "--background", "--python-expr", script],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to install addon: {e}")
            return False
    
    def execute_bpy(self, code: str) -> Dict[str, Any]:
        """Execute Python code in Blender"""
        # Write code to temp file
        script_path = Path(self.temp_dir) / "script.py"
        result_path = Path(self.temp_dir) / "result.json"
        
        # Wrap code to capture result
        wrapped_code = f"""
import bpy
import json
import sys

# User code
{code}

# Save result
result = {{"status": "success"}}
with open("{result_path}", "w") as f:
    json.dump(result, f)
"""
        
        script_path.write_text(wrapped_code)
        
        # Execute in Blender
        try:
            result = subprocess.run(
                [self.blender_path, "--background", "--python", str(script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "error": result.stderr
                }
            
            # Read result
            if result_path.exists():
                return json.loads(result_path.read_text())
            else:
                return {"status": "success"}
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Execution timeout"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
