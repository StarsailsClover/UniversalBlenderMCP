"""Import/Export tools for UBM MCP Server"""
from typing import Any, Dict, List, Optional
import os

from ..mcp_server import mcp, get_blender_connector


@mcp.tool()
def import_model(
    filepath: str,
    name: Optional[str] = None,
    location: List[float] = None
) -> Dict[str, Any]:
    """Import a 3D model file.
    
    Args:
        filepath: Path to model file
        name: Optional name for imported object
        location: [x, y, z] import location
    
    Returns:
        Import result
    """
    if not os.path.exists(filepath):
        return {
            "status": "error",
            "error": f"File not found: {filepath}"
        }
    
    # Detect format from extension
    ext = os.path.splitext(filepath)[1].lower()
    
    format_map = {
        ".obj": "obj",
        ".fbx": "fbx",
        ".gltf": "gltf",
        ".glb": "gltf",
        ".ply": "ply",
        ".stl": "stl",
        ".x3d": "x3d",
        ".usd": "usd",
        ".usda": "usd",
        ".usdc": "usd"
    }
    
    format_type = format_map.get(ext)
    if not format_type:
        return {
            "status": "error",
            "error": f"Unsupported format: {ext}. Supported: {', '.join(format_map.keys())}"
        }
    
    connector = get_blender_connector()
    
    loc_str = f"({location[0]}, {location[1]}, {location[2]})" if location else "(0, 0, 0)"
    
    code = f"""
import bpy
import os

filepath = r"{filepath}"

# Import based on format
if "{format_type}" == "obj":
    bpy.ops.import_scene.obj(filepath=filepath)
elif "{format_type}" == "fbx":
    bpy.ops.import_scene.fbx(filepath=filepath)
elif "{format_type}" == "gltf":
    bpy.ops.import_scene.gltf(filepath=filepath)
elif "{format_type}" == "ply":
    bpy.ops.import_scene.ply(filepath=filepath)
elif "{format_type}" == "stl":
    bpy.ops.import_scene.stl(filepath=filepath)
elif "{format_type}" == "x3d":
    bpy.ops.import_scene.x3d(filepath=filepath)
elif "{format_type}" == "usd":
    bpy.ops.wm.usd_import(filepath=filepath)

# Get imported objects
imported = []
for obj in bpy.context.selected_objects:
    obj.location = {loc_str}
    if "{name or ''}":
        obj.name = "{name or ''}"
    imported.append({{
        "name": obj.name,
        "type": obj.type
    }})

result["data"]["imported"] = imported
result["data"]["format"] = "{format_type}"
result["data"]["filepath"] = filepath
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def export_model(
    filepath: str,
    object_names: Optional[List[str]] = None,
    format: Optional[str] = None,
    selected_only: bool = False
) -> Dict[str, Any]:
    """Export objects to a 3D model file.
    
    Args:
        filepath: Output file path
        object_names: List of object names to export (None for all)
        format: Export format (auto-detected from extension if None)
        selected_only: Export only selected objects
    
    Returns:
        Export result
    """
    # Detect format from extension if not specified
    if not format:
        ext = os.path.splitext(filepath)[1].lower()
        format_map = {
            ".obj": "obj",
            ".fbx": "fbx",
            ".gltf": "gltf",
            ".glb": "gltf",
            ".ply": "ply",
            ".stl": "stl",
            ".x3d": "x3d",
            ".usd": "usd",
            ".usda": "usd",
            ".usdc": "usd"
        }
        format = format_map.get(ext)
        if not format:
            return {
                "status": "error",
                "error": f"Cannot detect format from extension: {ext}"
            }
    
    connector = get_blender_connector()
    
    # Build selection code
    selection_code = ""
    if object_names and not selected_only:
        selection_code = f"""
# Select specified objects
for obj in bpy.context.scene.objects:
    obj.select_set(False)
for name in {object_names}:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.select_set(True)
"""
    
    code = f"""
import bpy
import os

