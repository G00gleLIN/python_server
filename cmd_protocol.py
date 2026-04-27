# -*- coding: utf-8 -*-
"""
块块积木通讯协议 V1.1 - CMD 命令协议定义

依据：
  - 《块块积木积木块到 CMD 转换对照表》V1.2 (2026-04-24)
  - 《块块积木通讯协议 V1.1》
  - block_xml_parse 项目的实际解析代码

说明：
  type_sub 值以转换对照表（Section 4）为准，
  对照表与 C 语言枚举（Section 7）的值有差异时，以对照表+实际二进制示例为准。
  例如: 对照表 E_controls_if → 0x52，示例 6.3 也确认 0x52，
        而 C 枚举 SUB_PROGRAM_IF = 0x76 (位置 118) 不匹配实际协议。
"""

import struct


# ==================== 帧格式常量 ====================
FRAME_HEADER = 0x5B
FRAME_TAIL   = 0x5D
CMD_SIZE     = 24       # 每条命令固定 24 字节


# ==================== type_main 枚举 ====================
TM_VALUE    = 0x00      # 变量定义
TM_TASK     = 0x01      # 任务
TM_PROGRAM  = 0x02      # 程序
TM_HARDWARE = 0x03      # 硬件控制

TYPE_MAIN_NAMES = {
    TM_VALUE: "TM_VALUE",
    TM_TASK:  "TM_TASK",
    TM_PROGRAM: "TM_PROGRAM",
    TM_HARDWARE: "TM_HARDWARE",
}


# ==================== 变量类型枚举 (DEF_VAL_TYPE_EM) ====================
VAL_TYPE_U8     = 0
VAL_TYPE_I8     = 1
VAL_TYPE_U16    = 2
VAL_TYPE_I16    = 3
VAL_TYPE_U32    = 4
VAL_TYPE_I32    = 5        # 数据默认此类型
VAL_TYPE_FLOAT  = 6
VAL_TYPE_STRING = 7
VAL_TYPE_LIST   = 8
VAL_TYPE_BOOL   = 9
VAL_TYPE_NULL   = 10
VAL_TYPE_COLOR  = 11
VAL_TYPE_ARRAY8 = 12
VAL_TYPE_ARRAY16 = 13
VAL_TYPE_ARRAY32 = 14


# ==================== 常量类型枚举 (DEF_CONSTANT_TYPE_EM) ====================
CONS_TYPE_I32    = 0     # 整数常量
CONS_TYPE_FLOAT  = 1     # 浮点常量
CONS_TYPE_STRING = 2     # 文本常量
CONS_TYPE_LIST   = 3     # 列表常量
CONS_TYPE_BOOL   = 4     # 布尔常量
CONS_TYPE_NULL   = 5     # 空
CONS_TYPE_COLOR  = 6     # 颜色
CONS_TYPE_ARRAY8 = 7     # 单字节数组


# ==================== param_set 位域定义 ====================
# uint16_t 位域:
#   bit0:      next_flag  - 是否有跳转 (if/loop/break)
#   bit1:      r_flag     - 是否有返回值变量
#   bit2:      val1       - 参数1是否为变量 (1=变量, 0=常量)
#   bit3:      val2       - 参数2是否为变量
#   bit4:      val3       - 参数3是否为变量
#   bit5-7:    type_val1  - 参数1常量类型
#   bit8-10:   type_val2  - 参数2常量类型
#   bit11-13:  type_val3  - 参数3常量类型
#   bit14-15:  rev        - 保留

PARAM_NEXT_FLAG  = 0       # bit0
PARAM_R_FLAG     = 1       # bit1
PARAM_VAL1       = 2       # bit2
PARAM_VAL2       = 3       # bit3
PARAM_VAL3       = 4       # bit4
PARAM_TYPE_VAL1  = 5       # bit5-7
PARAM_TYPE_VAL2  = 8       # bit8-10
PARAM_TYPE_VAL3  = 11      # bit11-13


def build_param_set(next_flag=0, r_flag=0, val1_is_var=0, val2_is_var=0,
                    val3_is_var=0, type_val1=0, type_val2=0, type_val3=0):
    """构建 param_set 16位位域"""
    value = 0
    value |= (next_flag & 0x01) << PARAM_NEXT_FLAG
    value |= (r_flag    & 0x01) << PARAM_R_FLAG
    value |= (val1_is_var & 0x01) << PARAM_VAL1
    value |= (val2_is_var & 0x01) << PARAM_VAL2
    value |= (val3_is_var & 0x01) << PARAM_VAL3
    value |= (type_val1  & 0x07) << PARAM_TYPE_VAL1
    value |= (type_val2  & 0x07) << PARAM_TYPE_VAL2
    value |= (type_val3  & 0x07) << PARAM_TYPE_VAL3
    return value


