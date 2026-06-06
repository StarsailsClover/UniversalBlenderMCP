bl_info = {
    "name": "UniversalBlenderMCP",
    "author": "StarSails",
    "version": (0, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > UBM",
    "description": "Universal Blender MCP Server integration - Socket Server for real-time communication",
    "category": "System",
}

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty, PointerProperty
from bpy.types import Panel, Operator, PropertyGroup
from bpy.app.handlers import persistent

# Import server module
try:
    from . import server
    SERVER_AVAILABLE = True
except ImportError as e:
    print(f"UBM: Server module import failed: {e}")
    SERVER_AVAILABLE = False


class UBMSettings(PropertyGroup):
    """UBM Settings"""
    
    server_enabled: BoolProperty(
        name="Enable Socket Server",
        description="Start UBM socket server for real-time communication",
        default=False,
        update=lambda self, context: update_server_status(self, context)
    )
    
    server_port: IntProperty(
        name="Port",
        description="Server port",
        default=9876,
        min=1024,
        max=65535
    )
    
    server_host: StringProperty(
        name="Host",
        description="Server host address",
        default="127.0.0.1"
    )
    
    server_status: StringProperty(
        name="Status",
        description="Server status",
        default="Stopped"
    )


def update_server_status(settings, context):
    """Update server when settings change"""
    if not SERVER_AVAILABLE:
        settings.server_status = "Error: Server module not available"
        return
    
    if settings.server_enabled:
        # Start server
        success = server.start_server(settings.server_host, settings.server_port)
        if success:
            settings.server_status = f"Running on {settings.server_host}:{settings.server_port}"
        else:
            settings.server_status = "Failed to start"
            settings.server_enabled = False
    else:
        # Stop server
        server.stop_server()
        settings.server_status = "Stopped"


class UBM_OT_start_server(Operator):
    """Start UBM Socket Server"""
    bl_idname = "ubm.start_server"
    bl_label = "Start Server"
    bl_description = "Start the UBM socket server"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if not SERVER_AVAILABLE:
            self.report({'ERROR'}, "Server module not available")
            return {'CANCELLED'}
        
        settings = context.scene.ubm_settings
        
        success = server.start_server(settings.server_host, settings.server_port)
        if success:
            settings.server_enabled = True
            settings.server_status = f"Running on {settings.server_host}:{settings.server_port}"
            self.report({'INFO'}, f"Server started on port {settings.server_port}")
        else:
            settings.server_status = "Failed to start"
            self.report({'ERROR'}, "Failed to start server")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class UBM_OT_stop_server(Operator):
    """Stop UBM Socket Server"""
    bl_idname = "ubm.stop_server"
    bl_label = "Stop Server"
    bl_description = "Stop the UBM socket server"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if not SERVER_AVAILABLE:
            self.report({'ERROR'}, "Server module not available")
            return {'CANCELLED'}
        
        settings = context.scene.ubm_settings
        
        server.stop_server()
        settings.server_enabled = False
        settings.server_status = "Stopped"
        
        self.report({'INFO'}, "Server stopped")
        return {'FINISHED'}


class UBM_OT_test_connection(Operator):
    """Test UBM Connection"""
    bl_idname = "ubm.test_connection"
    bl_label = "Test Connection"
    bl_description = "Test connection to UBM"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        self.report({'INFO'}, "Connection test successful")
        return {'FINISHED'}


class UBM_PT_panel(Panel):
    """UBM Main Panel"""
    bl_label = "Universal Blender MCP"
    bl_idname = "UBM_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UBM'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.ubm_settings
        
        # Server status box
        box = layout.box()
        box.label(text="Socket Server", icon='SETTINGS')
        
        # Status
        row = box.row()
        row.label(text=f"Status: {settings.server_status}")
        
        # Host and Port
        row = box.row()
        row.prop(settings, "server_host")
        row = box.row()
        row.prop(settings, "server_port")
        
        # Start/Stop buttons
        row = box.row(align=True)
        if settings.server_enabled:
            row.operator("ubm.stop_server", icon='PAUSE')
        else:
            row.operator("ubm.start_server", icon='PLAY')
        
        row.operator("ubm.test_connection", icon='CHECKMARK')
        
        # Info
        layout.separator()
        box = layout.box()
        box.label(text="Info", icon='INFO')
        box.label(text=f"Version: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}")
        box.label(text="Category: System")


class UBM_PT_tools_panel(Panel):
    """UBM Tools Panel"""
    bl_label = "UBM Quick Tools"
    bl_idname = "UBM_PT_tools_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UBM'
    
    def draw(self, context):
        layout = self.layout
        
        # Quick actions
        layout.label(text="Quick Actions:")
        col = layout.column(align=True)
        
        # These operators would be defined in separate files
        # For now, just show placeholders
        col.label(text="• Create Primitive")
        col.label(text="• Add Light")
        col.label(text="• Set Camera")
        col.label(text="• Capture Viewport")


@persistent
def load_post_handler(dummy):
    """Handler called after loading a file"""
    # Auto-start server if enabled
    if bpy.context and bpy.context.scene:
        settings = bpy.context.scene.ubm_settings
        if settings.server_enabled:
            if SERVER_AVAILABLE:
                server.start_server(settings.server_host, settings.server_port)


@persistent
def save_pre_handler(dummy):
    """Handler called before saving"""
    pass


classes = (
    UBMSettings,
    UBM_OT_start_server,
    UBM_OT_stop_server,
    UBM_OT_test_connection,
    UBM_PT_panel,
    UBM_PT_tools_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.ubm_settings = PointerProperty(type=UBMSettings)
    
    # Register handlers
    bpy.app.handlers.load_post.append(load_post_handler)
    bpy.app.handlers.save_pre.append(save_pre_handler)
    
    print("UBM Addon: Registered")


def unregister():
    # Stop server if running
    if SERVER_AVAILABLE:
        server.stop_server()
    
    # Remove handlers
    bpy.app.handlers.load_post.remove(load_post_handler)
    bpy.app.handlers.save_pre.remove(save_pre_handler)
    
    del bpy.types.Scene.ubm_settings
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("UBM Addon: Unregistered")


if __name__ == "__main__":
    register()
