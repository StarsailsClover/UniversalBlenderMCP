"""Video recording command for UBM"""
import click
import time
import os
from pathlib import Path
from typing import Optional

@click.command()
@click.option('--output', '-o', default='./recording', help='Output video file path')
@click.option('--duration', '-d', default=10, help='Recording duration in seconds')
@click.option('--fps', '-f', default=30, help='Frames per second')
@click.option('--width', '-w', default=1920, help='Video width')
@click.option('--height', '-h', default=1080, help='Video height')
@click.option('--format', default='mp4', help='Video format (mp4, avi, mov)')
def record(output, duration, fps, width, height, format):
    """Record Blender viewport as video"""
    from ..blender.connector import BlenderConnector
    
    output_path = Path(output)
    if output_path.suffix == '':
        output_path = output_path.with_suffix(f'.{format}')
    
    frames_dir = output_path.parent / f"{output_path.stem}_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    click.echo(f"🎥 Video Recording Started")
    click.echo(f"   Duration: {duration}s")
    click.echo(f"   FPS: {fps}")
    click.echo(f"   Resolution: {width}x{height}")
    click.echo(f"   Output: {output_path}")
    click.echo()
    
    # 计算总帧数
    total_frames = duration * fps
    frame_interval = 1.0 / fps
    
    connector = BlenderConnector()
    
    try:
        for frame in range(total_frames):
            progress = (frame + 1) / total_frames * 100
            
            # 显示进度
            bar_length = 30
            filled = int(bar_length * (frame + 1) / total_frames)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            click.echo(f"\r[{bar}] {progress:.1f}% Frame {frame+1}/{total_frames}", nl=False)
            
            # 保存当前帧
            frame_path = frames_dir / f"frame_{frame:04d}.png"
            
            code = f"""
import bpy
scene = bpy.context.scene
scene.render.resolution_x = {width}
scene.render.resolution_y = {height}
scene.render.filepath = r"{frame_path}"
bpy.ops.render.render(write_still=True)
"""
            
            result = connector.execute_bpy(code, timeout=10)
            
            if result.get("status") != "success":
                click.echo(f"\n⚠️  Frame {frame} failed: {result.get('error')}")
            
            time.sleep(frame_interval)
            
        click.echo()  # 换行
        click.echo()
        click.echo("✅ Frames captured")
        
        # 编码视频
        click.echo("🎬 Encoding video...")
        
        # 使用 ffmpeg 或 Blender 的 Video Sequence Editor
        try:
            video_path = _encode_video(frames_dir, output_path, fps, format)
            click.echo(f"✅ Video saved: {video_path}")
            click.echo(f"   Duration: {duration}s")
            click.echo(f"   Frames: {total_frames}")
            
            # 清理帧文件（可选）
            # import shutil
            # shutil.rmtree(frames_dir)
            
        except Exception as e:
            click.echo(f"⚠️  Video encoding failed: {e}")
            click.echo(f"   Raw frames saved to: {frames_dir}")
            click.echo(f"   You can encode manually using ffmpeg")
            
    except KeyboardInterrupt:
        click.echo("\n⏹ Recording stopped by user")
        
def _encode_video(frames_dir: Path, output_path: Path, fps: int, format: str) -> Path:
    """使用 ffmpeg 编码视频"""
    import subprocess
    
    # 检查 ffmpeg 是否可用
    ffmpeg_check = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True
    )
    
    if ffmpeg_check.returncode != 0:
        raise RuntimeError("ffmpeg not found. Install ffmpeg to encode video.")
    
    # 构建 ffmpeg 命令
    input_pattern = str(frames_dir / "frame_%04d.png")
    
    codec_map = {
        'mp4': 'libx264',
        'avi': 'mpeg4',
        'mov': 'libx264'
    }
    
    codec = codec_map.get(format, 'libx264')
    
    cmd = [
        "ffmpeg",
        "-y",  # 覆盖输出文件
        "-framerate", str(fps),
        "-i", input_pattern,
        "-c:v", codec,
        "-pix_fmt", "yuv420p",
        "-crf", "18",  # 高质量
        str(output_path)
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    
    return output_path


@click.command()
@click.argument('frames_dir')
@click.option('--output', '-o', required=True, help='Output video file')
@click.option('--fps', '-f', default=30, help='Frames per second')
def encode(frames_dir, output, fps):
    """Encode frames to video using ffmpeg"""
    try:
        output_path = _encode_video(Path(frames_dir), Path(output), fps, Path(output).suffix[1:])
        click.echo(f"✅ Video encoded: {output_path}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}")
