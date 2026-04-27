# 块块积木 → CMD 协议转换功能 — 技术总结

> **日期**: 2026-04-27
> **项目路径**: `F:\myScratch\python_server`
> **状态**: ✅ 已完成，测试通过

---

## 一、背景与目标

### 背景
- 上位机工具（PyQt5）需要通过 USB 与 STM32 设备通信
- 用户使用 **块块积木（Scratch 3.0 兼容）** 编程界面编写控制逻辑
- 需要将 Scratch 积木块自动转换为 STM32 可执行的二进制命令帧

### 目标
在 `python_server` 中实现：**解析 .sb3 文件 → 提取积木块 → 按协议映射表转换为 24 字节 CMD → 封装成完整通信帧**

---

## 二、文件清单

### 新增文件（3个）

| 文件 | 行数 | 功能 |
|------|------|------|
| `cmd_protocol.py` | ~350行 | 协议定义层：常量、枚举、映射表、CRC8、帧封装 |
| `cmd_builder.py` | ~400行 | 命令构建层：积木数据→24字节CMD→协议帧 |
| `test_cmd_e2e.py` | ~50行 | 端到端验证脚本 |

### 修改文件（3个）

| 文件 | 改动 |
|------|------|
| `block_parser.py` | 解析时收集结构化 CMD 数据（cmd_data + 变量表 + 列表） |
| `block_server.py` | 新增 `generate_commands` action + 逐条打印 + cmd_details 返回 |
| `test_server.html` | 新增"⚡生成CMD命令"按钮 + CMD 输出展示区 |

---

## 三、核心架构

```
┌──────────────┐    ┌───────────────┐    ┌──────────────┐    ┌──────────────┐
│   .sb3 文件   │───▶│ block_parser  │───▶│ cmd_builder  │───▶│  协议帧输出   │
│ (Scratch项目) │    │ (积木解析+收集) │    │ (CMD构建+封装) │    │ (24B×N+CRC) │
└──────────────┘    └───────────────┘    └──────────────┘    └──────────────┘
                           │                    │
                           ▼                    ▼
                     cmd_data[]          OPCODE_TO_CMD[]
                     variables{}        INPUT_NAME_MAP{}
                     lists{}            MATHOP_MAP{}
```

---

## 四、协议格式详解

### 4.1 单条 CMD 命令 — 固定 24 字节

C 结构体 `DEF_FLASH_CMD_ST`：

```
偏移  字段           大小     说明
─────────────────────────────────────────────
0x00  type_main      1B      主类型: TM_VALUE(0) / TASK(1) / PROGRAM(2) / HARDWARE(3)
0x01  type_sub       1B      子类型: 由 OPCODE 映射决定（见 Section 4）
0x02  ind            2B LE   联合: prog_ind(低12位) + task_ind(高4位)
0x04  st_param       20B     参数区（两种布局，见下文）
─────────────────────────────────────────────
总计                24字节
```

### 4.2 参数区布局

**TM_VALUE 模式**（变量赋值类）：
```
[extend(LE16)][len(LE16)][buff(16B)]
  2B          2B         16B        = 20B
```

**TM_PROGRAM / TM_HARDWARE 模式**（程序/硬件类）：
```
[param_set(LE16)][buff(18B)]
     2B            18B       = 20B
```

- **param_set**: 位域编码 val1/val2/val3 的类型（I32/FLOAT/STRING/BOOL/VAR）
- **buff**: 实际参数值（整数4字节/浮点4字节/字符串最多16字节）

### 4.3 完整通信帧

```
[帧头][功能码][包号(LE16)][CMD1(24B)][CMD2(24B)]...[CMDn(24B)][CRC8][帧尾]
 1B     1B       2B            N×24B                          1B     1B
```

- **帧头**: `0x5B` (`[`)
- **帧尾**: `0x5D`] (`]`)
- **CRC8**: CRC8-Maxim 多项式 `0x31`，初始值 `0x00`
- **功能码**: 区分烧录/调试/查询等不同用途

