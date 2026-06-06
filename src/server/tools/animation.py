"""Animation tools for UBM MCP Server"""
from typing import Any, Dict, List, Optional, Tuple
import logging

from ..mcp_server import mcp, get_blender_connector

logger = logging.getLogger(__name__)


@mcp.tool()
def set_keyframe(
    object_name: str,
    frame: int,
    location: Optional[Tuple[float, float, float]] = None,
    rotation: Optional[Tuple[float, float, float]] = None,
    scale: Optional[Tuple[float, float, float]] = None
) -> Dict[str, Any]:
    """Set a keyframe for an object.
    
    Args:
        object_name: Object name
        frame: Frame number
        location: [x, y, z] location keyframe
        rotation: [x, y, z] rotation keyframe (radians)
        scale: [x, y, z] scale keyframe
    
    Returns:
        Keyframe result
    """
    if not any([location, rotation, scale]):
        return {
            "status": "error",
            "error": "At least one of location, rotation, or scale must be provided"
        }
    
    connector = get_blender_connector()
    
    # Build keyframe operations
    keyframe_ops = []
    if location:
        keyframe_ops.append(f'obj.location = ({location[0]}, {location[1]}, {location[2]})')
        keyframe_ops.append("obj.keyframe_insert(data_path=\"location\", frame={frame})")
    if rotation:
        keyframe_ops.append(f'obj.rotation_euler = ({rotation[0]}, {rotation[1]}, {rotation[2]})')
        keyframe_ops.append("obj.keyframe_insert(data_path=\"rotation_euler\", frame={frame})")
    if scale:
        keyframe_ops.append(f'obj.scale = ({scale[0]}, {scale[1]}, {scale[2]})')
        keyframe_ops.append("obj.keyframe_insert(data_path=\"scale\", frame={frame})")
    
    code = f"""
import bpy

# Find object
obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    # Set current frame
    bpy.context.scene.frame_set({frame})
    
    # Insert keyframes
    {chr(10).join('    ' + op for op in keyframe_ops)}
    
    result["data"]["keyframe"] = {{
        "object": obj.name,
        "frame": {frame},
        "properties": {len(keyframe_ops) // 2}
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def set_frame_range(start: int, end: int) -> Dict[str, Any]:
    """Set the animation frame range.
    
    Args:
        start: Start frame
        end: End frame
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

scene = bpy.context.scene
scene.frame_start = {start}
scene.frame_end = {end}

result["data"]["frame_range"] = {{
    "start": scene.frame_start,
    "end": scene.frame_end
}}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def get_frame() -> int:
    """Get current frame number.
    
    Returns:
        Current frame
    """
    connector = get_blender_connector()
    
    code = """
import bpy
result["data"]["frame"] = bpy.context.scene.frame_current
"""
    
    result = connector.execute_bpy(code)
    if result["status"] == "success":
        return result.get("data", {}).get("frame", 1)
    return 1


@mcp.tool()
def set_frame(frame: int) -> Dict[str, Any]:
    """Set current frame.
    
    Args:
        frame: Frame number
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy
bpy.context.scene.frame_set({frame})
result["data"]["frame"] = bpy.context.scene.frame_current
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def clear_animation(object_name: str, property_type: Optional[str] = None) -> Dict[str, Any]:
    """Clear animation data from an object.
    
    Args:
        object_name: Object name
        property_type: Specific property to clear (location, rotation, scale, or None for all)
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    if property_type:
        data_path = property_type
        code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path == "{data_path}":
                obj.animation_data.action.fcurves.remove(fcurve)
    
    result["data"]["cleared"] = "{property_type}"
"""
    else:
        code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    # Clear all animation data
    if obj.animation_data:
        obj.animation_data_clear()
    
    result["data"]["cleared"] = "all"
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def list_keyframes(object_name: str) -> Dict[str, Any]:
    """List all keyframes for an object.
    
    Args:
        object_name: Object name
    
    Returns:
        Keyframe information
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    keyframes = {{}}
    
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            data_path = fcurve.data_path
            keyframes[data_path] = []
            
            for keyframe in fcurve.keyframe_points:
                keyframes[data_path].append({{
                    "frame": keyframe.co[0],
                    "value": keyframe.co[1]
                }})
    
    result["data"]["keyframes"] = keyframes
    result["data"]["has_animation"] = len(keyframes) > 0
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def play_animation() -> Dict[str, Any]:
    """Start animation playback.
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    code = """
import bpy
bpy.ops.screen.animation_play()
result["data"]["playing"] = True
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def stop_animation() -> Dict[str, Any]:
    """Stop animation playback.
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    code = """
import bpy
bpy.ops.screen.animation_cancel()
result["data"]["playing"] = False
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def create_rotation_animation(
    object_name: str,
    start_frame: int = 1,
    end_frame: int = 60,
    axis: str = "Z",
    degrees: float = 360.0
) -> Dict[str, Any]:
    """Create a simple rotation animation.
    
    Args:
        object_name: Object to animate
        start_frame: Start frame
        end_frame: End frame
        axis: Rotation axis (X, Y, or Z)
        degrees: Total rotation in degrees
    
    Returns:
        Animation creation result
    """
    connector = get_blender_connector()
    
    # Convert to radians
    import math
    radians = degrees * math.pi / 180.0
    
    axis = axis.upper()
    if axis not in ["X", "Y", "Z"]:
        return {
            "status": "error",
            "error": f"Invalid axis: {axis}. Use X, Y, or Z"
        }
    
    code = f"""
import bpy
import math

obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    # Clear existing rotation animation
    if obj.animation_data and obj.animation_data.action:
        for fcurve in list(obj.animation_data.action.fcurves):
            if "rotation" in fcurve.data_path:
                obj.animation_data.action.fcurves.remove(fcurve)
    
    # Get initial rotation
    initial_rot = list(obj.rotation_euler)
    
    # Set start keyframe
    bpy.context.scene.frame_set({start_frame})
    obj.rotation_euler = initial_rot
    obj.keyframe_insert(data_path="rotation_euler", frame={start_frame})
    
    # Calculate end rotation
    end_rot = list(initial_rot)
    if "{axis}" == "X":
        end_rot[0] += {radians}
    elif "{axis}" == "Y":
        end_rot[1] += {radians}
    else:
        end_rot[2] += {radians}
    
    # Set end keyframe
    bpy.context.scene.frame_set({end_frame})
    obj.rotation_euler = end_rot
    obj.keyframe_insert(data_path="rotation_euler", frame={end_frame})
    
    # Set linear interpolation
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            if "rotation" in fcurve.data_path:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'LINEAR'
    
    result["data"]["animation"] = {{
        "object": obj.name,
        "type": "rotation",
        "axis": "{axis}",
        "start_frame": {start_frame},
        "end_frame": {end_frame},
        "degrees": {degrees}
    }}
"""
    
    return connector.execute_bpy(code)
