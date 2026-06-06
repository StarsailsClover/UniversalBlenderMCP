"""Material node editing tools for UBM MCP Server"""
from typing import Any, Dict, List, Optional, Tuple

from ..mcp_server import mcp, get_blender_connector


@mcp.tool()
def create_material_with_nodes(
    name: str,
    use_nodes: bool = True
) -> Dict[str, Any]:
    """Create a new material with node setup.
    
    Args:
        name: Material name
        use_nodes: Enable node tree
    
    Returns:
        Material creation result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

# Create material
mat = bpy.data.materials.new(name="{name}")
mat.use_nodes = {str(use_nodes).lower()}

if {str(use_nodes).lower()}:
    # Clear default nodes
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Add Material Output
    output_node = nodes.new('ShaderNodeOutputMaterial')
    output_node.location = (300, 0)
    
    # Add Principled BSDF
    bsdf_node = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf_node.location = (0, 0)
    
    # Link nodes
    links = mat.node_tree.links
    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    result["data"]["material"] = {{
        "name": mat.name,
        "use_nodes": mat.use_nodes,
        "nodes_count": len(nodes.nodes)
    }}
else:
    result["data"]["material"] = {{
        "name": mat.name,
        "use_nodes": mat.use_nodes
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def add_node(
    material_name: str,
    node_type: str,
    name: Optional[str] = None,
    location: List[float] = None
) -> Dict[str, Any]:
    """Add a node to material node tree.
    
    Args:
        material_name: Material name
        node_type: Node type (e.g., 'ShaderNodeBsdfPrincipled')
        name: Optional node name
        location: [x, y] node location
    
    Returns:
        Node addition result
    """
    connector = get_blender_connector()
    
    loc = location or [0, 0]
    node_name = name or node_type.split('_')[-1]
    
    code = f"""
import bpy

mat = bpy.data.materials.get("{material_name}")
if not mat:
    result["status"] = "error"
    result["error"] = f"Material not found: {material_name}"
elif not mat.use_nodes:
    result["status"] = "error"
    result["error"] = f"Material does not use nodes: {material_name}"
