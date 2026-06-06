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
            r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
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
    
    def execute_bpy(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code in Blender and return result.
        
        Args:
            code: Python code to execute (using bpy)
            timeout: Maximum execution time in seconds
        
        Returns:
            Execution result with status, result or error
        """
        import uuid
        
        # Generate unique IDs for this execution
        execution_id = str(uuid.uuid4())[:8]
        script_path = Path(self.temp_dir) / f"script_{execution_id}.py"
        result_path = Path(self.temp_dir) / f"result_{execution_id}.json"
        
        # Wrap code to capture result with error handling
        wrapped_code = f"""import bpy
import json
import traceback
import sys

result = {{"status": "success", "data": {{}}}}

try:
    # Execute user code
{chr(10).join('    ' + line for line in code.split(chr(10)))}
    
    # Try to get context info
    try:
        if bpy.context.active_object:
            obj = bpy.context.active_object
            result["data"]["active_object"] = {{
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location)
            }}
    except:
        pass
        
except Exception as e:
    result["status"] = "error"
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()

# Save result
with open(r"{result_path}", "w") as f:
    json.dump(result, f, indent=2)
"""
        
        script_path.write_text(wrapped_code, encoding='utf-8')
        
        # Execute in Blender
        try:
            logger.info(f"Executing Blender script: {script_path}")
            proc_result = subprocess.run(
                [self.blender_path, "--background", "--python", str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logger.debug(f"Blender stdout: {proc_result.stdout}")
            logger.debug(f"Blender stderr: {proc_result.stderr}")
            
            if proc_result.returncode != 0:
                # Blender execution failed
                return {
                    "status": "error",
                    "error": f"Blender execution failed: {proc_result.stderr}",
                    "stdout": proc_result.stdout
                }
            
            # Read result
            if result_path.exists():
                with open(result_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                # Clean up result file
                result_path.unlink()
                return result
            else:
                return {
                    "status": "error",
                    "error": "Result file not created",
                    "stdout": proc_result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": f"Execution timeout after {timeout}s"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def execute_bpy_simple(self, code: str) -> Dict[str, Any]:
        """Execute simple bpy code without complex result handling"""
        return self.execute_bpy(code)
    
    def get_scene_info(self) -> Dict[str, Any]:
        """Get current scene information from Blender"""
        code = """
# Get scene info
scene = bpy.context.scene
objects = []

for obj in scene.objects:
    obj_info = {
        "name": obj.name,
        "type": obj.type,
        "location": [round(x, 4) for x in obj.location],
        "rotation": [round(x, 4) for x in obj.rotation_euler],
        "scale": [round(x, 4) for x in obj.scale],
        "visible": obj.visible_get()
    }
    
    # Add mesh-specific info
    if obj.type == 'MESH' and obj.data:
        obj_info["vertices"] = len(obj.data.vertices)
        obj_info["faces"] = len(obj.data.polygons)
    
    objects.append(obj_info)

# Collect scene info
result["data"]["scene"] = {
    "name": scene.name,
    "frame_current": scene.frame_current,
    "frame_start": scene.frame_start,
    "frame_end": scene.frame_end,
    "objects_count": len(objects),
    "objects": objects,
    "render_engine": scene.render.engine,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y]
}
"""
        return self.execute_bpy(code)
