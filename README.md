# UniversalBlenderMCP (UBM)

> Used alongside Link2Blender.skill, enabling your AI Agent to create Blender models, animations and game assets by manipulating the CLI and leveraging Rust Native screenshot capabilities.

## Overview

UBM is a universal MCP server for Blender that can be used by any AI Agent:
- **Claude Desktop** via MCP
- **Cursor** via MCP  
- **VS Code** via MCP
- **Link2Blender.skill** (LBD) for OpenClaw ecosystem

## Architecture

```
AI Agent (Claude/Cursor/小跃)
    ↓ (MCP / OpenClaw Protocol)
UBM MCP Server
    ↓ (CLI / TCP Socket)
Blender + UBM Addon
    ↓ (bpy)
3D Scene
```

## Features

- 🚀 **Rust Native Screenshot** - High-performance viewport capture
- 🔧 **Full CLI** - Direct command execution (`ubm create`, `ubm capture`)
- 🎯 **MCP Protocol** - Standard Model Context Protocol
- 🌐 **Universal** - Works with any AI Agent
- 📦 **Blender Addon** - Native Blender integration

## Installation

```bash
pip install universal-blender-mcp
```

Or from source:

```bash
git clone https://github.com/Starsails/UniversalBlenderMCP
cd UniversalBlenderMCP
pip install -e ".[dev]"

# Optional: Build Rust screenshot module
pip install maturin
maturin develop
```

## Usage

### As MCP Server (for Claude Desktop)

Add to Claude Desktop config:

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

### CLI

```bash
# Start server
ubm serve

# Create objects
ubm create --type CUBE --location 0 0 0 --size 2

# Transform
ubm transform "Cube" --location 5 0 0 --rotation 0 0 1.57

# Capture viewport (using Rust native screenshot)
ubm capture --output screenshot.png --width 1920 --height 1080

# Check status
ubm status
```

### With Link2Blender.skill

See [Link2Blender.skill](../Link2Blender/) for OpenClaw integration.

## Development

### Project Structure

```
UniversalBlenderMCP/
├── src/
│   ├── server/           # MCP Server implementation
│   │   ├── mcp_server.py
│   │   └── tools/        # MCP Tools
│   ├── cli/              # CLI interface
│   │   └── main.py
│   ├── blender/          # Blender communication
│   │   └── connector.py
│   └── rust_bridge/      # Rust screenshot binding
├── rust/                 # Rust native module
│   └── src/
│       └── lib.rs
├── addon/                # Blender addon
│   └── __init__.py
└── tests/
```

### Running Tests

```bash
pytest tests/ -v
```

### Building Rust Module

```bash
cd rust
maturin develop  # For development
maturin build    # For distribution
```

## Version Compatibility

| UBM | Link2Blender.skill |
|-----|-------------------|
| 0.1.x | 0.1.x |

## License

MIT