# Ensure output directory exists
os.makedirs(os.path.dirname(r"{filepath}"), exist_ok=True)

{selection_code}

# Export based on format
if "{format}" == "obj":
    bpy.ops.export_scene.obj(
        filepath=r"{filepath}",
        use_selection=True
    )
elif "{format}" == "fbx":
    bpy.ops.export_scene.fbx(
        filepath=r"{filepath}",
        use_selection=True
    )
elif "{format}" == "gltf":
    bpy.ops.export_scene.gltf(
        filepath=r"{filepath}",
        use_selection=True
    )
elif "{format}" == "ply":
    bpy.ops.export_scene.ply(
        filepath=r"{filepath}",
        use_selection=True
    )
elif "{format}" == "stl":
    bpy.ops.export_scene.stl(
        filepath=r"{filepath}",
        use_selection=True
    )
elif "{format}" == "usd":
    bpy.ops.wm.usd_export(
        filepath=r"{filepath}",
        selected_objects_only=True
    )

result["data"]["exported"] = True
result["data"]["format"] = "{format}"
result["data"]["filepath"] = r"{filepath}"
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def export_gltf(
    filepath: str,
    format: str = "GLB",
    export_materials: str = "EXPORT",
    export_textures: bool = True,
    selected_only: bool = False
) -> Dict[str, Any]:
    """Export scene to glTF 2.0 format.
    
    Args:
        filepath: Output path (.glb or .gltf)
        format: "GLB" or "GLTF_SEPARATE"
        export_materials: "EXPORT", "PLACEHOLDER", or "NONE"
        export_textures: Whether to export textures
        selected_only: Export only selected objects
    
    Returns:
        Export result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy
import os

os.makedirs(os.path.dirname(r"{filepath}"), exist_ok=True)

# Set selection
if {selected_only}:
    for obj in bpy.context.scene.objects:
        if obj not in bpy.context.selected_objects:
            obj.select_set(False)

# Export glTF
bpy.ops.export_scene.gltf(
    filepath=r"{filepath}",
    export_format="{format}",
    export_materials="{export_materials}",
    export_textures={export_textures},
    use_selection={selected_only}
)

result["data"]["exported"] = True
result["data"]["format"] = "gltf"
result["data"]["filepath"] = r"{filepath}"
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def save_blend(filepath: str = None) -> Dict[str, Any]:
    """Save the current Blender file.
    
    Args:
        filepath: Optional save path (uses current if None)
    
    Returns:
        Save result
    """
    connector = get_blender_connector()
    
    if filepath:
        code = f"""
import bpy
import os

os.makedirs(os.path.dirname(r"{filepath}"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=r"{filepath}")

result["data"]["saved"] = True
result["data"]["filepath"] = r"{filepath}"
"""
    else:
        code = """
import bpy

bpy.ops.wm.save_mainfile()

result["data"]["saved"] = True
result["data"]["filepath"] = bpy.data.filepath
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def load_blend(filepath: str) -> Dict[str, Any]:
    """Load a Blender file.
    
    Args:
        filepath: Path to .blend file
    
    Returns:
        Load result
    """
    if not os.path.exists(filepath):
        return {
            "status": "error",
            "error": f"File not found: {filepath}"
        }
    
    connector = get_blender_connector()
    
    code = f"""
import bpy

bpy.ops.wm.open_mainfile(filepath=r"{filepath}")

result["data"]["loaded"] = True
result["data"]["filepath"] = r"{filepath}"
result["data"]["scene"] = bpy.context.scene.name
result["data"]["objects_count"] = len(bpy.context.scene.objects)
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def list_supported_formats() -> Dict[str, Any]:
    """List supported import/export formats.
    
    Returns:
        List of supported formats
    """
    formats = {
        "import": ["obj", "fbx", "gltf", "glb", "ply", "stl", "x3d", "usd"],
        "export": ["obj", "fbx", "gltf", "glb", "ply", "stl", "x3d", "usd"]
    }
    
    return {
        "status": "success",
        "formats": formats
    }
