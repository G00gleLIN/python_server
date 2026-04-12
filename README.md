# Scratch 硬件测试工具

基于 WebSocket 的积木块解析与硬件测试工具，通过浏览器实时解析 Scratch 项目并转换为硬件命令。

## 📁 目录结构

```
python_server/
├── block_config.py       # 积木配置文件（定义积木类型和分类）
├── block_parser.py       # 积木解析器（递归解析积木执行逻辑）
├── block_server.py       # WebSocket 服务（前端实时通信）
├── test_server.html      # Web 测试界面（豆沙绿护眼背景）
├── start_server.bat      # 启动脚本（自动激活虚拟环境）
├── README.md             # 本文件
├── venv/                 # Python 虚拟环境
└── .vscode/              # VSCode 配置
```

## 🚀 快速开始

### 步骤 1：启动 WebSocket 服务
```bash
# 双击运行（推荐）
双击 start_server.bat

# 或指定端口
start_server.bat 9000
```

### 步骤 2：打开测试页面
在浏览器中打开：
```
file:///F:/myScratch/python_server/test_server.html
```

### 步骤 3：连接并测试
1. 点击 **"连接服务"** 按钮（ws://localhost:8765）
2. 选择 `.sb3` 文件（自动解压提取 project.json）
3. 点击 **"查看原始 JSON"** 查看项目数据
4. 点击 **"解析项目数据"** 查看积木解析结果

## 🎯 功能说明

### 1. 积木块解析
- **递归解析**：按 next 指针递归，支持嵌套积木优先执行
- **多任务独立**：每个绿旗事件独立编号，支持并行任务
- **分类输出**：按事件、运动、外观、控制等分类显示
- **详细日志**：包含执行步骤、耗时、参数信息

### 2. Web 测试界面
- **豆沙绿背景**：护眼色 #C7EDCC，长时间使用不疲劳
- **实时通信**：WebSocket 双向通信，支持进度推送
- **文件管理**：选择 .sb3 文件，自动解压提取 JSON
- **JSON 查看器**：弹窗查看格式化的 project.json
- **统计面板**：请求次数、成功次数、平均耗时

### 3. 硬件命令转换
- 将积木块解析结果转换为硬件可执行的命令
- 支持 SmartPi、WeDo2 等扩展设备
- 预留串口下载功能（可集成 pyserial）

## 🖥️ WebSocket 协议

### 连接地址
```
ws://localhost:8765
```

### 请求格式
```json
{
  "id": "REQ-0001",
  "action": "parse_project",
  "project_data": { ... }
}
```

### 支持的 Action

| Action | 说明 | 参数 |
|--------|------|------|
| `parse_project` | 解析项目数据 | `project_data`: 项目 JSON 对象 |
| `parse_json_file` | 解析本地 JSON 文件 | `file_path`: 文件路径 |
| `ping` | 心跳检测 | 无 |
| `get_server_info` | 获取服务器信息 | 无 |

### 响应格式
```json
{
  "id": "REQ-0001",
  "status": "success",
  "steps": 15,
  "output": ["#1 🟢 当绿旗被点击", ...],
  "elapsed": 0.125,
  "timestamp": "14:32:15"
}
```

## 📦 积木块解析器

### 文件说明

| 文件 | 说明 |
|------|------|
| `block_config.py` | 积木块配置文件（定义 200+ 种积木类型） |
| `block_parser.py` | 积木块解析器（递归解析执行逻辑） |

### 支持的积木类型

#### 控制类
- `control_wait` - ⏱️ 等待
- `control_repeat` - 🔄 重复执行
- `control_forever` - ♾️ 无限循环
- `control_if` / `control_if_else` - ❓ 条件判断

#### 运算符类
- `operator_add/subtract/multiply/divide` - 四则运算
- `operator_gt/lt/equals` - 比较运算
- `operator_and/or/not` - 逻辑运算

#### 数据类
- `data_setvariableto` - 📦 变量设为
- `data_changevariableby` - 📦 变量增加
- `data_addtolist` - 📋 添加到列表

