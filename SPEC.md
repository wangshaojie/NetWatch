# NetWatch - 技术规格文档

## 1. 项目概述

- **项目名称**: NetWatch
- **项目类型**: Windows 桌面应用程序
- **核心功能**: 基于 psutil 的端口管理工具，实时显示 TCP/UDP 端口连接及进程信息，支持安全终止进程
- **目标用户**: Windows 开发者、系统管理员、安全运维人员

---

## 2. 技术架构

### 2.1 目录结构

```
NetWatch/
├── main.py                    # 应用入口，高 DPI 配置，单实例控制
├── core/
│   ├── theme_manager.py       # 主题管理（浅色/深色）
│   └── single_instance.py     # 单实例控制
├── models/
│   └── port_model.py          # PortConnection 数据模型
├── services/
│   ├── port_scanner.py        # psutil 端口扫描服务
│   └── process_killer.py      # 进程终止服务
├── ui/
│   └── main_window.py         # PyQt5 主窗口
└── assets/
    └── icon.ico               # 应用图标
```

### 2.2 核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| PyQt5 | >= 5.15.0 | GUI 框架 |
| psutil | >= 5.9.0 | 端口扫描、进程信息获取 |
| pyinstaller | >= 6.0.0 | 打包为 exe |

---

## 3. UI/UX 规格

### 3.1 窗口规格

| 属性 | 值 |
|------|---|
| 窗口类型 | QMainWindow |
| 默认尺寸 | 1200 x 700 |
| 最小尺寸 | 900 x 500 |
| 启动位置 | 屏幕居中 |
| 标题 | "NetWatch - Port Manager" |

### 3.2 布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  Header: 标题 | 搜索框 | 刷新按钮 | 主题切换                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Main: QTableWidget (10 列)                                     │
│  - Protocol | Local Address | Port | Remote | Status |          │
│    PID | Process | CPU% | Memory | Action                      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  StatusBar: 显示连接数或搜索结果数                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 表格列定义

| 列索引 | 列名 | 宽度模式 | 对齐 | 字体样式 |
|--------|------|----------|------|----------|
| 0 | Protocol | 固定 60 | 居中 | 常规 |
| 1 | Local Address | 自适应 | 左对齐 | 常规 |
| 2 | Port | 固定 60 | 居中 | 加粗，蓝色 |
| 3 | Remote | 自适应 | 左对齐 | 常规 |
| 4 | Status | 自适应 | 居中 | 常规 |
| 5 | PID | 自适应 | 居中 | 常规 |
| 6 | Process | 拉伸 | 左对齐 | 常规 |
| 7 | CPU% | 自适应 | 居中 | 绿色 |
| 8 | Memory | 自适应 | 居中 | 橙色 |
| 9 | Action | 固定 70 | 居中 | Kill 按钮 |

### 3.4 配色方案

#### 深色主题 (默认)
| 元素 | 颜色 |
|------|------|
| 背景 | #1E1E1E |
| 文字 | #CCCCCC |
| 强调色 | #0078D4 |
| 表头背景 | #2D2D2D |
| 交替行 | #2D2D2D |
| 选中行 | #094771 |
| 悬停行 | #2A3A4A |
| Kill 按钮 | #DC2626 |
| CPU 文字 | #00B450 |
| Memory 文字 | #B48200 |
| 状态栏 | #007ACC |

#### 浅色主题
| 元素 | 颜色 |
|------|------|
| 背景 | #F3F3F3 |
| 文字 | #1A1A1A |
| 强调色 | #0078D4 |
| 表头背景 | #F0F0F0 |
| 交替行 | #FAFAFA |
| 选中行 | #0078D4 |
| Kill 按钮 | #DC2626 |

### 3.5 组件规格

#### 搜索框
- 宽度: 300px
- 占位符: "Search by port (e.g. 80, 443, 8080)..."
- 搜索方式: 模糊匹配端口号

#### 刷新按钮
- 文字: "↻ Refresh"
- 样式: 浅灰色背景

#### 主题切换按钮
- 文字: "🌓"
- 宽度: 40px

#### Kill 按钮
- 文字: "Kill"
- 样式: 透明背景，红色文字，无边框
- 光标: 手型

#### 加载遮罩
- 居中显示 "正在获取端口..."
- 半透明背景遮罩
- 自动跟随窗口大小调整位置

---

## 4. 功能规格

### 4.1 端口扫描 (PortScanner)

**数据来源**: `psutil.net_connections(kind='inet')`