---

## 五、Opcode 映射表（核心转换逻辑）

定义在 `cmd_protocol.py` 的 `OPCODE_TO_CMD` 字典中，覆盖以下类别：

### 5.1 数学运算（7个）
| Scratch opcode | type_main | type_sub | 说明 |
|---------------|-----------|----------|------|
| `operator_add` | PROGRAM | 0x02 | ADD 加法 |
| `operator_subtract` | PROGRAM | 0x03 | SUB 减法 |
| `operator_multiply` | PROGRAM | 0x04 | MUL 乘法 |
| `operator_divide` | PROGRAM | 0x05 | DIV 除法 |
| `operator_mod` | PROGRAM | 0x1E | MOD 取模 |
| `operator_round` | PROGRAM | 0x1B | ROUND 四舍五入 |
| `operator_random` | PROGRAM | 0x20 | RAND 随机数 |

**动态映射** (`operator_mathop`)：
| 下拉选项 | type_sub | 说明 |
|---------|----------|------|
| abs | 0x08 | ABS 绝对值 |
| sqrt | 0x07 | SQRT 平方根 |
| sin/cos/tan | 0x0E~0x10 | 三角函数 |
| ln/log | 0x0A~0x0B | 对数函数 |
| e^ / 10^ | 0x0C~0x0D | 指数函数 |

### 5.2 比较运算（3个）
| opcode | type_sub | 说明 |
|--------|----------|------|
| `operator_gt` | 0x4B | MT 大于 |
| `operator_lt` | 0x49 | LT 小于 |
| `operator_equals` | 0x47 | EQU 等于 |

### 5.3 逻辑运算（3个）
| opcode | type_sub | 说明 |
|--------|----------|------|
| `operator_and` | 0x4D | AND 与 |
| `operator_or` | 0x4E | OR 或 |
| `operator_not` | 0x51 | NOT 非 |

### 5.4 字符串运算（4个）
| opcode | type_sub | 说明 |
|--------|----------|------|
| `operator_join` | 0x1C | TXT_ADD 拼接 |
| `operator_length` | 0x2D | STRLEN 长度 |
| `operator_contains` | 0x2F | STRSTR 包含判断 |
| `operator_letter_of` | 0x31 | GETCHR 取字符 |

### 5.5 控制类（9个）
| opcode | type_sub | 说明 |
|--------|----------|------|
| `control_if` | 0x52 | IF 条件判断 |
| `control_repeat` | 0x53 | REPEAT 计次循环 |
| `control_forever` | 0x53 | REPEAT 无限循环(次数=0) |
| `control_while` | 0x54 | WHILE_IF1 当真时循环 |
| `control_repeat_until` | 0x55 | WHILE_IF0 直到满足循环 |
| `control_for_each` | 0x56 | FOR_EACH 遍历列表 |
| `control_wait` | 0x00 | 延时等待 |
| `control_stop` | 0x57 | BREAK 跳出循环 |
| `control_if_else` | 0x52 | IF 带 else 分支 |

### 5.6 变量操作（2个）
| opcode | type_main | type_sub | 说明 |
|--------|-----------|----------|------|
| `data_setvariableto` | VALUE | 0x05 | SET 变量赋值 |
| `data_changevariableby` | PROGRAM | 0x02 | ADD 变量增减 |

### 5.7 列表操作（10个）
| opcode | type_sub | 说明 |
|--------|----------|------|
| `data_addtolist` | 0x63 | LIST_ADD_END 尾部添加 |
| `data_deleteoflist` | 0x56 | LIST_DEL_N 删除第N项 |
| `data_deletealloflist` | 0x46 | LIST_CREAT 清空重建 |
| `data_insertatlist` | 0x60 | LIST_ADD_N 插入第N项 |
| `data_replaceitemoflist` | 0x5B | LIST_SET_N 设置第N项 |
| `data_itemoflist` | 0x4C | LIST_GET_N 取第N项 |
| `data_itemnumoflist` | 0x4A | LIST_FIRST 查找首次出现 |
| `data_lengthoflist` | 0x48 | LIST_LEN 列表长度 |
| `data_listcontainsitem` | 0x4A | LIST_FIRST 包含判断 |

