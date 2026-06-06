"""UBM CLI - Command line interface for Universal Blender MCP"""
import click
import asyncio
from pathlib import Path

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
    from .mcp_server import mcp
    
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
    click.echo(f"  Location: {location}")
    click.echo(f"  Size: {size}")
    if name:
        click.echo(f"  Name: {name}")
    
    # TODO: Call MCP tool
    click.echo("Done (placeholder)")


@cli.command()
@click.argument('name')
def delete(name):
    """Delete an object"""
    click.echo(f"Deleting {name}...")
    # TODO: Call MCP tool
    click.echo("Done (placeholder)")


@cli.command()
@click.option('--output', '-o', help='Output path')
@click.option('--width', '-w', default=1920, help='Width')
@click.option('--height', '-h', default=1080, help='Height')
@click.option('--rust', is_flag=True, default=True, help='Use Rust screenshot')
def capture(output, width, height, rust):
    """Capture Blender viewport"""
    click.echo(f"Capturing viewport {width}x{height}...")
    if rust:
        click.echo("Using Rust native screenshot")
    # TODO: Call MCP tool
    click.echo("Done (placeholder)")


@cli.command()
def status():
    """Check UBM and Blender status"""
    click.echo("Checking status...")
    click.echo()
    
    # Check UBM
    click.echo("UBM:")
    click.echo(f"  Version: 0.1.0")
    click.echo(f"  Status: Ready")
    
    # Check Blender
    click.echo()
    click.echo("Blender:")
    click.echo(f"  Detected: Not implemented")
    click.echo(f"  Addon: Not implemented")


@cli.command()
def info():
    """Get server information"""
    from .mcp_server import get_server_info
    
    info = get_server_info()
    click.echo(f"Name: {info['name']}")
    click.echo(f"Version: {info['version']}")
    click.echo(f"Description: {info['description']}")
    click.echo()
    click.echo("Capabilities:")
    for cap in info['capabilities']:
        click.echo(f"  - {cap}")


def main():
    """Entry point"""
    cli()


if __name__ == "__main__":
    main()
