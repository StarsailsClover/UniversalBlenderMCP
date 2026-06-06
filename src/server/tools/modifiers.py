"""Modifiers and boolean operations tools for UBM MCP Server"""
from typing import Any, Dict, List, Optional

from ..mcp_server import mcp, get_blender_connector


@mcp.tool()
def add_modifier(
    object_name: str,
    type: str,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """Add a modifier to an object.
    
    Args:
        object_name: Object name
        type: Modifier type (SUBSURF, BEVEL, BOOLEAN, ARRAY, MIRROR, etc.)
        name: Optional modifier name
    
    Returns:
        Modifier addition result
    """
    connector = get_blender_connector()
    
    mod_name = name or f"{type}_Modifier"
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj or obj.type != 'MESH':
    result["status"] = "error"
    result["error"] = f"Mesh object not found: {object_name}"
else:
    # Add modifier
    modifier = obj.modifiers.new(name="{mod_name}", type="{type}")
    
    result["data"]["modifier"] = {{
        "name": modifier.name,
        "type": modifier.type,
        "object": obj.name
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def remove_modifier(
    object_name: str,
    modifier_name: str
) -> Dict[str, Any]:
    """Remove a modifier from an object.
    
    Args:
        object_name: Object name
        modifier_name: Modifier name
    
    Returns:
        Removal result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    modifier = obj.modifiers.get("{modifier_name}")
    if modifier:
        obj.modifiers.remove(modifier)
        result["data"]["removed"] = "{modifier_name}"
    else:
        result["status"] = "error"
        result["error"] = f"Modifier not found: {modifier_name}"
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def set_modifier_property(
    object_name: str,
    modifier_name: str,
    property: str,
    value: Any
) -> Dict[str, Any]:
    """Set a modifier property.
    
    Args:
        object_name: Object name
        modifier_name: Modifier name
        property: Property name
        value: Property value
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    # Convert value to appropriate Python literal
    value_str = repr(value)
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    modifier = obj.modifiers.get("{modifier_name}")
    if not modifier:
        result["status"] = "error"
        result["error"] = f"Modifier not found: {modifier_name}"
    else:
        # Set property
        setattr(modifier, "{property}", {value_str})
        
        result["data"]["modifier"] = {{
            "name": modifier.name,
            "property": "{property}",
            "value": getattr(modifier, "{property}")
        }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def apply_modifier(
    object_name: str,
    modifier_name: str
) -> Dict[str, Any]:
    """Apply a modifier to the mesh.
    
    Args:
        object_name: Object name
        modifier_name: Modifier name
    
    Returns:
        Application result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj or obj.type != 'MESH':
    result["status"] = "error"
    result["error"] = f"Mesh object not found: {object_name}"
else:
    # Apply modifier
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="{modifier_name}")
    
    result["data"]["applied"] = "{modifier_name}"
    result["data"]["object"] = obj.name
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def boolean_operation(
    target: str,
    operator: str,
    operand: str
) -> Dict[str, Any]:
    """Perform boolean operation between two objects.
    
    Args:
        target: Target object name (result goes here)
        operator: Boolean type (UNION, DIFFERENCE, INTERSECT)
        operand: Operand object name
    
    Returns:
        Boolean operation result
    """
    connector = get_blender_connector()
    
    operator = operator.upper()
    if operator not in ["UNION", "DIFFERENCE", "INTERSECT"]:
        return {
            "status": "error",
            "error": f"Invalid operator: {operator}. Use UNION, DIFFERENCE, or INTERSECT"
        }
    
    code = f"""
import bpy

target_obj = bpy.data.objects.get("{target}")
operand_obj = bpy.data.objects.get("{operand}")

if not target_obj or target_obj.type != 'MESH':
    result["status"] = "error"
    result["error"] = f"Target mesh not found: {target}"
elif not operand_obj or operand_obj.type != 'MESH':
    result["status"] = "error"
    result["error"] = f"Operand mesh not found: {operand}"
else:
    # Add boolean modifier
    bool_mod = target_obj.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.operation = '{operator}'
    bool_mod.object = operand_obj
    
    # Make operand invisible
    operand_obj.hide_set(True)
    
    result["data"]["operation"] = "{operator}"
    result["data"]["target"] = target_obj.name
    result["data"]["operand"] = operand_obj.name
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def add_subdivision(
    object_name: str,
    levels: int = 2,
    render_levels: Optional[int] = None
) -> Dict[str, Any]:
    """Add subdivision surface modifier.
    
    Args:
        object_name: Object name
        levels: Viewport subdivision levels
        render_levels: Render subdivision levels (defaults to levels)
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    render = render_levels or levels
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj or obj.type != 'MESH':
    result["status"] = "error"
    result["error"] = f"Mesh not found: {object_name}"
else:
    # Add subdivision modifier
    mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    mod.levels = {levels}
    mod.render_levels = {render}
    
    result["data"]["modifier"] = {{
        "name": mod.name,
        "type": mod.type,
        "levels": mod.levels,
        "render_levels": mod.render_levels
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def add_array(
    object_name: str,
    count: int = 2,
    offset: List[float] = None
) -> Dict[str, Any]:
    """Add array modifier.
    
    Args:
        object_name: Object name
        count: Number of copies
        offset: [x, y, z] offset between copies
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    off = offset or [1.0, 0.0, 0.0]
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj or obj.type != 'MESH':
    result["status"] = "error"
    result["error"] = f"Mesh not found: {object_name}"
else:
    # Add array modifier
    mod = obj.modifiers.new(name="Array", type='ARRAY')
    mod.count = {count}
    mod.relative_offset_displace[0] = {off[0]}
    mod.relative_offset_displace[1] = {off[1]}
    mod.relative_offset_displace[2] = {off[2]}
    
    result["data"]["modifier"] = {{
        "name": mod.name,
        "type": mod.type,
        "count": mod.count,
        "offset": [{off[0]}, {off[1]}, {off[2]}]
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def add_bevel(
    object_name: str,
    width: float = 0.1,
    segments: int = 4
) -> Dict[str, Any]:
    """Add bevel modifier.
    
    Args:
        object_name: Object name
        width: Bevel width
        segments: Number of bevel segments
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj or obj.type != 'MESH':
    result["status"] = "error"
    result["error"] = f"Mesh not found: {object_name}"
else:
    # Add bevel modifier
    mod = obj.modifiers.new(name="Bevel", type='BEVEL')
    mod.width = {width}
    mod.segments = {segments}
    
    result["data"]["modifier"] = {{
        "name": mod.name,
        "type": mod.type,
        "width": mod.width,
        "segments": mod.segments
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def add_mirror(
    object_name: str,
    axis: str = "X",
    bisect: bool = True
) -> Dict[str, Any]:
    """Add mirror modifier.
    
    Args:
        object_name: Object name
        axis: Mirror axis (X, Y, or Z)
        bisect: Enable bisect
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    axis = axis.upper()
    if axis not in ["X", "Y", "Z"]:
        return {
            "status": "error",
            "error": f"Invalid axis: {axis}. Use X, Y, or Z"
        }
    
    axis_map = {"X": 0, "Y": 1, "Z": 2}
    axis_idx = axis_map[axis]
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj or obj.type != 'MESH':
    result["status"] = "error"
    result["error"] = f"Mesh not found: {object_name}"
else:
    # Add mirror modifier
    mod = obj.modifiers.new(name="Mirror", type='MIRROR')
    mod.use_axis[0] = {str(axis_idx == 0).lower()}
    mod.use_axis[1] = {str(axis_idx == 1).lower()}
    mod.use_axis[2] = {str(axis_idx == 2).lower()}
    mod.use_bisect_axis[0] = {str(bisect and axis_idx == 0).lower()}
    mod.use_bisect_axis[1] = {str(bisect and axis_idx == 1).lower()}
    mod.use_bisect_axis[2] = {str(bisect and axis_idx == 2).lower()}
    
    result["data"]["modifier"] = {{
        "name": mod.name,
        "type": mod.type,
        "axis": "{axis}",
        "bisect": {bisect}
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def list_modifiers(object_name: str) -> Dict[str, Any]:
    """List all modifiers on an object.
    
    Args:
        object_name: Object name
    
    Returns:
        List of modifiers
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj:
    result["status"] = "error"
    result["error"] = f"Object not found: {object_name}"
else:
    modifiers = []
    for mod in obj.modifiers:
        modifiers.append({{
            "name": mod.name,
            "type": mod.type,
            "show_viewport": mod.show_viewport,
            "show_render": mod.show_render
        }})
    
    result["data"]["modifiers"] = modifiers
    result["data"]["count"] = len(modifiers)
"""
    
    return connector.execute_bpy(code)