**获取字段**:
- Protocol: TCP (SOCK_STREAM) / UDP (SOCK_DGRAM)
- Local Address / Port
- Remote Address / Port
- Status: 连接状态
- PID: 进程 ID

**进程信息获取**: `psutil.Process(pid)`
- name(): 进程名
- exe(): 进程路径
- cpu_percent(interval=0.01): CPU 使用率
- memory_info().rss: 内存使用 (MB)
- memory_percent(): 内存使用率

**性能优化**:
- 进程缓存: 最多 10000 条
- CPU 采样间隔: 10ms

**过滤规则**:
- 系统进程不显示（白名单）
- 去重: (protocol, local_addr, port, remote_addr, port, status, pid)

**系统进程白名单**:
```
system, smss.exe, csrss.exe, wininit.exe, services.exe,
lsass.exe, svchost.exe, winlogon.exe, explorer.exe,
dllhost.exe, rundll32.exe, taskmgr.exe, winmgmt.exe,
spoolsv.exe, fontdrvhost.exe, dwm.exe, conhost.exe,
ctfmon.exe, sihost.exe, logonui.exe, WUDFHost.exe,
Registry, audiodg.exe, SearchIndexer.exe
```

### 4.2 进程终止 (ProcessKiller)

**实现方式**: `psutil.Process(pid).kill()`

**保护机制**:
- 终止前再次检查 PID 是否存在
- 系统进程白名单校验
- 确认对话框

### 4.3 搜索功能

**搜索范围**: 仅端口号 (local_port)
**匹配方式**: 子字符串模糊匹配
**示例**:
- "80" 匹配 80, 800, 8080, 30080
- "443" 匹配 443, 1443, 4430

**高亮显示**: 匹配行的端口列显示绿色

### 4.4 主题切换

**实现方式**: ThemeManager.toggle_theme()

**主题样式**: 通过 stylesheet 应用到 QMainWindow

**样式持久化**: 仅内存保留，不保存到配置

### 4.5 单实例控制

**实现方式**: 文件锁 (.netwatch.lock)

**锁文件内容**: 当前进程 PID

**检查逻辑**: 启动时检查锁文件 PID 是否存在

---

## 5. 数据模型

### PortConnection (dataclass)

```python
@dataclass
class PortConnection:
    protocol: str          # TCP 或 UDP
    local_address: str     # 本地 IP
    local_port: int       # 本地端口
    remote_address: str   # 远程 IP
    remote_port: int      # 远程端口
    status: str           # 连接状态
    pid: int              # 进程 ID
    process_name: str     # 进程名
    process_path: str     # 进程路径
    cpu_percent: float    # CPU 使用率
    memory_percent: float # 内存使用率
    memory_mb: float     # 内存使用 (MB)
```

### matches_search(query)

仅匹配 local_port，支持模糊搜索。

---

## 6. 后台线程

### ScanThread (QThread)

**用途**: 在后台执行端口扫描，避免 UI 阻塞

**信号**:
- `finished(list)`: 扫描完成，返回连接列表

**执行流程**:
1. 启动线程
2. 调用 scanner.get_all_connections()
3. 发射 finished 信号
4. 线程结束

---

## 7. 用户交互流程

### 7.1 启动流程
```
启动应用 → 单实例检查 → 显示窗口(居中) →
显示加载遮罩 → 后台扫描端口 → 显示数据
```

### 7.2 搜索流程
```
输入搜索 → 过滤连接 → 重新显示表格 →
高亮匹配端口 → 更新状态栏计数
```

### 7.3 终止进程流程
```
点击 Kill → 显示确认对话框 →
显示进程信息 → 用户确认 →
执行 kill → 显示结果 → 刷新端口列表
```

---

## 8. 验收标准

### 视觉检查点
- [x] 窗口启动时居中显示
- [x] 深色/浅色主题正确切换
- [x] 标题在两种主题下都可见
- [x] 表格显示 10 列数据
- [x] Kill 按钮为红色
- [x] 搜索匹配端口显示绿色
- [x] 加载时显示 "正在获取端口..." 遮罩

### 功能检查点
- [x] 端口扫描使用 psutil.net_connections()
- [x] 进程信息使用 psutil.Process()
- [x] CPU 使用率准确显示（非 0.0）
- [x] 系统进程不显示在列表中
- [x] Kill 按钮可正常终止进程
- [x] 搜索仅匹配端口号
- [x] 后台线程不阻塞 UI
- [x] 单实例控制正常工作
