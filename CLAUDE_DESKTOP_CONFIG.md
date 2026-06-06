# Claude Desktop Configuration

To use UBM with Claude Desktop, add this to your Claude Desktop config:

## macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "/path/to/python",
      "args": ["-m", "src.server.mcp_server"],
      "cwd": "/path/to/UniversalBlenderMCP"
    }
  }
}
```

## Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "C:\\path\\to\\python.exe",
      "args": ["-m", "src.server.mcp_server"],
      "cwd": "C:\\path\\to\\UniversalBlenderMCP"
    }
  }
}
```

## Alternative: Using pip installation

If you installed UBM via pip:

```json
{
  "mcpServers": {
    "blender": {
      "command": "ubm",
      "args": ["serve", "--stdio"]
    }
  }
}
```

## Verification

After configuration:
1. Restart Claude Desktop
2. Look for the hammer icon (tools)
3. You should see Blender tools like `create_primitive`, `get_scene_info`

## Available Tools

Once configured, Claude can use:

- `create_primitive` - Create basic shapes
- `delete_object` - Delete objects
- `transform_object` - Move, rotate, scale
- `get_scene_info` - Get scene information
- `list_objects` - List all objects
- `set_material_color` - Set object color
- `capture_viewport` - Take screenshots
