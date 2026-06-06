"""Light tools for UBM MCP Server"""
from typing import Any, Dict, List, Optional, Tuple
import logging

from ..mcp_server import mcp, get_blender_connector

logger = logging.getLogger(__name__)


@mcp.tool()
def add_light(
    type: str,
    name: Optional[str] = None,
    location: Tuple[float, float, float] = (0.0, 0.0, 5.0),
    energy: float = 10.0,
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
) -> Dict[str, Any]:
    """Add a light to the scene.
    
    Args:
        type: Light type (SUN, AREA, POINT, SPOT)
        name: Optional light name
        location: [x, y, z] location
        energy: Light energy (brightness)
        color: [r, g, b] color values (0-1)
    
    Returns:
        Light creation result
    """
    # Validate type
    valid_types = ["SUN", "AREA", "POINT", "SPOT"]
    type_upper = type.upper()
    if type_upper not in valid_types:
        return {
            "status": "error",
            "error": f"Invalid light type: {type}. Valid: {', '.join(valid_types)}"
        }
    
    connector = get_blender_connector()
    light_name = name or f"{type.capitalize()}_Light"
    
    code = f"""
import bpy

# Create light data
light_data = bpy.data.lights.new(name="{light_name}_Data", type="{type_upper}")
light_data.energy = {energy}
light_data.color = ({color[0]}, {color[1]}, {color[2]})

# Create light object
light_obj = bpy.data.objects.new(name="{light_name}", object_data=light_data)
bpy.context.collection.objects.link(light_obj)

# Set location
light_obj.location = ({location[0]}, {location[1]}, {location[2]})

# Store result
result["data"]["light"] = {{
    "name": light_obj.name,
    "type": light_data.type,
    "energy": light_data.energy,
    "color": list(light_data.color),
    "location": list(light_obj.location)
}}

# Make active
bpy.context.view_layer.objects.active = light_obj
"""
    
    result = connector.execute_bpy(code)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "name": light_name,
            "type": type_upper,
            "location": list(location),
            "energy": energy,
            "color": list(color),
            "data": result.get("data", {})
        }
    else:
        return result


@mcp.tool()
def set_light_properties(
    name: str,
    energy: Optional[float] = None,
    color: Optional[Tuple[float, float, float]] = None,
    location: Optional[Tuple[float, float, float]] = None
) -> Dict[str, Any]:
    """Update light properties.
    
    Args:
        name: Light object name
        energy: New energy value
        color: New [r, g, b] color
        location: New [x, y, z] location
    
    Returns:
        Update result
    """
    if not any([energy, color, location]):
        return {
            "status": "error",
            "error": "At least one property must be provided"
        }
    
    connector = get_blender_connector()
    
    # Build property updates
    updates = []
    if energy is not None:
        updates.append(f'light_data.energy = {energy}')
    if color is not None:
        updates.append(f'light_data.color = ({color[0]}, {color[1]}, {color[2]})')
    if location is not None:
        updates.append(f'light_obj.location = ({location[0]}, {location[1]}, {location[2]})')
    
    code = f"""
import bpy

# Find light object
light_obj = bpy.data.objects.get("{name}")
if not light_obj:
    result["status"] = "error"
    result["error"] = f"Light not found: {name}"
else:
    light_data = light_obj.data
    
    # Apply updates
    {chr(10).join('    ' + u for u in updates)}
    
    # Store result
    result["data"]["light"] = {{
        "name": light_obj.name,
        "energy": light_data.energy,
        "color": list(light_data.color),
        "location": list(light_obj.location)
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def delete_light(name: str) -> Dict[str, Any]:
    """Delete a light from the scene.
    
    Args:
        name: Light object name
    
    Returns:
        Deletion result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

# Find light object
light_obj = bpy.data.objects.get("{name}")
if not light_obj:
    result["status"] = "error"
    result["error"] = f"Light not found: {name}"
else:
    light_data = light_obj.data
    
    # Remove object
    bpy.data.objects.remove(light_obj, do_unlink=True)
    
    # Remove light data
    if light_data and light_data.users == 0:
        bpy.data.lights.remove(light_data)
    
    result["data"]["deleted"] = "{name}"
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def list_lights() -> Dict[str, Any]:
    """List all lights in the scene.
    
    Returns:
        List of lights with properties
    """
    connector = get_blender_connector()
    
    code = """
import bpy

lights = []
for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT' and obj.data:
        light_data = obj.data
        lights.append({
            "name": obj.name,
            "type": light_data.type,
            "energy": light_data.energy,
            "color": [round(c, 4) for c in light_data.color],
            "location": [round(x, 4) for x in obj.location]
        })

result["data"]["lights"] = lights
result["data"]["count"] = len(lights)
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def setup_three_point_lighting(
    key_location: Tuple[float, float, float] = (5.0, 5.0, 5.0),
    fill_location: Tuple[float, float, float] = (-3.0, 2.0, 3.0),
    rim_location: Tuple[float, float, float] = (0.0, -5.0, 4.0)
) -> Dict[str, Any]:
    """Set up classic three-point lighting.
    
    Creates:
    - Key light (main light, high energy)
    - Fill light (soft fill, medium energy)
    - Rim light (backlight, medium energy)
    
    Args:
        key_location: Key light position
        fill_location: Fill light position
        rim_location: Rim light position
    
    Returns:
        Lighting setup result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

lights_created = []

# Key light (main)
key_data = bpy.data.lights.new(name="Key_Light_Data", type="AREA")
key_data.energy = 1000
key_obj = bpy.data.objects.new(name="Key_Light", object_data=key_data)
bpy.context.collection.objects.link(key_obj)
key_obj.location = ({key_location[0]}, {key_location[1]}, {key_location[2]})
lights_created.append("Key_Light")

# Fill light
fill_data = bpy.data.lights.new(name="Fill_Light_Data", type="AREA")
fill_data.energy = 500
fill_obj = bpy.data.objects.new(name="Fill_Light", object_data=fill_data)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = ({fill_location[0]}, {fill_location[1]}, {fill_location[2]})
lights_created.append("Fill_Light")

# Rim light
rim_data = bpy.data.lights.new(name="Rim_Light_Data", type="AREA")
rim_data.energy = 800
rim_obj = bpy.data.objects.new(name="Rim_Light", object_data=rim_data)
bpy.context.collection.objects.link(rim_obj)
rim_obj.location = ({rim_location[0]}, {rim_location[1]}, {rim_location[2]})
lights_created.append("Rim_Light")

result["data"]["lights_created"] = lights_created
result["data"]["setup"] = "three_point"
"""
    
    result = connector.execute_bpy(code)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "setup": "three_point_lighting",
            "lights": result.get("data", {}).get("lights_created", []),
            "key_location": list(key_location),
            "fill_location": list(fill_location),
            "rim_location": list(rim_location)
        }
    else:
        return result
