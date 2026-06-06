"""WebSocket Server for real-time Blender monitoring"""
import asyncio
import websockets
import json
import time
from typing import Set, Dict, Any
from datetime import datetime

class BlenderWebSocketServer:
    """
    WebSocket 服务器 - 实时广播 Blender 操作
    
    功能：
    1. 多客户端实时连接
    2. 广播执行状态
    3. 发送截图数据
    4. 接收远程命令
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        self.server = None
        
    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """注册新客户端"""
        self.clients.add(websocket)
        print(f"👤 客户端连接 ({len(self.clients)} 在线)")
        await self._send_to_client(websocket, {
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Blender WebSocket Server"
        })
        
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """注销客户端"""
        self.clients.discard(websocket)
        print(f"👋 客户端断开 ({len(self.clients)} 在线)")
        
    async def _send_to_client(self, websocket, message: Dict):
        """发送消息给单个客户端"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            print(f"⚠️  发送失败: {e}")
            
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有客户端"""
        if self.clients:
            message["timestamp"] = datetime.now().isoformat()
            message["clients"] = len(self.clients)
            
            # 并发发送给所有客户端
            await asyncio.gather(
                *[self._send_to_client(client, message) for client in self.clients],
                return_exceptions=True
            )
            
    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
            
    async def _handle_message(self, websocket, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")
            
            if msg_type == "command":
                # 执行命令
                command = data.get("command")
                await self._execute_command(command, data.get("params", {}))
            elif msg_type == "ping":
                await self._send_to_client(websocket, {"type": "pong"})
            else:
                await self._send_to_client(websocket, {
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })
        except json.JSONDecodeError:
            await self._send_to_client(websocket, {
                "type": "error",
                "message": "Invalid JSON"
            })
            
    async def _execute_command(self, command: str, params: Dict):
        """执行 Blender 命令"""
        from ..server.mcp_server import (
            create_primitive,
            get_scene_info,
            capture_viewport
        )
        
        result = {"type": "command_result", "command": command}
        
        try:
            if command == "create_primitive":
                result["data"] = create_primitive(**params)
            elif command == "get_scene_info":
                result["data"] = get_scene_info()
            elif command == "capture_viewport":
                result["data"] = capture_viewport(**params)
            else:
                result["error"] = f"Unknown command: {command}"
                
        except Exception as e:
            result["error"] = str(e)
            
        await self.broadcast(result)
        
    async def start(self):
        """启动 WebSocket 服务器"""
        self.running = True
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port
        )
        print(f"🌐 WebSocket Server started at ws://{self.host}:{self.port}")
        print(f"   等待客户端连接...")
        
        # 保持运行
        while self.running:
            await asyncio.sleep(1)
            
    async def stop(self):
        """停止服务器"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        print("🛑 WebSocket Server stopped")
        
    async def send_progress(self, step: int, total: int, message: str, details: Dict = None):
        """发送进度更新"""
        await self.broadcast({
            "type": "progress",
            "step": step,
            "total": total,
            "progress_percent": int(step / total * 100),
            "message": message,
            "details": details or {}
        })
        
    async def send_screenshot(self, image_path: str, description: str):
        """发送截图信息"""
        import base64
        
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
                
            await self.broadcast({
                "type": "screenshot",
                "description": description,
                "image_base64": f"data:image/png;base64,{image_data}",
                "image_path": image_path
            })
        except Exception as e:
            await self.broadcast({
                "type": "error",
                "message": f"Failed to send screenshot: {e}"
            })


# 全局服务器实例
_server_instance: BlenderWebSocketServer = None

async def start_websocket_server(host: str = "localhost", port: int = 8765):
    """启动 WebSocket 服务器"""
    global _server_instance
    _server_instance = BlenderWebSocketServer(host, port)
    await _server_instance.start()
    
def get_websocket_server() -> BlenderWebSocketServer:
    """获取 WebSocket 服务器实例"""
    return _server_instance

async def broadcast_message(message: Dict[str, Any]):
    """广播消息"""
    if _server_instance:
        await _server_instance.broadcast(message)
