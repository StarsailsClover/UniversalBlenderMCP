bl_info = {
    "name": "UniversalBlenderMCP",
    "author": "StarSails",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > UBM",
    "description": "Universal Blender MCP Server integration",
    "category": "System",
}

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty
from bpy.types import Panel, Operator, PropertyGroup

# 全局服务器实例
_server_instance = None

class UBMSettings(PropertyGroup):
    """UBM Settings"""
    enabled: BoolProperty(
        name="Enable Server",
        description="Start UBM socket server",
        default=False
    )
    port: IntProperty(
        name="Port",
        description="Server port",
        default=9876,
        min=1024,
        max=65535
    )
    host: StringProperty(
        name="Host",
        description="Server host",
        default="127.0.0.1"
    )

class UBM_OT_toggle_server(Operator):
    """Toggle UBM Server"""
    bl_idname = "ubm.toggle_server"
    bl_label = "Toggle Server"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        settings = context.scene.ubm_settings
        
        global _server_instance
        
        if settings.enabled:
            # Start server
            self.report({'INFO'}, "Starting UBM server...")
            # TODO: Start server
            settings.enabled = True
        else:
            # Stop server
            self.report({'INFO'}, "Stopping UBM server...")
            # TODO: Stop server
            settings.enabled = False
        
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
        
        layout.label(text="Server Settings")
        layout.prop(settings, "enabled")
        layout.prop(settings, "host")
        layout.prop(settings, "port")
        
        layout.separator()
        
        # Server status
        box = layout.box()
        box.label(text="Status:")
        if _server_instance:
            box.label(text="Running", icon='CHECKMARK')
        else:
            box.label(text="Stopped", icon='X')
        
        layout.separator()
        
        # Quick actions
        layout.label(text="Quick Actions")
        layout.operator("ubm.toggle_server")

classes = [
    UBMSettings,
    UBM_OT_toggle_server,
    UBM_PT_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ubm_settings = bpy.props.PointerProperty(type=UBMSettings)

def unregister():
    # Stop server if running
    global _server_instance
    if _server_instance:
        # TODO: Stop server
        pass
    
    del bpy.types.Scene.ubm_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
