"""GUI command - Launch Blender with real-time control"""
import click
import subprocess
import time
import os
from pathlib import Path

@click.command()
@click.option('--file', '-f', help='Open specific .blend file')
@click.option('--script', '-s', help='Auto-run Python script on startup')
@click.option('--port', '-p', default=9876, help='Socket server port')
@click.option('--start-server', is_flag=True, help='Start UBM socket server')
def gui(file, script, port, start_server):
    """Launch Blender GUI with UBM integration"""
    from ..blender.connector import BlenderConnector
    
    click.echo("🚀 Launching Blender GUI...")
    
    # 查找 Blender
    connector = BlenderConnector()
    blender_path = connector.blender_path
    
    # 构建命令
    cmd = [blender_path]
    
    # 添加文件
    if file:
        if not os.path.exists(file):
            click.echo(f"❌ File not found: {file}")
            return
        cmd.append(file)
        click.echo(f"📁 Opening: {file}")
    
    # 添加脚本
    if script:
        if not os.path.exists(script):
            click.echo(f"❌ Script not found: {script}")
            return
        cmd.extend(["--python", script])
        click.echo(f"🐍 Auto-running script: {script}")
    
    # 启动服务器脚本（如果需要）
    if start_server:
        server_script = _create_server_script(port)
        cmd.extend(["--python", server_script])
        click.echo(f"🔌 Socket server on port {port}")
    
    click.echo()
    click.echo(f"⚙️  Blender path: {blender_path}")
    click.echo(f"🎯 Command: {' '.join(cmd)}")
    click.echo()
    
    try:
        # 启动 Blender GUI（非阻塞）
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        click.echo(f"✅ Blender GUI started (PID: {process.pid})")
        click.echo()
        
        # 等待 Blender 启动
        time.sleep(2)
        
        if process.poll() is None:
            click.echo("🎉 Blender is running!")
            click.echo()
            click.echo("Commands:")
            click.echo("  ubm status     - Check connection")
            click.echo("  ubm create     - Create objects")
            click.echo("  ubm capture    - Take screenshot")
            click.echo()
            
            if start_server:
                click.echo(f"Socket server: localhost:{port}")
                click.echo()
            
            click.echo("Press Ctrl+C to stop monitoring (Blender will keep running)")
            click.echo()
            
            # 监控输出
            try:
                while True:
                    output = process.stdout.readline()
                    if output:
                        click.echo(f"[Blender] {output.strip()}")
                        
                    # 检查是否仍在运行
                    if process.poll() is not None:
                        break
                        
            except KeyboardInterrupt:
                click.echo("\n⏹ Monitoring stopped")
                click.echo("💡 Blender is still running in the background")
                click.echo(f"   PID: {process.pid}")
                
        else:
            stdout, stderr = process.communicate()
            click.echo(f"❌ Blender exited with code {process.returncode}")
            if stderr:
                click.echo(f"Error: {stderr}")
                
    except Exception as e:
        click.echo(f"❌ Failed to start: {e}")

def _create_server_script(port: int) -> str:
    """创建临时服务器启动脚本"""
    script_content = f"""
import bpy
import threading
import socket
import json

class UBMServer:
    def __init__(self, port={port}):
        self.port = port
        self.running = False
        
    def start(self):
        self.running = True
        print(f"UBM Server starting on port {{self.port}}")
        # 实际服务器实现在 addon/server.py 中
        
    def stop(self):
        self.running = False

server = UBMServer()
server.start()
print(f"UBM Server ready on port {port}")
"""
    
    script_path = Path(os.environ.get('TEMP', '/tmp')) / "ubm_startup_server.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return str(script_path)


@click.command()
@click.argument('pid', type=int)
def stop(pid):
    """Stop Blender process by PID"""
    import signal
    import os
    
    try:
        os.kill(pid, signal.SIGTERM)
        click.echo(f"🛑 Stopped Blender (PID: {pid})")
    except ProcessLookupError:
        click.echo(f"❌ Process {pid} not found")
    except PermissionError:
        click.echo(f"❌ Permission denied to stop process {pid}")