#### 自定义扩展
- `smartpi_*` - SmartPi 设备（电机、LED、传感器）
- `wedo2_*` - LEGO WeDo 2.0

### 解析输出示例

```
[INFO] ============================================================
[INFO] 🎭 舞台 (Stage)
[INFO] ============================================================
[INFO] 📊 变量: 得分 = 0
[INFO] 📋 列表: 高分榜 = []

🧱 积木块解析:
🌐 #0 全局任务初始化 (共 1 个并行任务)
📦 [任务 1] #0 创建任务/初始化

#1 🟢 当绿旗被点击
#2 🔊 播放声音直到完成 (SOUND_MENU=喵)
#3 💬 说出秒数 (MESSAGE=你好！, SECS=2)
#4 🚶 移动步数 (STEPS=10)
#5 📦 变量设为 (VALUE=0)
#6 📋 添加到列表
#7 ⏱️ 等待 (DURATION=1)
==================================================
#8 🔄 开始循环: 重复 10 次
==================================================
   ┌─ 循环体
    #9 ⏱️ 等待 (DURATION=1)
   └─ 循环体结束
#10 ✅ 循环结束

✅ 解析完成！共 10 个步骤，耗时 0.125 秒
```

### 设计逻辑

- **顺序编号**：从 #1 开始连续递增，代表执行顺序
- **嵌套优先**：嵌套积木先执行，父积木使用返回值
- **递归解析**：按 next 指针递归，遇到嵌套先处理
- **任务隔离**：每个绿旗事件独立工作序列

## 🔧 依赖项

已安装在虚拟环境中：
- **websockets**: WebSocket 服务库
- **其他**: Python 标准库（json, asyncio, os, sys）

### 安装依赖
```bash
# 激活虚拟环境
venv\Scripts\activate.bat

# 安装 websockets
pip install websockets
```

## 🌐 架构设计

```
┌─────────────────────────────────────────┐
│  浏览器 (test_server.html)              │
│  ┌───────────────────────────────────┐  │
│  │  WebSocket Client                 │  │
│  │  ├─ 发送项目数据                  │  │
│  │  └─ 接收解析结果                  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
              ↕ WebSocket (localhost:8765)
┌─────────────────────────────────────────┐
│  Python 本地服务 (block_server.py)      │
│  ┌───────────────────────────────────┐  │
│  │  WebSocket Server (websockets)    │  │
│  │  ├─ block_parser.py (积木解析)    │  │
│  │  ├─ block_config.py (配置)        │  │
│  │  └─ 命令转换器                    │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 📝 与 scratch-editor 的关系

`python_server` 是 `scratch-editor` 项目的**独立测试工具**：

| 项目 | 说明 |
|------|------|
| **scratch-editor** | Scratch 3.0 编辑器 Monorepo，包含 GUI/VM/Render 等核心包 |
| **python_server** | 独立的积木解析工具，通过 WebSocket 提供解析服务 |

**工作流程**：
1. 在 `scratch-editor` 中编辑 .sb3 项目
2. 通过 `python_server` 解析积木块
3. 将解析结果转换为硬件命令
4. 发送到 SmartPi/WeDo2 等硬件设备

## ⚠️ 注意事项

1. **Python 版本**：需要 Python 3.8+（推荐 3.12）
2. **端口占用**：默认端口 8765，冲突时可自定义
3. **防火墙**：首次运行可能需允许 Python 通过防火墙
4. **文件路径**：Windows 路径使用双反斜杠 `\\` 或正斜杠 `/`

## 🐛 调试技巧

- **查看服务日志**：命令行窗口显示详细解析过程
- **心跳检测**：使用 "💓 心跳检测" 测试连接
- **服务器信息**：查看版本、请求统计、连接数
- **清除日志**：点击 "🗑️ 清除日志" 重新开始

## 📚 相关文档

- 设计逻辑：`F:\myScratch\scratch-editor\scripts\设计逻辑总结.md`
- SmartPi 扩展：`F:\myScratch\scratch-editor\SMARTPI_EXTENSION_GUIDE.md`
- 打包总结：`F:\myScratch\scratch-editor\打包总结.md`
