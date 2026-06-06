"""UBM MCP Server - Core server implementation using FastMCP"""
from fastmcp import FastMCP
from typing import Any, Dict, List, Optional, Tuple
import logging
import sys
import os

# Configure logging to stderr to avoid interfering with stdio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp = FastMCP("universal-blender-mcp")

# Global blender connector instance
_blender_connector = None

def get_blender_connector():
    """Get or create blender connector singleton"""
    global _blender_connector
    if _blender_connector is None:
        from ..blender.connector import BlenderConnector
        _blender_connector = BlenderConnector()
    return _blender_connector


@mcp.tool()
def get_server_info() -> Dict[str, Any]:
    """Get information about the UBM server capabilities."""
    return {
        "name": "Universal Blender MCP",
        "version": "0.1.0",
        "description": "Universal MCP server for Blender with Rust screenshot",
        "capabilities": [
            "primitive_creation",
            "object_transformation",
            "material_management",
            "scene_operations",
            "viewport_capture"
        ]
    }


@mcp.tool()
def list_available_tools() -> List[str]:
    """List all available 3D modeling tools."""
    return [
        "create_primitive",
        "delete_object",
        "transform_object",
        "get_scene_info",
        "capture_viewport",
        "list_objects",
        "set_material_color"
    ]


@mcp.tool()
def create_primitive(
    type: str,
    name: Optional[str] = None,
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    size: float = 1.0
) -> Dict[str, Any]:
    """Create a primitive object in Blender.
    
    Args:
        type: Primitive type (CUBE, SPHERE, CYLINDER, CONE, PLANE)
        name: Optional custom name for the object
        location: [x, y, z] coordinates
        size: Base size of the primitive
    
    Returns:
        Object creation result with name, type, and location
    """
    # Validate type
    valid_types = ["CUBE", "SPHERE", "CYLINDER", "CONE", "PLANE"]
    type_upper = type.upper()
    if type_upper not in valid_types:
        return {
            "status": "error",
            "error": f"Invalid type: {type}. Valid types: {', '.join(valid_types)}"
        }
    
    connector = get_blender_connector()
    obj_name = name or f"{type.capitalize()}_001"
    
    # Map type to Blender operator
    operator_map = {
        "CUBE": "bpy.ops.mesh.primitive_cube_add",
        "SPHERE": "bpy.ops.mesh.primitive_uv_sphere_add",
        "CYLINDER": "bpy.ops.mesh.primitive_cylinder_add",
        "CONE": "bpy.ops.mesh.primitive_cone_add",
        "PLANE": "bpy.ops.mesh.primitive_plane_add"
    }
    
    operator = operator_map[type_upper]
    loc_str = f"({location[0]}, {location[1]}, {location[2]})"
    
    code = f"""
# Create primitive
{operator}(size={size}, location={loc_str})

# Get created object
obj = bpy.context.active_object
if obj:
    obj.name = "{obj_name}"
    result["data"]["object"] = {{
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale)
    }}
"""
    
    result = connector.execute_bpy(code)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "type": type_upper,
            "name": obj_name,
            "location": list(location),
            "size": size,
            "data": result.get("data", {})
        }
    else:
        return result


@mcp.tool()
def delete_object(name: str) -> Dict[str, Any]:
    """Delete an object from the scene.
    
    Args:
        name: Name of the object to delete
    
    Returns:
        Deletion result
    """
    connector = get_blender_connector()
    
    code = f"""
# Find and delete object
obj = bpy.data.objects.get("{name}")
if obj:
    bpy.data.objects.remove(obj, do_unlink=True)
    result["data"]["deleted"] = "{name}"
else:
    result["status"] = "error"
    result["error"] = f"Object not found: {name}"
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def transform_object(
    name: str,
    location: Optional[Tuple[float, float, float]] = None,
    rotation: Optional[Tuple[float, float, float]] = None,
    scale: Optional[Tuple[float, float, float]] = None
) -> Dict[str, Any]:
    """Transform an object in the scene.
    
    Only specified parameters will be modified.
    
    Args:
        name: Object name
        location: New [x, y, z] location
        rotation: New [x, y, z] rotation in radians
        scale: New [x, y, z] scale
    
    Returns:
        Transformation result
    """
    connector = get_blender_connector()
    
    # Build transformation code
    transforms = []
    if location:
        transforms.append(f'obj.location = ({location[0]}, {location[1]}, {location[2]})')
    if rotation:
        transforms.append(f'obj.rotation_euler = ({rotation[0]}, {rotation[1]}, {rotation[2]})')
    if scale:
        transforms.append(f'obj.scale = ({scale[0]}, {scale[1]}, {scale[2]})')
    
    if not transforms:
        return {
            "status": "error",
            "error": "At least one transformation parameter must be provided"
        }
    
    code = f"""
