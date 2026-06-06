"""Rust bridge - Python interface to Rust screenshot module"""
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import Rust module
try:
    from .ubm_rust import (
        capture_viewport,
        is_blender_running,
        list_blender_windows,
        get_window_rect
    )
    RUST_AVAILABLE = True
    logger.info("Rust module loaded successfully")
except ImportError as e:
    RUST_AVAILABLE = False
    logger.warning(f"Rust module not available: {e}")
    
    # Define fallback functions
    def capture_viewport(output_path: Optional[str], width: int, height: int) -> str:
        """Fallback - use Blender render instead"""
        raise NotImplementedError(
            "Rust screenshot not available. "
            "Please build with: cd rust && cargo build --release"
        )
    
    def is_blender_running() -> bool:
        """Fallback - check using Python"""
        import subprocess
        try:
            result = subprocess.run(
                ["pgrep", "-x", "blender"],
                capture_output=True
            )
            return result.returncode == 0
        except:
            return False
    
    def list_blender_windows() -> List[Tuple[int, str]]:
        """Fallback - not available without Rust"""
        return []
    
    def get_window_rect(window_id: int) -> Tuple[int, int, int, int]:
        """Fallback - not available without Rust"""
        raise NotImplementedError("Window rect requires Rust module")


def capture_blender_viewport(
    output_path: Optional[str] = None,
    width: int = 1920,
    height: int = 1080,
    fallback_to_blender: bool = True
) -> str:
    """
    Capture Blender viewport using Rust native screenshot.
    
    Args:
        output_path: Where to save screenshot
        width: Screenshot width
        height: Screenshot height
        fallback_to_blender: If True and Rust fails, use Blender render
    
    Returns:
        Path to saved screenshot
    """
    if not RUST_AVAILABLE and not fallback_to_blender:
        raise RuntimeError("Rust module not available and fallback disabled")
    
    try:
        if RUST_AVAILABLE:
            return capture_viewport(output_path, width, height)
    except Exception as e:
        logger.warning(f"Rust screenshot failed: {e}")
        if not fallback_to_blender:
            raise
    
    # Fallback to Blender render
    if fallback_to_blender:
        logger.info("Falling back to Blender render")
        from ..blender.connector import BlenderConnector
        
        connector = BlenderConnector()
        return connector.capture_viewport(output_path, width, height)
    
    raise RuntimeError("Screenshot failed and no fallback available")


def check_rust_available() -> bool:
    """Check if Rust module is available"""
    return RUST_AVAILABLE
