# UBM Python API 使用指南 - 保底方案

> 当 CLI 因编码问题无法使用时，使用此 Python API

---

## 🎯 为什么需要这个？

### 问题
在 Windows GBK 编码系统（如中文 Windows）上，UBM CLI 会出现：
```
UnicodeEncodeError: 'gbk' codec can't encode character '\u2713'
```

### 解决方案
使用纯 Python API，完全避免命令行编码问题。

---

## 🚀 快速开始

### 方法 1: 直接运行示例

```bash
cd UniversalBlenderMCP
python api.py
```

### 方法 2: 导入使用

```python
from api import UBM, create_cube, quick_capture

# 创建 UBM 实例
ubm = UBM()

# 创建立方体
ubm.create_primitive("CUBE", name="MyCube", location=[0, 0, 0])

# 设置材质
ubm.set_material("MyCube", color=[0.8, 0.2, 0.2, 1.0])

# 截图
ubm.capture("screenshot.png")
```

### 方法 3: 便捷函数

```python
from api import create_cube, create_sphere, quick_capture

# 一键创建立方体
create_cube(location=[0, 0, 1], size=2)

# 一键创建球体
create_sphere(location=[3, 0, 1], size=1)

# 一键截图
quick_capture("quick.png")
```

---

## 📋 API 参考

### UBM 类

```python
ubm = UBM(blender_path=None)  # 自动检测 Blender 路径
```

#### 方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `create_primitive` | type, name, location, size | 创建几何体 |
| `delete_object` | name | 删除对象 |
| `transform` | name, location, rotation, scale | 变换对象 |
| `set_material` | object_name, color, name | 设置材质 |
| `capture` | output_path, width, height | 截图 |
| `get_scene_info` | - | 场景信息 |
| `list_objects` | - | 列出对象 |
| `add_light` | type, location, energy | 添加灯光 |
| `create_camera` | location, rotation | 创建相机 |

---

## 💡 完整示例

### 示例 1: 创建简单场景

```python
from api import UBM

ubm = UBM()

# 创建地板
ubm.create_primitive("PLANE", "Floor", [0, 0, 0], 10)

# 创建立方体
ubm.create_primitive("CUBE", "Box", [0, 0, 1], 2)

# 添加灯光
ubm.add_light("SUN", [5, 5, 8], energy=3)

# 截图
ubm.capture("scene.png")
```

### 示例 2: 产品展示

```python
from api import UBM

ubm = UBM()

# 创建立方体
cube = ubm.create_primitive("CUBE", "Product", [0, 0, 1], 2)

# 金属材质
ubm.set_material("Product", color=[0.9, 0.9, 0.9, 1.0])  # 银色

# 添加相机
ubm.create_camera(location=[7, -7, 5], rotation=[1.1, 0, 0.78])

# 4K 截图
ubm.capture("product_4k.png", width=3840, height=2160)
```

---

## 🔧 故障排除

### 问题 1: "Blender not found"

**解决**: 指定 Blender 路径

```python
ubm = UBM(blender_path="C:/Program Files/Blender Foundation/Blender 5.1/blender.exe")
```

### 问题 2: 模块导入错误

**解决**: 确保在 UniversalBlenderMCP 目录中运行

```bash
cd UniversalBlenderMCP
python api.py
```

### 问题 3: 截图失败

**解决**: 确保 Blender 场景中有相机

```python
ubm.create_camera(location=[7, -7, 5])
ubm.capture("screenshot.png")
```

---

## 📊 与 CLI 对比

| 功能 | CLI | Python API |
|------|-----|------------|
| 编码问题 | ❌ GBK 失败 | ✅ 无编码问题 |
| 使用难度 | 简单 | 中等 |
| 灵活性 | 有限 | 无限 |
| 集成性 | 命令行 | 代码嵌入 |
| 调试 | 困难 | 容易 |

---

## ✅ 推荐用法

| 场景 | 推荐方式 |
|------|----------|
| Windows GBK 系统 | Python API |
| 快速测试 | Python API |
| 脚本自动化 | Python API |
| 与其他 Python 集成 | Python API |
| Linux/Mac UTF-8 | CLI 可用 |
| 命令行偏好 | CLI 可用 |

---

## 📝 备注

- 纯 Python 实现，无外部依赖
- 所有输出使用 ASCII 字符 `[OK]` `[ERR]`
- 支持 Windows/Linux/Mac
- 可直接在 Blender 的 Python 控制台中运行

---

**[OK] Python API 准备就绪！**