else:
    nodes = mat.node_tree.nodes
    node = nodes.new("{node_type}")
    if "{node_name}":
        node.name = "{node_name}"
    node.location = ({loc[0]}, {loc[1]})
    
    result["data"]["node"] = {{
        "name": node.name,
        "type": node.type,
        "bl_idname": node.bl_idname,
        "location": list(node.location)
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def connect_nodes(
    material_name: str,
    from_node: str,
    from_socket: str,
    to_node: str,
    to_socket: str
) -> Dict[str, Any]:
    """Connect two nodes in material node tree.
    
    Args:
        material_name: Material name
        from_node: Source node name
        from_socket: Source socket name
        to_node: Target node name
        to_socket: Target socket name
    
    Returns:
        Connection result
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

mat = bpy.data.materials.get("{material_name}")
if not mat or not mat.use_nodes:
    result["status"] = "error"
    result["error"] = f"Material not found or nodes disabled: {material_name}"
else:
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Find nodes
    from_n = nodes.get("{from_node}")
    to_n = nodes.get("{to_node}")
    
    if not from_n:
        result["status"] = "error"
        result["error"] = f"Source node not found: {from_node}"
    elif not to_n:
        result["status"] = "error"
        result["error"] = f"Target node not found: {to_node}"
    else:
        # Find sockets
        from_sock = from_n.outputs.get("{from_socket}")
        to_sock = to_n.inputs.get("{to_socket}")
        
        if not from_sock:
            result["status"] = "error"
            result["error"] = f"Source socket not found: {from_socket}"
        elif not to_sock:
            result["status"] = "error"
            result["error"] = f"Target socket not found: {to_socket}"
        else:
            # Create link
            link = links.new(from_sock, to_sock)
            
            result["data"]["link"] = {{
                "from_node": from_n.name,
                "from_socket": "{from_socket}",
                "to_node": to_n.name,
                "to_socket": "{to_socket}"
            }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def set_node_property(
    material_name: str,
    node_name: str,
    property: str,
    value: Any
) -> Dict[str, Any]:
    """Set a node property value.
    
    Args:
        material_name: Material name
        node_name: Node name
        property: Property name (e.g., 'inputs[0].default_value')
        value: Property value
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    value_str = repr(value)
    
    code = f"""
import bpy

mat = bpy.data.materials.get("{material_name}")
if not mat or not mat.use_nodes:
    result["status"] = "error"
    result["error"] = f"Material not found or nodes disabled: {material_name}"
else:
    node = mat.node_tree.nodes.get("{node_name}")
    if not node:
        result["status"] = "error"
        result["error"] = f"Node not found: {node_name}"
    else:
        # Set property using exec for complex paths
        exec(f"node.{property} = {value_str}")
        
        result["data"]["node"] = {{
            "name": node.name,
            "property": "{property}",
            "value": eval(f"node.{property}")
        }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def set_principled_properties(
    material_name: str,
    base_color: Optional[Tuple[float, float, float, float]] = None,
    metallic: Optional[float] = None,
    roughness: Optional[float] = None,
    subsurface: Optional[float] = None,
    emission: Optional[Tuple[float, float, float, float]] = None
) -> Dict[str, Any]:
    """Set multiple properties on Principled BSDF node.
    
    Args:
        material_name: Material name
        base_color: [r, g, b, a]
        metallic: Metallic value (0-1)
        roughness: Roughness value (0-1)
        subsurface: Subsurface value
        emission: [r, g, b, a] emission color
    
    Returns:
        Result
    """
    connector = get_blender_connector()
    
    # Build property updates
    updates = []
    if base_color:
        updates.append(f'inputs["Base Color"].default_value = {list(base_color)}')
    if metallic is not None:
        updates.append(f'inputs["Metallic"].default_value = {metallic}')
    if roughness is not None:
        updates.append(f'inputs["Roughness"].default_value = {roughness}')
    if subsurface is not None:
        updates.append(f'inputs["Subsurface"].default_value = {subsurface}')
    if emission:
        updates.append(f'inputs["Emission"].default_value = {list(emission)}')
    
    if not updates:
        return {
            "status": "error",
            "error": "At least one property must be provided"
        }
    
    code = f"""
import bpy

mat = bpy.data.materials.get("{material_name}")
if not mat or not mat.use_nodes:
    result["status"] = "error"
    result["error"] = f"Material not found or nodes disabled: {material_name}"
else:
    # Find Principled BSDF node
    bsdf = None
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break
    
    if not bsdf:
        result["status"] = "error"
        result["error"] = "Principled BSDF node not found"
    else:
        # Apply updates
        {chr(10).join('        ' + u for u in updates)}
        
        result["data"]["node"] = {{
            "name": bsdf.name,
            "type": bsdf.type
        }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def add_texture_image(
    material_name: str,
    image_path: str,
    node_name: str = "Image Texture",
    connect_to_color: bool = True
) -> Dict[str, Any]:
    """Add an image texture node to material.
    
    Args:
        material_name: Material name
        image_path: Path to image file
        node_name: Node name
        connect_to_color: Auto-connect to base color
    
    Returns:
        Result
    """
    import os
    if not os.path.exists(image_path):
        return {
            "status": "error",
            "error": f"Image not found: {image_path}"
        }
    
    connector = get_blender_connector()
    
    code = f"""
import bpy
import os

mat = bpy.data.materials.get("{material_name}")
if not mat or not mat.use_nodes:
    result["status"] = "error"
    result["error"] = f"Material not found or nodes disabled: {material_name}"
else:
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Load image
    img = bpy.data.images.load(r"{image_path}")
    
    # Create image texture node
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.name = "{node_name}"
    tex_node.image = img
    tex_node.location = (-300, 0)
    
    if {str(connect_to_color).lower()}:
        # Find Principled BSDF and connect
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                links.new(tex_node.outputs['Color'], node.inputs['Base Color'])
                break
    
    result["data"]["node"] = {{
        "name": tex_node.name,
        "type": tex_node.type,
        "image": img.name
    }}
"""
    
    return connector.execute_bpy(code)


@mcp.tool()
def list_material_nodes(material_name: str) -> Dict[str, Any]:
    """List all nodes in a material.
    
    Args:
        material_name: Material name
    
    Returns:
        List of nodes
    """
    connector = get_blender_connector()
    
    code = f"""
import bpy

mat = bpy.data.materials.get("{material_name}")
if not mat:
    result["status"] = "error"
    result["error"] = f"Material not found: {material_name}"
elif not mat.use_nodes:
    result["status"] = "error"
    result["error"] = f"Material does not use nodes: {material_name}"
else:
    nodes = []
    for node in mat.node_tree.nodes:
        nodes.append({{
            "name": node.name,
            "type": node.type,
            "bl_idname": node.bl_idname,
            "location": list(node.location)
        }})
    
    result["data"]["nodes"] = nodes
    result["data"]["count"] = len(nodes)
"""
    
    return connector.execute_bpy(code)