### 5.8 SmartPi 硬件扩展（18个）
| opcode | type_sub | 说明 |
|--------|----------|------|
| `smartpi_motorOnFor` | 0x01 | 电机运转N秒 |
| `smartpi_motorOn` | 0x02 | 电机启动 |
| `smartpi_motorOff` | 0x03 | 电机关闭 |
| `smartpi_setMotorPower` | 0x04 | 设置电机功率 |
| `smartpi_setMotorDirection` | 0x05 | 设置电机转向 |
| `smartpi_setLEDColor` | 0x10 | 设置 LED 颜色(RGB) |
| `smartpi_setLEDBrightness` | 0x11 | 设置 LED 亮度 |
| `smartpi_playNoteFor` | 0x20 | 播放音符N秒 |
| `smartpi_setTempo` | 0x21 | 设置演奏速度 |
| `smartpi_playSoundEffect` | 0x22 | 播放音效 |
| `smartpi_getDistance` | 0x30 | 测距传感器 |
| `smartpi_getAngle` | 0x31 | 角度传感器 |
| `smartpi_getSensorValue` | 0x32 | 通用传感器读取 |
| `smartpi_getButtonState` | 0x33 | 按键状态 |
| `smartpi_setMotorSpeed` | 0x40 | 设置电机速度 |
| `smartpi_motorForward` | 0x41 | 电机正转 |
| `smartpi_motorBackward` | 0x42 | 电机反转 |
| `smartpi_motorStop` | 0x43 | 电机停止 |

---

## 六、参数位置映射

Scratch 积木的输入参数名各不相同（如 `NUM1`, `OPERAND1`, `VALUE`），需要统一映射到协议的 `val1/val2/val3`：

```python
# 例: operator_add 的两个输入
"operator_add": {"NUM1": 1, "NUM2": 2}   # NUM1→val1, NUM2→val2

# 例: data_setvariableto 的一个输入
"data_setvariableto": {"VALUE": 1}        # VALUE→val1
```

完整映射定义在 `INPUT_NAME_MAP` 中，覆盖全部 30+ 个 opcode 的输入参数。

---

## 七、参数类型识别

CmdBuilder 自动识别每个参数的类型：

| 类型 | 标识 | buff 编码方式 |
|------|------|--------------|
| I32 整数常量 | 数字字面量 | `<i` 4字节小端 |
| FLOAT 浮点常量 | 含小数点的数字 | `<f` 4字节小端 |
| STRING 字符串常量 | 引号字符串 | UTF-8 最多16字节 |
| BOOL 布尔常量 | true/false | 1字节 0/1 |
| VAR 变量引用 | `__var__变量名` 前缀 | param_set 对应位标记 |

param_set 位域定义（每2bit表示一个参数类型）：
- bit[1:0] = val1 类型, bit[3:2] = val2 类型, bit[5:4] = val3 类型
- `00`=I32, `01`=FLOAT, `10`=STRING, `11`=BOOL; 若为变量则对应位额外置1

---

## 八、WebSocket 接口

### 请求
```json
{
    "action": "generate_commands",
    "project_data": { ... }  // 完整 project.json 内容
}
```

### 响应
```json
{
    "status": "success",
    "steps": 25,
    "output": ["📦 [任务 1] #0 ...", ...],
    "cmd_stats": {
        "total_cmds": 24,
        "error_count": 1,
        "supported_cmds": 23,
        "skipped_cmds": 1
    },
    "cmd_hex_strings": [
        "03 21 01 10 00 00 ...",   // 第1条CMD的hex
        "02 53 02 10 0A 00 ...",   // 第2条
        ...
    ],
    "cmd_details": [
        ["opcode=xxx", "desc=xxx", "type_main=0x03", ...],  // 每条的详情
        ...
    ],
    "frame_hex": "5b xx ... yy 5d",   // 完整帧hex
    "frame_length": 582,
    "errors": [],
    "elapsed": 0.009
}
```