def parse_param_set(param_set):
    """解析 param_set 16位位域，返回字典"""
    return {
        'next_flag':  (param_set >> PARAM_NEXT_FLAG) & 0x01,
        'r_flag':     (param_set >> PARAM_R_FLAG)    & 0x01,
        'val1':       (param_set >> PARAM_VAL1)      & 0x01,
        'val2':       (param_set >> PARAM_VAL2)      & 0x01,
        'val3':       (param_set >> PARAM_VAL3)      & 0x01,
        'type_val1':  (param_set >> PARAM_TYPE_VAL1) & 0x07,
        'type_val2':  (param_set >> PARAM_TYPE_VAL2) & 0x07,
        'type_val3':  (param_set >> PARAM_TYPE_VAL3) & 0x07,
    }


# ==================== ind 联合体定义 ====================
# uint16_t: bit0-11 = prog_ind (程序序号), bit12-15 = task_ind (任务序号)


def build_ind(prog_ind, task_ind=0):
    """构建 ind 16位值"""
    return ((prog_ind & 0xFFF) | ((task_ind & 0x0F) << 12))


def parse_ind(ind_val):
    """解析 ind 16位值"""
    return {
        'prog_ind': ind_val & 0xFFF,
        'task_ind': (ind_val >> 12) & 0x0F,
    }


# ==================== Scratch opcode → CMD 映射表 ====================
# 格式: opcode → (type_main, type_sub)
# type_sub 值以转换对照表 Section 4 为准

OPCODE_TO_CMD = {
    # ─── 数学运算 (对照表 4.1) ───
    "operator_add":       (TM_PROGRAM, 0x02),   # ADD
    "operator_subtract":  (TM_PROGRAM, 0x03),   # SUB
    "operator_multiply":  (TM_PROGRAM, 0x04),   # MUL
    "operator_divide":    (TM_PROGRAM, 0x05),   # DIV
    "operator_mod":       (TM_PROGRAM, 0x1E),   # MOD
    "operator_round":     (TM_PROGRAM, 0x1B),   # ROUND
    "operator_random":    (TM_PROGRAM, 0x20),   # RAND
    "operator_mathop":    (TM_PROGRAM, None),   # 动态: 根据 OPERATOR 字段确定 type_sub

    # ─── 比较运算 (对照表 4.4) ───
    "operator_gt":        (TM_PROGRAM, 0x4B),   # MT  (大于)
    "operator_lt":        (TM_PROGRAM, 0x49),   # LT  (小于)
    "operator_equals":    (TM_PROGRAM, 0x47),   # EQU (等于)

    # ─── 逻辑运算 (对照表 4.4) ───
    "operator_and":       (TM_PROGRAM, 0x4D),   # AND
    "operator_or":        (TM_PROGRAM, 0x4E),   # OR
    "operator_not":       (TM_PROGRAM, 0x51),   # NOT

    # ─── 字符串运算 (对照表 4.2) ───
    "operator_join":      (TM_PROGRAM, 0x1C),   # TXT_ADD
    "operator_length":    (TM_PROGRAM, 0x2D),   # STRLEN
    "operator_contains":  (TM_PROGRAM, 0x2F),   # STRSTR
    "operator_letter_of": (TM_PROGRAM, 0x31),   # GETCHR

    # ─── 控制类 (对照表 4.5) ───
    "control_if":           (TM_PROGRAM, 0x52),  # IF 条件判断
    "control_if_else":      (TM_PROGRAM, 0x52),  # IF (带 else 分支)
    "control_repeat":       (TM_PROGRAM, 0x53),  # REPEAT 重复循环
    "control_repeat_until": (TM_PROGRAM, 0x55),  # WHILE_IF0 (重复直到条件满足)
    "control_while":        (TM_PROGRAM, 0x54),  # WHILE_IF1 (当条件真时重复)
    "control_forever":      (TM_PROGRAM, 0x53),  # REPEAT 无限循环(次数=0)
    "control_for_each":     (TM_PROGRAM, 0x56),  # FOR_EACH 遍历列表
    "control_wait":         (TM_PROGRAM, 0x00),  # 延时/等待
    "control_stop":         (TM_PROGRAM, 0x57),  # BREAK 跳出循环

    # ─── 变量操作 (对照表 4.6) ───
    "data_setvariableto":    (TM_VALUE,   0x05),  # SET 变量赋值 (type_sub=I32类型码)
    "data_changevariableby": (TM_PROGRAM, 0x02),  # ADD 变量增加

    # ─── 列表操作 (对照表 4.3) ───
    "data_addtolist":         (TM_PROGRAM, 0x63),  # LIST_ADD_END
    "data_deleteoflist":      (TM_PROGRAM, 0x56),  # LIST_DEL_N
    "data_deletealloflist":   (TM_PROGRAM, 0x46),  # LIST_CREAT (重建空列表)
    "data_insertatlist":      (TM_PROGRAM, 0x60),  # LIST_ADD_N 插入
    "data_replaceitemoflist": (TM_PROGRAM, 0x5B),  # LIST_SET_N 设置第N项
    "data_itemoflist":        (TM_PROGRAM, 0x4C),  # LIST_GET_N 取第N项
    "data_itemnumoflist":     (TM_PROGRAM, 0x4A),  # LIST_FIRST 查找首次出现
    "data_lengthoflist":      (TM_PROGRAM, 0x48),  # LIST_LEN 列表长度
    "data_listcontainsitem":  (TM_PROGRAM, 0x4A),  # LIST_FIRST 查找

    # ─── SmartPi 硬件扩展 ───
    "smartpi_motorOnFor":        (TM_HARDWARE, 0x01),
    "smartpi_motorOn":           (TM_HARDWARE, 0x02),
    "smartpi_motorOff":          (TM_HARDWARE, 0x03),
    "smartpi_setMotorPower":     (TM_HARDWARE, 0x04),
    "smartpi_setMotorDirection": (TM_HARDWARE, 0x05),
    "smartpi_setLEDColor":       (TM_HARDWARE, 0x10),
    "smartpi_setLEDBrightness":  (TM_HARDWARE, 0x11),
    "smartpi_playNoteFor":       (TM_HARDWARE, 0x20),
    "smartpi_setTempo":          (TM_HARDWARE, 0x21),
    "smartpi_playSoundEffect":   (TM_HARDWARE, 0x22),
    "smartpi_getDistance":       (TM_HARDWARE, 0x30),
    "smartpi_getAngle":          (TM_HARDWARE, 0x31),
    "smartpi_getSensorValue":    (TM_HARDWARE, 0x32),
    "smartpi_getButtonState":    (TM_HARDWARE, 0x33),
    "smartpi_setMotorSpeed":     (TM_HARDWARE, 0x40),
    "smartpi_motorForward":      (TM_HARDWARE, 0x41),
    "smartpi_motorBackward":     (TM_HARDWARE, 0x42),
    "smartpi_motorStop":         (TM_HARDWARE, 0x43),
}