# Find and transform object
obj = bpy.data.objects.get("{name}")
if obj:
    {chr(10).join('    ' + t for t in transforms)}
    
    result["data"]["object"] = {{
        "name": obj.name,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale)
    }}
    result["data"]["transforms_applied"] = {len(transforms)}
else:
    result["status"] = "error"
    result["error"] = f"Object not found: {name}"
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def get_scene_info() -> Dict[str, Any]:
    """Get current scene information.
    
    Returns:
        Scene information including objects, materials, lights
    """
    connector = get_blender_connector()
    return connector.get_scene_info()


@mcp.tool()
def list_objects() -> Dict[str, Any]:
    """List all objects in the scene.
    
    Returns:
        List of objects with basic info
    """
    connector = get_blender_connector()
    
    code = """
objects = []
for obj in bpy.context.scene.objects:
    objects.append({
        "name": obj.name,
        "type": obj.type,
        "location": [round(x, 4) for x in obj.location],
        "visible": obj.visible_get()
    })

result["data"]["objects"] = objects
result["data"]["count"] = len(objects)
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def set_material_color(
    object_name: str,
    color: Tuple[float, float, float, float],
    material_name: Optional[str] = None
) -> Dict[str, Any]:
    """Set material color for an object.
    
    Args:
        object_name: Name of the object
        color: [r, g, b, a] color values (0-1)
        material_name: Optional material name (creates new if not exists)
    
    Returns:
        Material application result
    """
    connector = get_blender_connector()
    
    mat_name = material_name or f"{object_name}_Material"
    
    code = f"""
obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    # Create or get material
    mat = bpy.data.materials.get("{mat_name}")
    if not mat:
        mat = bpy.data.materials.new(name="{mat_name}")
    
    # Enable nodes
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    
    if principled:
        principled.inputs["Base Color"].default_value = ({color[0]}, {color[1]}, {color[2]}, {color[3]})
    
    # Assign to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    result["data"]["material"] = {{
        "name": mat.name,
        "color": [{color[0]}, {color[1]}, {color[2]}, {color[3]}]
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def capture_viewport(
    output_path: Optional[str] = None,
    width: int = 1920,
    height: int = 1080,
    use_rust: bool = True
) -> str:
    """Capture the current Blender viewport.
    
    Args:
        output_path: Where to save the screenshot (auto-generated if None)
        width: Screenshot width
        height: Screenshot height
        use_rust: Use native Rust screenshot for better performance
    
    Returns:
        Path to the saved screenshot
    """
    import tempfile
    import time
    
    if output_path is None:
        timestamp = int(time.time())
        output_path = f"/tmp/ubm_capture_{timestamp}.png"
    
    logger.info(f"Capturing viewport to {output_path} ({width}x{height})")
    
    # Try Rust screenshot first if enabled
    if use_rust:
        try:
            from ..rust_bridge import capture_blender_viewport
            result_path = capture_blender_viewport(output_path, width, height)
            logger.info(f"Rust screenshot saved: {result_path}")
            return result_path
        except Exception as e:
            logger.warning(f"Rust screenshot failed: {e}, falling back to Blender render")
    
    # Fallback to Blender's built-in render
    connector = get_blender_connector()
    
    code = f"""
import bpy

# Set render resolution
scene = bpy.context.scene
scene.render.resolution_x = {width}
scene.render.resolution_y = {height}
scene.render.resolution_percentage = 100

# Set output path
scene.render.filepath = r"{output_path}"

# Render
bpy.ops.render.render(write_still=True)

result["data"]["path"] = r"{output_path}"
result["data"]["width"] = {width}
result["data"]["height"] = {height}
"""
    
    result = connector.execute_bpy(code, timeout=60)  # Longer timeout for render
    
    if result["status"] == "success":
        return output_path
    else:
        logger.error(f"Screenshot failed: {result.get('error')}")
        return f"Error: {result.get('error', 'Unknown error')}"


def main():
    """Run the MCP server"""
    logger.info("Starting Universal Blender MCP server")
    
    # Test blender connection on startup
    try:
        connector = get_blender_connector()
        logger.info(f"Blender found at: {connector.blender_path}")
    except Exception as e:
        logger.warning(f"Blender not found: {e}")
        logger.info("Server will start but tools may fail until Blender is available")
    
    mcp.run()


if __name__ == "__main__":
    main()
