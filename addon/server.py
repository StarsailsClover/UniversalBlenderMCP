"""UBM Socket Server - Runs inside Blender for real-time communication"""
import bpy
import threading
import socket
import json
import traceback
import logging
from typing import Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

class UBMSocketServer:
    """Socket server that runs inside Blender"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9876):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
    def start(self) -> bool:
        """Start the socket server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.socket.setblocking(False)
            
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            
            logger.info(f"UBM Socket Server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the socket server"""
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.info("UBM Socket Server stopped")
    
    def _run(self) -> None:
        """Main server loop"""
        while self.running:
            try:
                # Use select for non-blocking accept
                import select
                ready, _, _ = select.select([self.socket], [], [], 0.1)
                
                if ready:
                    client, address = self.socket.accept()
                    logger.info(f"Client connected: {address}")
                    
                    # Handle client in a new thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,),
                        daemon=True
                    )
                    client_thread.start()
                    
            except Exception as e:
                if self.running:
                    logger.error(f"Server error: {e}")
        
    def _handle_client(self, client: socket.socket) -> None:
        """Handle a client connection"""
        try:
            # Set timeout
            client.settimeout(30.0)
            
            # Receive data
            data = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we have a complete message
                try:
                    request = json.loads(data.decode('utf-8'))
                    break
                except json.JSONDecodeError:
                    continue
            
            # Process request
            if data:
                try:
                    request = json.loads(data.decode('utf-8'))
                    response = self._process_request(request)
                except json.JSONDecodeError as e:
                    response = {"status": "error", "error": f"Invalid JSON: {e}"}
                except Exception as e:
                    response = {"status": "error", "error": str(e)}
                
                # Send response
                response_json = json.dumps(response).encode('utf-8')
                client.sendall(response_json)
                
        except Exception as e:
            logger.error(f"Client handling error: {e}")
        finally:
            client.close()
    
    def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request - must run in Blender's main thread"""
        method = request.get("method")
        params = request.get("params", {})
        
        # Use Blender's main thread executor
        import bpy
        
        # For safety, execute in main thread
        result = {"status": "success"}
        
        try:
            if method == "get_scene_info":
                result["data"] = self._get_scene_info()
            elif method == "create_primitive":
                result["data"] = self._create_primitive(**params)
            elif method == "delete_object":
                result["data"] = self._delete_object(**params)
            elif method == "transform_object":
                result["data"] = self._transform_object(**params)
            elif method == "list_objects":
                result["data"] = self._list_objects()
            elif method == "add_light":
                result["data"] = self._add_light(**params)
            elif method == "create_camera":
                result["data"] = self._create_camera(**params)
            elif method == "set_keyframe":
                result["data"] = self._set_keyframe(**params)
            elif method == "capture_viewport":
                result["data"] = self._capture_viewport(**params)
            else:
                result = {"status": "error", "error": f"Unknown method: {method}"}
                
        except Exception as e:
            result = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
        
        return result
    
    def _get_scene_info(self) -> Dict[str, Any]:
        """Get scene information"""
        scene = bpy.context.scene
        
        objects = []
        for obj in scene.objects:
            obj_info = {
                "name": obj.name,
                "type": obj.type,
                "location": [round(x, 4) for x in obj.location],
                "visible": obj.visible_get()
            }
            if obj.type == 'MESH' and obj.data:
                obj_info["vertices"] = len(obj.data.vertices)
                obj_info["faces"] = len(obj.data.polygons)
            objects.append(obj_info)
        
        return {
            "name": scene.name,
            "objects_count": len(objects),
            "objects": objects,
            "frame_current": scene.frame_current,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end
        }
    
    def _create_primitive(self, type: str, name: str = None, location: list = None, size: float = 1.0) -> Dict[str, Any]:
        """Create a primitive object"""
        type_map = {
            "CUBE": "cube",
            "SPHERE": "uv_sphere",
            "CYLINDER": "cylinder",
            "CONE": "cone",
            "PLANE": "plane"
        }
        
        op_name = type_map.get(type.upper())
        if not op_name:
            raise ValueError(f"Invalid type: {type}")
        
        loc = location or [0, 0, 0]
        
        # Execute operator
        op = getattr(bpy.ops.mesh, f"primitive_{op_name}_add")
        op(size=size, location=tuple(loc))
        
        # Get created object
        obj = bpy.context.active_object
        if name:
            obj.name = name
        
        return {
            "name": obj.name,
            "type": type,
            "location": list(obj.location)
        }
    
    def _delete_object(self, name: str) -> Dict[str, Any]:
        """Delete an object"""
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
            return {"deleted": name}
        else:
            raise ValueError(f"Object not found: {name}")
    
    def _transform_object(self, name: str, location: list = None, rotation: list = None, scale: list = None) -> Dict[str, Any]:
        """Transform an object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        if location:
            obj.location = tuple(location)
        if rotation:
            obj.rotation_euler = tuple(rotation)
        if scale:
            obj.scale = tuple(scale)
        
        return {
            "name": obj.name,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale)
        }
    
    def _list_objects(self) -> Dict[str, Any]:
        """List all objects"""
        objects = []
        for obj in bpy.context.scene.objects:
            objects.append({
                "name": obj.name,
                "type": obj.type,
                "location": [round(x, 4) for x in obj.location],
                "visible": obj.visible_get()
            })
        
        return {"objects": objects, "count": len(objects)}
    
    def _add_light(self, type: str, name: str = None, location: list = None, energy: float = 10.0) -> Dict[str, Any]:
        """Add a light"""
        loc = location or [0, 0, 5]
        
        light_data = bpy.data.lights.new(name=(name or f"{type}_Light"), type=type)
        light_data.energy = energy
        
        light_obj = bpy.data.objects.new(name=(name or f"{type}_Light"), object_data=light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.location = tuple(loc)
        
        return {"name": light_obj.name, "type": type, "energy": energy}
    
    def _create_camera(self, name: str = None, location: list = None, rotation: list = None) -> Dict[str, Any]:
        """Create a camera"""
        loc = location or [7, -7, 5]
        rot = rotation or [1.1, 0, 0.8]
        
        camera_data = bpy.data.cameras.new(name=(name or "Camera"))
        camera_obj = bpy.data.objects.new(name=(name or "Camera"), object_data=camera_data)
        bpy.context.collection.objects.link(camera_obj)
        
        camera_obj.location = tuple(loc)
        camera_obj.rotation_euler = tuple(rot)
        
        # Set as active
        bpy.context.scene.camera = camera_obj
        
        return {"name": camera_obj.name, "location": loc, "rotation": rot}
    
    def _set_keyframe(self, object_name: str, frame: int, location: list = None) -> Dict[str, Any]:
        """Set a keyframe"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        
        # Set frame
        bpy.context.scene.frame_set(frame)
        
        # Set location if provided
        if location:
            obj.location = tuple(location)
            obj.keyframe_insert(data_path="location", frame=frame)
        
        return {"object": object_name, "frame": frame}
    
    def _capture_viewport(self, output_path: str = None, width: int = 1920, height: int = 1080) -> Dict[str, Any]:
        """Capture viewport"""
        import time
        
        if not output_path:
            output_path = f"/tmp/ubm_capture_{int(time.time())}.png"
        
        scene = bpy.context.scene
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100
        scene.render.filepath = output_path
        
        # Render
        bpy.ops.render.render(write_still=True)
        
        return {"path": output_path, "width": width, "height": height}


# Global server instance
_server: Optional[UBMSocketServer] = None

def get_server() -> Optional[UBMSocketServer]:
    """Get the global server instance"""
    global _server
    return _server

def start_server(host: str = "127.0.0.1", port: int = 9876) -> bool:
    """Start the socket server"""
    global _server
    
    if _server and _server.running:
        logger.warning("Server already running")
        return True
    
    _server = UBMSocketServer(host, port)
    return _server.start()

def stop_server() -> None:
    """Stop the socket server"""
    global _server
    
    if _server:
        _server.stop()
        _server = None
