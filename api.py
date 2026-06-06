#!/usr/bin/env python3
"""
UBM Pure Python API - 保底方案
不依赖 CLI，直接使用 Python 调用所有功能

特点：
- 纯 Python，无编码问题
- 不依赖命令行
- 直接在 Blender 中运行或外部调用
- 支持 Windows GBK 编码

示例：
    from api import UBM
    
    ubm = UBM()
    ubm.create_primitive("CUBE", location=[0, 0, 0])
    ubm.set_material("Cube", color=[0.8, 0.2, 0.2])
    ubm.capture("screenshot.png")
"""

import sys
import os
from pathlib import Path

# 添加 src 到路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from blender.connector import BlenderConnector
from server.mcp_server import (
    create_primitive,
    delete_object,
    transform_object,
    get_scene_info,
    list_objects,
    set_material_color,
    capture_viewport,
    add_light,
    create_camera,
    set_keyframe
)


class UBM:
    """
    UniversalBlenderMCP Python API
    
    不依赖 CLI 的纯 Python 接口
    """
    
    def __init__(self, blender_path: str = None):
        """
        初始化 UBM
        
        Args:
            blender_path: Blender 可执行文件路径，None 则自动检测
        """
        self.connector = BlenderConnector(blender_path)
        print(f"[INFO] UBM initialized")
        print(f"[INFO] Blender: {self.connector.blender_path}")
        
    def create_primitive(self, type: str, name: str = None, location: list = None, size: float = 1.0) -> dict:
        """
        创建基本几何体
        
        Args:
            type: 类型 (CUBE, SPHERE, CYLINDER, CONE, PLANE)
            name: 对象名称
            location: [x, y, z] 位置
            size: 大小
        
        Returns:
            创建结果
        """
        loc = location or [0, 0, 0]
        print(f"[ACTION] Creating {type} at {loc}...")
        
        result = create_primitive(
            type=type,
            name=name,
            location=tuple(loc),
            size=size
        )
        
        if result.get("status") == "success":
            print(f"[OK] Created: {result.get('name')}")
        else:
            print(f"[ERR] {result.get('error')}")
            
        return result
        
    def delete_object(self, name: str) -> dict:
        """删除对象"""
        print(f"[ACTION] Deleting {name}...")
        result = delete_object(name=name)
        if result.get("status") == "success":
            print(f"[OK] Deleted: {name}")
        else:
            print(f"[ERR] {result.get('error')}")
        return result
        
    def transform(self, name: str, location: list = None, rotation: list = None, scale: list = None) -> dict:
        """
        变换对象
        
        Args:
            name: 对象名称
            location: [x, y, z] 新位置
            rotation: [x, y, z] 旋转（弧度）
            scale: [x, y, z] 缩放
        """
        print(f"[ACTION] Transforming {name}...")
        
        result = transform_object(
            name=name,
            location=tuple(location) if location else None,
            rotation=tuple(rotation) if rotation else None,
            scale=tuple(scale) if scale else None
        )
        
        if result.get("status") == "success":
            print(f"[OK] Transformed: {name}")
        else:
            print(f"[ERR] {result.get('error')}")
            
        return result
        
    def set_material(self, object_name: str, color: list, name: str = None) -> dict:
        """
        设置材质颜色
        
        Args:
            object_name: 对象名称
            color: [r, g, b, a] 颜色值 (0-1)
            name: 材质名称
        """
        print(f"[ACTION] Setting material for {object_name}...")
        
        result = set_material_color(
            object_name=object_name,
            color=tuple(color),
            material_name=name
        )
        
        if result.get("status") == "success":
            print(f"[OK] Material set: {result.get('data', {}).get('material', {}).get('name')}")
        else:
            print(f"[ERR] {result.get('error')}")
            
        return result
        
    def capture(self, output_path: str, width: int = 1920, height: int = 1080) -> str:
        """
        截图
        
        Args:
            output_path: 输出路径
            width: 宽度
            height: 高度
        
        Returns:
            截图路径
        """
        print(f"[ACTION] Capturing {width}x{height}...")
        
        result = capture_viewport(
            output_path=output_path,
            width=width,
            height=height
        )
        
        if not result.startswith("Error"):
            print(f"[OK] Saved: {result}")
        else:
            print(f"[ERR] {result}")
            
        return result
        
    def get_scene_info(self) -> dict:
        """获取场景信息"""
        print("[ACTION] Getting scene info...")
        result = get_scene_info()
        
        if result.get("status") == "success":
            scene = result.get("data", {}).get("scene", {})
            print(f"[OK] Scene: {scene.get('name')}")
            print(f"       Objects: {scene.get('objects_count')}")
        else:
            print(f"[ERR] {result.get('error')}")
            
        return result
        
    def list_objects(self) -> list:
        """列出所有对象"""
        print("[ACTION] Listing objects...")
        result = list_objects()
        
        if result.get("status") == "success":
            objects = result.get("data", {}).get("objects", [])
            print(f"[OK] Found {len(objects)} objects")
            for obj in objects[:5]:  # 显示前5个
                print(f"       - {obj['name']} ({obj['type']})")
        else:
            print(f"[ERR] {result.get('error')}")
            
        return result
        
    def add_light(self, type: str, location: list = None, energy: float = 10.0) -> dict:
        """添加灯光"""
        print(f"[ACTION] Adding {type} light...")
        result = add_light(
            type=type,
            location=tuple(location) if location else None,
            energy=energy
        )
        
        if result.get("status") == "success":
            print(f"[OK] Light added: {result.get('name')}")
        else:
            print(f"[ERR] {result.get('error')}")
            
        return result
        
    def create_camera(self, location: list = None, rotation: list = None) -> dict:
        """创建相机"""
        print("[ACTION] Creating camera...")
        result = create_camera(
            location=tuple(location) if location else None,
            rotation=tuple(rotation) if rotation else None
        )
        
        if result.get("status") == "success":
            print(f"[OK] Camera: {result.get('name')}")
        else:
            print(f"[ERR] {result.get('error')}")
            
        return result


# 便捷函数 - 无需实例化

def create_cube(location: list = None, name: str = "Cube", size: float = 1.0) -> dict:
    """快速创建立方体"""
    ubm = UBM()
    return ubm.create_primitive("CUBE", name=name, location=location, size=size)

def create_sphere(location: list = None, name: str = "Sphere", size: float = 1.0) -> dict:
    """快速创建球体"""
    ubm = UBM()
    return ubm.create_primitive("SPHERE", name=name, location=location, size=size)

def quick_capture(output: str = "screenshot.png") -> str:
    """快速截图"""
    ubm = UBM()
    return ubm.capture(output)


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("UBM Python API Demo - 保底方案")
    print("=" * 60)
    print()
    
    # 方法1: 使用类
    ubm = UBM()
    
    # 创建场景
    ubm.create_primitive("PLANE", name="Floor", location=[0, 0, 0], size=10)
    ubm.create_primitive("CUBE", name="Box", location=[0, 0, 1], size=2)
    ubm.set_material("Box", color=[0.8, 0.2, 0.2, 1.0])
    
    # 截图
    ubm.capture("api_demo.png", width=1920, height=1080)
    
    print()
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)