# ==================== operator_mathop 运算符映射 ====================
# Scratch mathop 下拉菜单选项 → type_sub
MATHOP_MAP = {
    "abs":      0x08,   # ABS 绝对值
    "sqrt":     0x07,   # SQRT 平方根
    "floor":    0x1D,   # FLOOR 向下取整
    "ceiling":  0x1C,   # CEIL 向上取整
    "sin":      0x0E,   # SIN 正弦
    "cos":      0x0F,   # COS 余弦
    "tan":      0x10,   # TAN 正切
    "asin":     0x11,   # ASIN 反正弦
    "acos":     0x12,   # ACOS 反余弦
    "atan":     0x13,   # ATAN 反正切
    "ln":       0x0A,   # LN 自然对数
    "log":      0x0B,   # LOG10 以10为底的对数
    "e ^":      0x0C,   # EXP e的N次方
    "10 ^":     0x0D,   # POW10 10的N次方
}


# ==================== Scratch 输入参数名 → 协议参数位置映射 ====================
# 不同 opcode 使用不同的输入参数名，需要统一映射到 val1/val2/val3
INPUT_NAME_MAP = {
    # ─── 数学运算 ───
    "operator_add":       {"NUM1": 1,  "NUM2": 2},
    "operator_subtract":  {"NUM1": 1,  "NUM2": 2},
    "operator_multiply":  {"NUM1": 1,  "NUM2": 2},
    "operator_divide":    {"NUM1": 1,  "NUM2": 2},
    "operator_mod":       {"NUM1": 1,  "NUM2": 2},
    "operator_random":    {"FROM": 1,   "TO": 2},
    "operator_round":     {"NUM": 1},
    "operator_mathop":    {"NUM": 1},

    # ─── 比较 ───
    "operator_gt":        {"OPERAND1": 1,  "OPERAND2": 2},
    "operator_lt":        {"OPERAND1": 1,  "OPERAND2": 2},
    "operator_equals":    {"OPERAND1": 1,  "OPERAND2": 2},

    # ─── 逻辑 ───
    "operator_and":       {"OPERAND1": 1,  "OPERAND2": 2},
    "operator_or":        {"OPERAND1": 1,  "OPERAND2": 2},
    "operator_not":       {"OPERAND": 1},

    # ─── 字符串 ───
    "operator_join":      {"STRING1": 1,  "STRING2": 2},
    "operator_length":    {"STRING": 1},
    "operator_contains":  {"STRING1": 1,  "STRING2": 2},
    "operator_letter_of": {"STRING": 1,   "LETTER": 2},

    # ─── 控制 ───
    "control_repeat":       {"TIMES": 1},
    "control_repeat_until": {"CONDITION": 1},
    "control_while":        {"CONDITION": 1},
    "control_wait":         {"DURATION": 1},
    "control_for_each":     {"VALUE": 1},

    # ─── 变量 ───
    "data_setvariableto":    {"VALUE": 1},
    "data_changevariableby": {"VALUE": 1},

    # ─── 列表 ───
    "data_addtolist":         {"ITEM": 1},
    "data_deleteoflist":      {"INDEX": 1},
    "data_insertatlist":      {"INDEX": 1,  "ITEM": 2},
    "data_replaceitemoflist": {"INDEX": 1,  "ITEM": 2},
    "data_itemoflist":        {"INDEX": 1},
    "data_itemnumoflist":     {"ITEM": 1},
    "data_listcontainsitem":  {"ITEM": 1},
}