---

## 九、前端页面功能

### test_server.html 新增内容

1. **⚡ 生成CMD命令按钮** — 选择 .sb3 文件后可用
2. **CMD 命令输出区域**:
   - 顶部统计徽章（命令数 / 帧长度 / 错误数 / 耗时）
   - 命令列表（黄色高亮 hex 头部 + 蓝色详情行 + 灰色分隔线）
3. **服务端逐条打印** — 控制台输出带格式的每条 CMD 详情（序号/hex/opcode/字段解析）

---

## 十、实测结果

使用 `Scratch作品3.sb3` 测试：

| 指标 | 数值 |
|------|------|
| 解析积木块数 | **25 个** |
| 生成的 CMD 命令 | **24 条** |
| 完整帧大小 | **582 字节** |
| 生成耗时 | **~9ms** |
| 覆盖的功能类型 | 循环/if/wait / 四则运算 / 比较 / 变量赋值 / SmartPi硬件(电机/LED/音符/红外) |
| 识别的变量 | 我的变量, X, Y (共3个) |

### 服务端打印示例
```
======================================================================
CMD 命令输出:
----------------------------------------------------------------------
  [  1] #1 03 21 01 10 00 00 ...
        │ opcode=smartpi_whenInfraredPressed  🔘 SmartPi 当红外按键按下
        │  type_main = 0x03 (HARDWARE)
        │  type_sub  = 0x21
        │  ind       = 0x0001
        └─ ───────────────────────────────────────────────────
  [  2] #2 02 53 02 10 0A 00 ...
        │ opcode=control_repeat  🔄 重复执行
        │  type_main = 0x02 (PROGRAM)
        │  type_sub  = 0x53 (REPEAT)
        └─ ...
----------------------------------------------------------------------
CMD 生成完成: 24 条命令, 帧长 582B, 耗时 0.009s
======================================================================
```

---

## 十一、设计决策记录

### Q1: 为什么 type_sub 不用 C 枚举值？
**原因**: C 头文件的枚举值与实际协议文档中的值不匹配。最终以《块块积木积木块到 CMD 转换对照表》Section 4 为准。

### Q2: 为什么 24 字节有两种内部布局？
**原因**: 不同主类型的参数需求不同：
- **TM_VALUE**（变量操作）需要 `extend`(扩展ID) + `len`(数据长度) 来支持任意长度的变量名和数据
- **TM_PROGRAM/HARDWARE**（程序/硬件指令）需要 `param_set`（参数类型位域）+ 更大的 `buff`(18B)来容纳多个参数值

### Q3: CRC8 表为什么用程序生成而非手写？
**原因**: 手写的 256 条目查表容易遗漏或重复（之前就遇到过只写了 208 条导致越界的问题）。改为 `_gen_crc8_table()` 函数运行时生成，保证正确性且代码更简洁。

### Q4: 变量如何从 Scratch 名称映射到协议中的 ID？
**当前方案**: 在 BlockParser 收集阶段建立 `{变量名: var_id}` 映射表，CmdBuilder 构建时查找该表。后续如需优化可改用连续索引。

---

## 十二、后续可扩展方向

- [ ] 支持更多 Scratch 扩展块的 opcode 映射
- [ ] 增加 CMD 帧的拆分/分包机制（当命令数超过单帧容量时）
- [ ] 实现 STM32 端的帧解析和执行引擎（配合上位机发送）
- [ ] 增加"模拟运行"模式，在前端可视化展示 CMD 执行流程
- [ ] 支持反向解析：CMD 帧 → 可读的积木描述（用于调试接收到的响应）
