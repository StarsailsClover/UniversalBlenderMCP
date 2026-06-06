"""UBM CLI - Command line interface for Universal Blender MCP"""
import click
import asyncio
import json
from pathlib import Path
from typing import Optional

# Import MCP server tools
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from server.mcp_server import (
    create_primitive,
    delete_object,
    transform_object,
    get_scene_info,
    list_objects,
    set_material_color,
    capture_viewport,
    get_server_info
)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Universal Blender MCP - CLI Tool
    
    Universal MCP server for Blender with Rust screenshot capabilities.
    Used alongside Link2Blender.skill to enable AI Agents to create 3D models.
    """
    pass


@cli.command()
@click.option('--port', '-p', default=9876, help='Server port')
@click.option('--stdio', is_flag=True, help='Use stdio transport (for Claude Desktop)')
@click.option('--tcp', is_flag=True, help='Use TCP transport')
def serve(port, stdio, tcp):
    """Start the MCP Server"""
    from server.mcp_server import mcp
    
    click.echo(f"Starting UBM server...")
    
    if stdio:
        click.echo("Using stdio transport (for Claude Desktop)")
        mcp.run()
    elif tcp:
        click.echo(f"Using TCP transport on port {port}")
        # TODO: Implement TCP mode
        click.echo("TCP mode not yet implemented")
    else:
        click.echo("Using default transport")
        mcp.run()


@cli.command()
@click.option('--type', '-t', required=True, 
              type=click.Choice(['CUBE', 'SPHERE', 'CYLINDER', 'CONE', 'PLANE']),
              help='Primitive type')
@click.option('--name', '-n', help='Object name')
@click.option('--location', '-l', nargs=3, type=float, default=(0, 0, 0), 
              help='Location x y z')
@click.option('--size', '-s', default=1.0, help='Size')
def create(type, name, location, size):
    """Create a primitive object"""
    click.echo(f"Creating {type}...")
    
    try:
        result = create_primitive(
            type=type,
            name=name,
            location=location,
            size=size
        )
        
        if result.get("status") == "success":
            click.echo(f"✓ Created {result['name']} ({result['type']})")
            click.echo(f"  Location: {result['location']}")
            click.echo(f"  Size: {result['size']}")
        else:
            click.echo(f"✗ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        click.echo(f"✗ Failed: {e}")


@cli.command()
@click.argument('name')
def delete(name):
    """Delete an object"""
    click.echo(f"Deleting {name}...")
    
    try:
        result = delete_object(name=name)
        
        if result.get("status") == "success":
            click.echo(f"✓ Deleted {name}")
        else:
            click.echo(f"✗ Error: {result.get('error')}")
            
    except Exception as e:
        click.echo(f"✗ Failed: {e}")


@cli.command()
@click.argument('name')
@click.option('--location', '-l', nargs=3, type=float, help='New location x y z')
@click.option('--rotation', '-r', nargs=3, type=float, help='New rotation x y z (radians)')
@click.option('--scale', '-s', nargs=3, type=float, help='New scale x y z')
def transform(name, location, rotation, scale):
    """Transform an object"""
    if not any([location, rotation, scale]):
        click.echo("Error: At least one of --location, --rotation, or --scale must be provided")
        return
    
    click.echo(f"Transforming {name}...")
    
    try:
        result = transform_object(
            name=name,
            location=tuple(location) if location else None,
            rotation=tuple(rotation) if rotation else None,
            scale=tuple(scale) if scale else None
        )
        
        if result.get("status") == "success":
            click.echo(f"✓ Transformed {name}")
            obj = result.get("data", {}).get("object", {})
            click.echo(f"  Location: {obj.get('location')}")
            click.echo(f"  Rotation: {obj.get('rotation')}")
            click.echo(f"  Scale: {obj.get('scale')}")
        else:
            click.echo(f"✗ Error: {result.get('error')}")
            
    except Exception as e:
        click.echo(f"✗ Failed: {e}")


@cli.command()
def scene():
    """Get scene information"""
    click.echo("Getting scene info...")
    
    try:
        result = get_scene_info()
        
        if result.get("status") == "success":
            scene_data = result.get("data", {}).get("scene", {})
            click.echo(f"\nScene: {scene_data.get('name')}")
            click.echo(f"Objects: {scene_data.get('objects_count')}")
            click.echo(f"Frame: {scene_data.get('frame_current')}")
            click.echo(f"Resolution: {scene_data.get('resolution')}")
            click.echo(f"Engine: {scene_data.get('render_engine')}")
        else:
            click.echo(f"✗ Error: {result.get('error')}")
            
    except Exception as e:
        click.echo(f"✗ Failed: {e}")


@cli.command()
def list():
    """List all objects in scene"""
    click.echo("Listing objects...")
    
    try:
        result = list_objects()
        
        if result.get("status") == "success":
            objects = result.get("data", {}).get("objects", [])
            count = result.get("data", {}).get("count", 0)
            
            click.echo(f"\nFound {count} objects:\n")
            click.echo(f"{'Name':<20} {'Type':<15} {'Location':<30}")
            click.echo("-" * 65)
            
            for obj in objects:
                loc = obj.get('location', [0, 0, 0])
                loc_str = f"({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f})"
                click.echo(f"{obj['name']:<20} {obj['type']:<15} {loc_str:<30}")
        else:
            click.echo(f"✗ Error: {result.get('error')}")
            
    except Exception as e:
        click.echo(f"✗ Failed: {e}")


@cli.command()
@click.argument('object_name')
@click.option('--color', '-c', nargs=4, type=float, default=(0.8, 0.2, 0.2, 1.0),
              help='Color r g b a (0-1)')
@click.option('--material', '-m', help='Material name')
def material(object_name, color, material):
    """Set object material color"""
    click.echo(f"Setting material for {object_name}...")
    
    try:
        result = set_material_color(
            object_name=object_name,
            color=tuple(color),
            material_name=material
        )
        
        if result.get("status") == "success":
            mat = result.get("data", {}).get("material", {})
            click.echo(f"✓ Material set: {mat.get('name')}")
            click.echo(f"  Color: {mat.get('color')}")
        else:
            click.echo(f"✗ Error: {result.get('error')}")
            
    except Exception as e:
        click.echo(f"✗ Failed: {e}")


@cli.command()
@click.option('--output', '-o', help='Output path')
@click.option('--width', '-w', default=1920, help='Width')
@click.option('--height', '-h', default=1080, help='Height')
def capture(output, width, height):
    """Capture Blender viewport"""
    click.echo(f"Capturing viewport {width}x{height}...")
    
    try:
        result = capture_viewport(
            output_path=output,
            width=width,
            height=height
        )
        
        if result.startswith("Error:"):
            click.echo(f"✗ {result}")
        else:
            click.echo(f"✓ Screenshot saved: {result}")
            
    except Exception as e:
        click.echo(f"✗ Failed: {e}")


@cli.command()
def status():
    """Check UBM and Blender status"""
    click.echo("Checking status...\n")
    
    # Check UBM
    click.echo("UBM:")
    click.echo(f"  Version: 0.1.0")
    click.echo(f"  Status: Ready")
    
    # Try to get scene info to check Blender connection
    click.echo("\nBlender:")
    try:
        result = get_scene_info()
        if result.get("status") == "success":
            scene = result.get("data", {}).get("scene", {})
            click.echo(f"  Status: Connected ✓")
            click.echo(f"  Scene: {scene.get('name')}")
            click.echo(f"  Objects: {scene.get('objects_count')}")
        else:
            click.echo(f"  Status: Error")
            click.echo(f"  Error: {result.get('error')}")
    except Exception as e:
        click.echo(f"  Status: Not connected")
        click.echo(f"  Error: {e}")


@cli.command()
def info():
    """Get server information"""
    info = get_server_info()
    click.echo(f"Name: {info['name']}")
    click.echo(f"Version: {info['version']}")
    click.echo(f"Description: {info['description']}")
    click.echo()
    click.echo("Capabilities:")
    for cap in info['capabilities']:
        click.echo(f"  - {cap}")
    click.echo()
    click.echo("Tools:")
    from server.mcp_server import list_available_tools
    for tool in list_available_tools():
        click.echo(f"  - {tool}")


def main():
    """Entry point"""
    cli()


if __name__ == "__main__":
    main()
