"""Camera tools for UBM MCP Server"""
from typing import Any, Dict, List, Optional, Tuple
import logging
import math

from ..mcp_server import mcp, get_blender_connector

logger = logging.getLogger(__name__)


@mcp.tool()
def create_camera(
    name: Optional[str] = None,
    location: Tuple[float, float, float] = (7.0, -7.0, 5.0),
    rotation: Tuple[float, float, float] = (1.1, 0.0, 0.8),
    look_at: Optional[Tuple[float, float, float]] = None
) -> Dict[str, Any]:
    """Create a camera in the scene.
    
    Args:
        name: Optional camera name
        location: [x, y, z] camera position
        rotation: [x, y, z] camera rotation in radians (or use look_at)
        look_at: [x, y, z] point to look at (alternative to rotation)
    
    Returns:
        Camera creation result
    """
    connector = get_blender_connector()
    camera_name = name or "Camera"
    
    # If look_at is provided, calculate rotation
    if look_at:
        # Calculate rotation to look at point
        # This is a simplified version
        dx = look_at[0] - location[0]
        dy = look_at[1] - location[1]
        dz = look_at[2] - location[2]
        
        # Calculate rotation angles
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        if distance > 0:
            rot_x = math.atan2(dy, math.sqrt(dx**2 + dz**2))
            rot_y = 0  # Simplified
            rot_z = math.atan2(dx, dz)
            rotation = (rot_x, rot_y, rot_z)
    
    code = f"""
import bpy
import math

# Create camera data
camera_data = bpy.data.cameras.new(name="{camera_name}_Data")

# Create camera object
camera_obj = bpy.data.objects.new(name="{camera_name}", object_data=camera_data)
bpy.context.collection.objects.link(camera_obj)

# Set location and rotation
camera_obj.location = ({location[0]}, {location[1]}, {location[2]})
camera_obj.rotation_euler = ({rotation[0]}, {rotation[1]}, {rotation[2]})

# Make active camera
bpy.context.scene.camera = camera_obj

# Store result
result["data"]["camera"] = {{
    "name": camera_obj.name,
    "location": list(camera_obj.location),
    "rotation": list(camera_obj.rotation_euler),
    "lens": camera_data.lens
}}

# Make active
bpy.context.view_layer.objects.active = camera_obj
"""
    
    result = connector.execute_bpy(code)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "name": camera_name,
            "location": list(location),
            "rotation": list(rotation),
            "data": result.get("data", {})
        }
    else:
        return result


@mcp.tool()
def set_active_camera(name: str) -> Dict[str, Any]:
    """Set the active camera for rendering.
    
    Args:
        name: Camera object name
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

# Find camera
camera_obj = bpy.data.objects.get("{name}")
if not camera_obj:
    result["status"] = "error"
    result["error"] = f"Camera not found: {name}"
elif camera_obj.type != 'CAMERA':
    result["status"] = "error"
    result["error"] = f"Object is not a camera: {name}"
else:
    # Set as active camera
    bpy.context.scene.camera = camera_obj
    result["data"]["active_camera"] = camera_obj.name
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def set_camera_properties(
    name: str,
    lens: Optional[float] = None,
    sensor_width: Optional[float] = None,
    dof_distance: Optional[float] = None,
    aperture_fstop: Optional[float] = None
) -> Dict[str, Any]:
    """Update camera properties.
    
    Args:
        name: Camera object name
        lens: Focal length in mm
        sensor_width: Sensor width in mm
        dof_distance: Depth of field distance
        aperture_fstop: Aperture f-stop value
    
    Returns:
        Update result
    """
    connector = get_blender_connector()
    
    # Build updates
    updates = []
    if lens is not None:
        updates.append(f'camera_data.lens = {lens}')
    if sensor_width is not None:
        updates.append(f'camera_data.sensor_width = {sensor_width}')
    if dof_distance is not None:
        updates.append(f'camera_data.dof.focus_distance = {dof_distance}')
    if aperture_fstop is not None:
        updates.append(f'camera_data.dof.aperture_fstop = {aperture_fstop}')
        updates.append('camera_data.dof.use_dof = True')
    
    if not updates:
        return {
            "status": "error",
            "error": "At least one property must be provided"
        }
    
    code = f"""
import bpy

# Find camera
camera_obj = bpy.data.objects.get("{name}")
if not camera_obj or camera_obj.type != 'CAMERA':
    result["status"] = "error"
    result["error"] = f"Camera not found: {name}"
else:
    camera_data = camera_obj.data
    
    # Apply updates
    {chr(10).join('    ' + u for u in updates)}
    
    # Store result
    result["data"]["camera"] = {{
        "name": camera_obj.name,
        "lens": camera_data.lens,
        "sensor_width": camera_data.sensor_width,
        "dof_distance": getattr(camera_data.dof, 'focus_distance', None),
        "aperture_fstop": getattr(camera_data.dof, 'aperture_fstop', None)
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def frame_object(camera_name: str, object_name: str, padding: float = 1.5) -> Dict[str, Any]:
    """Position camera to frame an object.
    
    Args:
        camera_name: Camera object name
        object_name: Target object name
        padding: Frame padding multiplier
    
    Returns:
        Camera positioning result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy
import math

# Find objects
camera_obj = bpy.data.objects.get("{camera_name}")
target_obj = bpy.data.objects.get("{object_name}")

if not camera_obj or camera_obj.type != 'CAMERA':
    result["status"] = "error"
    result["error"] = f"Camera not found: {camera_name}"
elif not target_obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    # Get object bounds
    if target_obj.type == 'MESH' and target_obj.data:
        bbox = [target_obj.matrix_world @ v.co for v in target_obj.data.vertices]
        center = sum(bbox, bpy.mathutils.Vector()) / len(bbox)
        size = max((max(v[i] for v in bbox) - min(v[i] for v in bbox)) for i in range(3))
    else:
        center = target_obj.location
        size = 2.0
    
    # Calculate camera position
    distance = size * {padding} / math.tan(camera_obj.data.lens * math.pi / 360)
    
    # Position camera
    camera_obj.location = (center[0], center[1] - distance, center[2] + distance * 0.5)
    
    # Look at object
    direction = center - camera_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera_obj.rotation_euler = rot_quat.to_euler()
    
    result["data"]["camera"] = {{
        "name": camera_obj.name,
        "location": list(camera_obj.location),
        "rotation": list(camera_obj.rotation_euler),
        "distance": distance
    }}
    result["data"]["target"] = "{object_name}"
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def list_cameras() -> Dict[str, Any]:
    """List all cameras in the scene.
    
    Returns:
        List of cameras with properties
    """
    connector = get_blender_connector()
    
    code = """
import bpy

cameras = []
active_camera = bpy.context.scene.camera.name if bpy.context.scene.camera else None

for obj in bpy.context.scene.objects:
    if obj.type == 'CAMERA' and obj.data:
        camera_data = obj.data
        cameras.append({
            "name": obj.name,
            "location": [round(x, 4) for x in obj.location],
            "rotation": [round(x, 4) for x in obj.rotation_euler],
            "lens": camera_data.lens,
            "sensor_width": camera_data.sensor_width,
            "is_active": obj.name == active_camera
        })

result["data"]["cameras"] = cameras
result["data"]["count"] = len(cameras)
result["data"]["active"] = active_camera
"""
    
    return connector.execute_bpy(code)