# ==================== CRC8-Maxim 算法 ====================
# 多项式: x^8 + x^5 + x^4 + 1 = 0x31
# 初始值: 0x00; 无反转/无输出反转 (标准 Maxim/Dallas CRC-8)

# CRC8-Maxim 查表 (多项式 0x31, 完整 256 条目)
def _gen_crc8_table():
    t = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
        t.append(crc)
    return t

_CRC8_TABLE = _gen_crc8_table()


def crc8_maxim(data: bytes) -> int:
    """
    计算 CRC8-Maxim 校验值
    多项式: x^8 + x^5 + x^4 + 1 (0x31)
    初始值: 0x00
    返回: 1字节校验值
    """
    crc = 0
    for byte in data:
        crc = _CRC8_TABLE[(crc ^ byte) & 0xFF]
    return crc


# ==================== 帧封装/解封函数 ====================
def build_frame(func_code, cmd_list):
    """
    构建完整协议帧

    帧结构:
      [帧头][功能码][长度(LE16)][内容][校验][帧尾]
       1B     1B       2B         N*24B   1B     1B

    Args:
        func_code: 功能码 (区分烧录命令、调试命令等)
        cmd_list: 命令列表，每条为 24 字节 bytes

    Returns:
        完整帧 bytes
    """
    content = struct.pack('<H', len(cmd_list))  # 包号(2B)
    for cmd_bytes in cmd_list:
        if len(cmd_bytes) != CMD_SIZE:
            raise ValueError(f"CMD 大小必须是 {CMD_SIZE} 字节，实际 {len(cmd_bytes)}")
        content += cmd_bytes

    payload = bytes([func_code]) + content
    crc = crc8_maxim(payload)

    frame = bytes([FRAME_HEADER]) + payload + bytes([crc]) + bytes([FRAME_TAIL])
    return frame


def parse_frame(frame):
    """
    解析协议帧
    返回: dict {func_code, pkg_num, commands: [24B...], crc, valid}
    """
    if len(frame) < 7:
        raise ValueError(f"帧长度不足，至少需要7字节，实际{len(frame)}")

    if frame[0] != FRAME_HEADER:
        raise ValueError(f"帧头错误: 0x{frame[0]:02X} != 0x5B")
    if frame[-1] != FRAME_TAIL:
        raise ValueError(f"帧尾错误: 0x{frame[-1]:02X} != 0x5D")

    func_code = frame[1]
    length = struct.unpack('<H', frame[2:4])[0]  # 包号
    payload = frame[2:-2]
    crc_received = frame[-2]
    crc_calculated = crc8_maxim(payload)

    # 解析命令列表
    data_part = frame[4:-2]
    cmd_count = len(data_part) // CMD_SIZE
    commands = []
    for i in range(cmd_count):
        commands.append(data_part[i * CMD_SIZE:(i + 1) * CMD_SIZE])

    return {
        'func_code': func_code,
        'pkg_num': length,
        'commands': commands,
        'crc_received': crc_received,
        'crc_calculated': crc_calculated,
        'valid': crc_received == crc_calculated,
    }
