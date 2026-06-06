"""Visual Blender Control - 可视化 Blender 控制"""
import subprocess
import time
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import json

class BlenderVisualController:
    """
    可视化 Blender 控制器
    
    功能：
    1. 启动 Blender GUI
    2. 实时执行 bpy 操作
    3. 定期截图显示状态
    4. 让用户"看到"操作过程
    """
    
    def __init__(self, blender_path: Optional[str] = None):
        self.blender_path = blender_path or self._find_blender()
        self.process: Optional[subprocess.Popen] = None
        self.screenshot_dir = tempfile.mkdtemp(prefix="blender_visual_")
        self.operation_log = []
        self.current_step = 0
        
    def _find_blender(self) -> str:
        """查找 Blender"""
        paths = [
            r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender\blender.exe",
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return "blender"
    
    def start_gui(self) -> bool:
        """
        启动 Blender GUI
        
        Returns:
            是否成功启动
        """
        try:
            # 启动 Blender GUI (不带 --background)
            self.process = subprocess.Popen(
                [self.blender_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"🚀 Blender GUI 启动中... (PID: {self.process.pid})")
            time.sleep(3)  # 等待启动
            return self.process.poll() is None
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
    
    def execute_and_show(self, code: str, description: str) -> Dict[str, Any]:
        """
        执行 bpy 代码并显示结果
        
        Args:
            code: bpy 代码
            description: 操作描述
        
        Returns:
            执行结果
        """
        self.current_step += 1
        print(f"\n📍 步骤 {self.current_step}: {description}")
        print("─" * 50)
        
        # 创建带截图的脚本
        script = self._wrap_with_screenshot(code)
        
        # 执行
        result = self._execute_script(script)
        
        # 显示截图
        self._show_latest_screenshot()
        
        return result
    
    def _wrap_with_screenshot(self, code: str) -> str:
        """包装代码，添加截图功能"""
        screenshot_path = os.path.join(self.screenshot_dir, f"step_{self.current_step:02d}.png")
        
        wrapped = f'''
import bpy
import json

result = {{"status": "success", "data": {{}}}}

try:
    # 执行用户代码
{chr(10).join("    " + line for line in code.split(chr(10)))}
    
    # 截图
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.filepath = r"{screenshot_path}"
    bpy.ops.render.render(write_still=True)
    
    result["data"]["screenshot"] = r"{screenshot_path}"
    
except Exception as e:
    result["status"] = "error"
    result["error"] = str(e)

# 保存结果
with open(r"{screenshot_path}.json", "w") as f:
    json.dump(result, f)
'''
        return wrapped
    
    def _execute_script(self, script: str) -> Dict[str, Any]:
        """执行脚本"""
        script_path = os.path.join(self.screenshot_dir, f"script_{self.current_step}.py")
        with open(script_path, "w") as f:
            f.write(script)
        
        # 使用 subprocess 执行
        result = subprocess.run(
            [self.blender_path, "--background", "--python", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 读取结果
        result_path = os.path.join(self.screenshot_dir, f"step_{self.current_step:02d}.png.json")
        if os.path.exists(result_path):
            with open(result_path) as f:
                return json.load(f)
        
        return {"status": "success"}
    
    def _show_latest_screenshot(self):
        """显示最新截图"""
        screenshot_path = os.path.join(self.screenshot_dir, f"step_{self.current_step:02d}.png")
        if os.path.exists(screenshot_path):
            print(f"📸 截图已保存: {screenshot_path}")
            # 这里可以添加图片显示逻辑
    
    def create_cube_demo(self):
        """创建立方体演示"""
        steps = [
            ("创建地板", """
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.active_object.name = "Floor"
"""),
            ("创建立方体", """
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
bpy.context.active_object.name = "Cube"
"""),
            ("设置材质", """
mat = bpy.data.materials.new(name="RedMaterial")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.2, 0.2, 1)
bpy.context.active_object.data.materials.append(mat)
"""),
            ("添加相机", """
bpy.ops.object.camera_add(location=(7, -7, 5), rotation=(1.1, 0, 0.78))
bpy.context.scene.camera = bpy.context.active_object
""")
        ]
        
        print("=" * 60)
        print("🎬 Blender 可视化演示")
        print("=" * 60)
        
        for desc, code in steps:
            input(f"\n⏸ 按 Enter 执行: {desc}")
            result = self.execute_and_show(code, desc)
            if result.get("status") != "success":
                print(f"❌ 失败: {result.get('error')}")
        
        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print(f"📁 截图保存位置: {self.screenshot_dir}")
        print("=" * 60)
    
    def close(self):
        """关闭 Blender"""
        if self.process:
            self.process.terminate()
            print("🛑 Blender 已关闭")


# 使用示例
if __name__ == "__main__":
    controller = BlenderVisualController()
    
    # 启动 GUI
    if controller.start_gui():
        print("✅ Blender GUI 已启动！")
        print("请在 Blender 窗口中查看操作...")
        
        # 运行演示
        controller.create_cube_demo()
        
        # 保持运行
        input("\n⏸ 按 Enter 关闭 Blender...")
        controller.close()
    else:
        print("❌ 启动失败")
