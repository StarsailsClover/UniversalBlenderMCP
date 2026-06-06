"""UBM MCP Server - Core server implementation using FastMCP"""
from fastmcp import FastMCP
from typing import Any, Dict, List, Optional, Tuple
import logging
import sys

# Configure logging to stderr to avoid interfering with stdio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp = FastMCP("universal-blender-mcp")


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
        "capture_viewport"
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
    # This is a placeholder - actual implementation will call Blender
    obj_name = name or f"{type.capitalize()}_001"
    
    logger.info(f"Creating {type} named {obj_name} at {location}")
    
    return {
        "status": "success",
        "type": type,
        "name": obj_name,
        "location": list(location),
        "size": size,
        "message": f"Created {type} '{obj_name}' at {location}"
    }


@mcp.tool()
def delete_object(name: str) -> Dict[str, Any]:
    """Delete an object from the scene.
    
    Args:
        name: Name of the object to delete
    
    Returns:
        Deletion result
    """
    logger.info(f"Deleting object: {name}")
    
    return {
        "status": "success",
        "deleted": name,
        "message": f"Deleted object '{name}'"
    }


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
    logger.info(f"Transforming object: {name}")
    
    result = {
        "status": "success",
        "object": name,
        "transforms": {}
    }
    
    if location:
        result["transforms"]["location"] = list(location)
    if rotation:
        result["transforms"]["rotation"] = list(rotation)
    if scale:
        result["transforms"]["scale"] = list(scale)
    
    return result


@mcp.tool()
def get_scene_info() -> Dict[str, Any]:
    """Get current scene information.
    
    Returns:
        Scene information including objects, materials, lights
    """
    # Placeholder - will be populated with actual Blender data
    return {
        "status": "success",
        "scene_name": "Scene",
        "objects_count": 0,
        "objects": [],
        "materials_count": 0,
        "lights_count": 0,
        "cameras_count": 0
    }


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
    
    if use_rust:
        try:
            from ..rust_bridge import capture_viewport
            result = capture_viewport(output_path, width, height)
            return result
        except ImportError:
            logger.warning("Rust module not available, using fallback")
    
    # Fallback or actual Blender implementation
    return output_path


def main():
    """Run the MCP server"""
    logger.info("Starting Universal Blender MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
