"""Watch mode - Real-time Blender monitoring"""
import click
import time
import json
from pathlib import Path
from typing import Optional

@click.command()
@click.option('--interval', '-i', default=2, help='Screenshot interval in seconds')
@click.option('--output', '-o', default='./watch_output', help='Output directory')
@click.option('--duration', '-d', default=60, help='Duration in seconds')
def watch(interval, output, duration):
    """Watch Blender scene in real-time"""
    from ..blender.connector import BlenderConnector
    from ..server.mcp_server import capture_viewport
    
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    click.echo(f"👁️  Watch mode started")
    click.echo(f"   Interval: {interval}s")
    click.echo(f"   Duration: {duration}s")
    click.echo(f"   Output: {output_path}")
    click.echo()
    
    start_time = time.time()
    frame = 0
    
    try:
        while time.time() - start_time < duration:
            frame += 1
            timestamp = time.strftime("%H%M%S")
            screenshot_path = output_path / f"frame_{frame:04d}_{timestamp}.png"
            
            click.echo(f"📸 Frame {frame:04d}...", nl=False)
            
            result = capture_viewport(
                output_path=str(screenshot_path),
                width=1280,
                height=720
            )
            
            if not result.startswith("Error"):
                click.echo(f" ✓ {screenshot_path.name}")
            else:
                click.echo(f" ✗ {result}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        click.echo("\n⏹ Stopped by user")
    
    click.echo()
    click.echo(f"✅ Captured {frame} frames")
    click.echo(f"📁 Saved to: {output_path}")
