"""Basic tests for UBM functionality"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blender.connector import BlenderConnector
from server.mcp_server import (
    create_primitive,
    delete_object,
    get_scene_info,
    list_objects
)


class TestBlenderConnector:
    """Test Blender connector"""
    
    def test_connector_creation(self):
        """Test that connector can be created"""
        # This will fail if Blender is not found
        try:
            connector = BlenderConnector()
            assert connector.blender_path is not None
        except FileNotFoundError:
            pytest.skip("Blender not installed")
    
    def test_scene_info(self):
        """Test getting scene info"""
        try:
            connector = BlenderConnector()
            result = connector.get_scene_info()
            assert "status" in result
        except FileNotFoundError:
            pytest.skip("Blender not installed")


class TestMCPTools:
    """Test MCP Tools"""
    
    def test_server_info(self):
        """Test server info tool"""
        from server.mcp_server import get_server_info
        info = get_server_info()
        assert info["name"] == "Universal Blender MCP"
        assert "version" in info
    
    def test_list_tools(self):
        """Test list tools"""
        from server.mcp_server import list_available_tools
        tools = list_available_tools()
        assert "create_primitive" in tools
        assert "delete_object" in tools
        assert "get_scene_info" in tools


class TestCLI:
    """Test CLI commands"""
    
    def test_cli_import(self):
        """Test CLI can be imported"""
        from cli.main import cli
        assert cli is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
