# -*- coding: utf-8 -*-
"""
CMD 命令构建器

将解析后的积木块数据转换为协议帧（24字节命令 + 帧封装）
依赖: cmd_protocol.py (协议常量定义)
"""

import struct
import json
from cmd_protocol import (
    CMD_SIZE, TM_VALUE, TM_PROGRAM, TM_HARDWARE,
    VAL_TYPE_I32, VAL_TYPE_FLOAT, VAL_TYPE_STRING, VAL_TYPE_BOOL,
    CONS_TYPE_I32, CONS_TYPE_FLOAT, CONS_TYPE_STRING, CONS_TYPE_BOOL,
    build_param_set, parse_param_set,
    build_ind, parse_ind,
    OPCODE_TO_CMD, MATHOP_MAP, INPUT_NAME_MAP,
    crc8_maxim, build_frame, parse_frame,
)


class CmdBuilder:
    """积木 → CMD命令 构建器"""

    def __init__(self):
        self.prog_ind = 0        # 程序序号计数器
        self.var_table = {}       # 变量名 → 变量表索引
        self.list_table = {}      # 列表名 → 列表表索引
        self.cmds = []            # 已生成的命令列表
        self.errors = []          # 错误信息列表

    def reset(self):
        """重置构建器状态"""
        self.prog_ind = 0
        self.var_table = {}
        self.list_table = {}
        self.cmds = []
        self.errors = []

    # ──────────────────────────────
    # 公共接口
    # ──────────────────────────────

    def build_commands(self, block_list, variables=None, lists=None):
        """
        将积木块列表转换为CMD命令帧

        Args:
            block_list: 积木块列表，每项为 dict {
                'step': int,              # 步骤序号
                'opcode': str,           # Scratch opcode
                'task_id': int,          # 任务编号(1-8)
                'inputs': dict,          # 输入参数 {name: value}
                'fields': dict,          # 字段参数 {name: value}
                'is_nested': bool,       # 是否嵌套积木
                'has_return': bool,      # 是否有返回值
                'description': str,      # 描述文本
            }
            variables: dict {var_name: var_id} - 目标中的变量定义
            lists: dict {list_name: list_id} - 目标中的列表定义

        Returns:
            dict {
                'commands': [bytes...],   # 24字节命令列表
                'frame': bytes,           # 完整协议帧
                'hex_strings': [str...],  # 十六进制字符串表示
                'errors': [str...],       # 错误/警告列表
                'stats': dict,            # 统计信息
            }
        """
        self.reset()

        # 1. 注册变量和列表
        if variables:
            for idx, (var_name, _) in enumerate(variables.items()):
                self.var_table[var_name] = idx
        if lists:
            for idx, (list_name, _) in enumerate(lists.items()):
                self.list_table[list_name] = idx

        # 2. 逐个处理积木块
        for block_info in block_list:
            cmd = self._build_single_cmd(block_info)
            if cmd is not None:
                self.cmds.append(cmd)

        # 3. 封装为完整帧
        frame = build_frame(func_code=0x01, cmd_list=self.cmds)

        hex_strs = []
        for c in self.cmds:
            hex_strs.append(c.hex(' ').upper())

        return {
            'commands': self.cmds,
            'frame': frame,
            'frame_hex': frame.hex(' ').upper(),
            'cmd_hex_strings': hex_strs,
            'errors': self.errors,
            'stats': {
                'total_cmds': len(self.cmds),
                'total_vars': len(self.var_table),
                'total_lists': len(self.list_table),
                'error_count': len(self.errors),
            },
        }

    # ──────────────────────────────
    # 核心构建逻辑
    # ──────────────────────────────

    def _build_single_cmd(self, block_info):
        """将单个积木块转换为24字节CMD命令"""
        opcode = block_info.get('opcode', '')
        task_id = block_info.get('task_id', 0)
        step = block_info.get('step', 0)
        inputs = block_info.get('inputs', {})
        fields = block_info.get('fields', {})
        is_nested = block_info.get('is_nested', False)
        has_return = block_info.get('has_return', False)

        # 查找映射
        mapping = OPCODE_TO_CMD.get(opcode)
        if mapping is None:
            self.errors.append(f"未映射的 opcode: {opcode}")
            return None

        type_main, type_sub_base = mapping

        # 特殊处理: operator_mathop 需要动态确定 type_sub
        if opcode == 'operator_mathop':
            operator_field = fields.get('OPERATOR', '')
            type_sub = MATHOP_MAP.get(operator_field)
            if type_sub is None:
                self.errors.append(f"未知的 mathop 运算符: {operator_field}")
                return None
        else:
            type_sub = type_sub_base

        if type_sub is None:
            self.errors.append(f"opcode {opcode} 缺少 type_sub")
            return None

        # 分配程序序号
        self.prog_ind += 1
        ind_val = build_ind(self.prog_ind, task_id)

        # 解析参数
        param_data = self._parse_params(opcode, inputs, fields, is_nested, has_return)

        # 构建24字节命令
        cmd_bytes = self._assemble_24byte(
            type_main=type_main,
            type_sub=type_sub,
            ind=ind_val,
            param_set_val=param_data['param_set'],
            buff=param_data['buff'],
            extend=param_data.get('extend', 0),
            buff_len=param_data.get('buff_len', 0),
        )

        return cmd_bytes

    def _parse_params(self, opcode, inputs, fields, is_nested=False, has_return=False):
        """
        解析积木参数，生成 param_set 和 buff 数据

        Returns:
            dict {
                'param_set': uint16,
                'buff': bytes (最多18字节),
                'extend': uint16,
                'buff_len': uint16,
            }
        """
        input_map = INPUT_NAME_MAP.get(opcode, {})

        # 初始化参数状态
        val_is_var = [False, False, False]     # 参数是否为变量
        val_values = [None, None, None]         # 参数值(数值或变量名)
        val_types = [CONS_TYPE_I32, CONS_TYPE_I32, CONS_TYPE_I32]  # 参数常量类型
        next_flag = 0
        r_flag = 1 if has_return else 0

        # 遍历所有输入，按 INPUT_NAME_MAP 映射到位置
        for inp_name, inp_value in inputs.items():
            pos = input_map.get(inp_name)  # 1, 2 or 3
            if pos is None:
                continue
            idx = pos - 1  # 转为0-based

            # 判断是变量还是常量
            if isinstance(inp_value, str):
                # 检查是否为变量引用
                if inp_value in self.var_table:
                    val_is_var[idx] = True
                    val_values[idx] = self.var_table[inp_value]
                    val_types[idx] = CONS_TYPE_I32
                elif inp_value.startswith('__var__'):
                    val_is_var[idx] = True
                    try:
                        val_values[idx] = int(inp_value.split('_')[-1])
                    except (ValueError, IndexError):
                        val_values[idx] = 0
                    val_types[idx] = CONS_TYPE_I32
                else:
                    # 尝试转为数字常量
                    try:
                        if '.' in str(inp_value):
                            val_values[idx] = float(inp_value)
                            val_types[idx] = CONS_TYPE_FLOAT
                        elif isinstance(inp_value, str) and inp_value.startswith('__var'):
                            # 变量标记: 记录为变量引用
                            var_name = inp_value.replace('__var__', '').strip('_')
                            val_is_var[idx] = True
                            val_values[idx] = self.var_table.get(var_name, 0)
                            val_types[idx] = CONS_TYPE_I32
                        else:
                            val_values[idx] = int(inp_value)
                            val_types[idx] = CONS_TYPE_I32
                    except (ValueError, TypeError):
                        val_values[idx] = inp_value
                        val_types[idx] = CONS_TYPE_STRING
            elif isinstance(inp_value, (int, float)):
                val_values[idx] = inp_value
                val_types[idx] = CONS_TYPE_FLOAT if isinstance(inp_value, float) else CONS_TYPE_I32
            else:
                val_values[idx] = inp_value
                val_types[idx] = CONS_TYPE_STRING

        # 处理循环/条件跳转标志 (if/loop/break 有 next_flag=1)
        loop_control_opcodes = {'control_repeat', 'control_repeat_until',
                                'control_while', 'control_forever', 'control_if',
                                'control_if_else', 'control_stop'}
        if opcode in loop_control_opcodes:
            next_flag = 1

        # 构建 param_set
        param_set = build_param_set(
            next_flag=next_flag,
            r_flag=r_flag,
            val1_is_var=val_is_var[0],
            val2_is_var=val_is_var[1],
            val3_is_var=val_is_var[2],
            type_val1=val_types[0],
            type_val2=val_types[1],
            type_val3=val_types[2],
        )

        # 构建 buff 内容 (18 字节)
        buff = bytearray(18)
        offset = 0

        for i in range(3):
            if val_values[i] is None:
                continue

            if val_is_var[i]:
                # 变量: 存储变量索引 (2字节 LE)
                struct.pack_into('<H', buff, offset, int(val_values[i]) & 0xFFFF)
                offset += 2
            else:
                # 常量: 根据类型存储
                v = val_values[i]
                if val_types[i] == CONS_TYPE_I32:
                    if offset + 4 <= 18:
                        struct.pack_into('<i', buff, offset, int(v))
                        offset += 4
                elif val_types[i] == CONS_TYPE_FLOAT:
                    if offset + 4 <= 18:
                        struct.pack_into('<f', buff, offset, float(v))
                        offset += 4
                elif val_types[i] == CONS_TYPE_STRING:
                    # 字符串常量: 最多16字节
                    s = str(v).encode('utf-8')[:16]
                    buff[offset:offset+len(s)] = s
                    offset += min(len(s), 16)
                elif val_types[i] == CONS_TYPE_BOOL:
                    if offset < 18:
                        buff[offset] = 1 if v else 0
                        offset += 1

        buff_len = offset
        extend = 0

        return {
            'param_set': param_set,
            'buff': bytes(buff),
            'extend': extend,
            'buff_len': buff_len,
        }

    def _assemble_24byte(self, type_main, type_sub, ind, param_set_val,
                          buff, extend=0, buff_len=0):
        """
        组装24字节命令

        C 结构体 DEF_FLASH_CMD_ST 布局 (共24字节):
          type_main(1) + type_sub(1) + ind(2) + st_param(20) = 24字节

        st_param 根据模式有两种布局:
        ── TM_VALUE 模式 (变量赋值):
          [extend(LE16)][len(LE16)][buff(16B)]
        ── TM_PROGRAM 模式 (程序执行):
          [param_set(LE16)][buff(18B)]
        """
        cmd = bytearray(CMD_SIZE)

        # 固定头部
        cmd[0] = type_main & 0xFF
        cmd[1] = type_sub & 0xFF
        struct.pack_into('<H', cmd, 2, ind & 0xFFFF)  # ind

        if type_main == TM_VALUE:
            # 变量模式: extend + len + buff(16)
            struct.pack_into('<H', cmd, 4, extend & 0xFFFF)
            struct.pack_into('<H', cmd, 6, buff_len & 0xFFFF)
            cmd[7:23] = buff[:16]
        else:
            # 程序/硬件模式: param_set + buff(18)
            struct.pack_into('<H', cmd, 4, param_set_val & 0xFFFF)
            cmd[6:24] = buff[:18]

        return bytes(cmd)


# ──────────────────────────────
# 辅助函数
# ──────────────────────────────

def format_cmd_hex(cmd_bytes):
    """格式化单条CMD为可读十六进制字符串"""
    parts = [
        f"type_main=0x{cmd_bytes[0]:02X}",
        f"sub=0x{cmd_bytes[1]:02X}",
        f"ind={struct.unpack_from('<H', cmd_bytes, 2)[0]}",
        f"ps=0x{struct.unpack_from('<H', cmd_bytes, 4)[0]:04X}",
        f"ext={struct.unpack_from('<H', cmd_bytes, 6)[0]}",
        f"len={struct.unpack_from('<H', cmd_bytes, 8)[0]}",
        f"data={' '.join(f'{b:02X}' for b in cmd_bytes[9:25])}",
    ]
    return " | ".join(parts)


def decode_cmd_detail(cmd_bytes):
    """解码24字节CMD命令为详细字典"""
    if len(cmd_bytes) < CMD_SIZE:
        return {'error': f'长度不足 {len(cmd_bytes)}'}

    ps = parse_param_set(struct.unpack_from('<H', cmd_bytes, 4)[0])
    ind = parse_ind(struct.unpack_from('<H', cmd_bytes, 2)[0])

    return {
        'type_main': cmd_bytes[0],
        'type_sub': cmd_bytes[1],
        'ind': ind,
        'param_set': ps,
        'extend': struct.unpack_from('<H', cmd_bytes, 6)[0],
        'length': struct.unpack_from('<H', cmd_bytes, 8)[0],
        'data': cmd_bytes[9:25].hex(' ').upper(),
    }


# ==================== 测试入口 ====================
if __name__ == '__main__':
    print("=" * 60)
    print("CMD 命令构建器测试")
    print("=" * 60)

    builder = CmdBuilder()

    # 测试1: 变量赋值 X = 100 (对照表示例 6.1)
    print("\n--- 测试1: X = 100 ---")
    test_blocks1 = [{
        'step': 1,
        'opcode': 'data_setvariableto',
        'task_id': 1,
        'inputs': {'VALUE': 100},
        'fields': {},
        'is_nested': False,
        'has_return': False,
    }]
    result1 = builder.build_commands(test_blocks1, variables={'X': 'var_x'})
    print(f"CMD Hex: {result1['cmd_hex_strings'][0]}")
    print(f"Detail: {decode_cmd_detail(result1['commands'][0])}")

    # 重置
    builder.reset()

    # 测试2: 加法 Y = X + 10 (对照表示例 6.2)
    print("\n--- 测试2: Y = X + 10 ---")
    test_blocks2 = [
        {'step': 1, 'opcode': 'operator_add', 'task_id': 1,
         'inputs': {'NUM1': '__var_X__', 'NUM2': 10}, 'fields': {},
         'is_nested': True, 'has_return': True},
    ]
    result2 = builder.build_commands(test_blocks2, variables={'X': 'var_x'})
    if result2['commands']:
        print(f"CMD Hex: {result2['cmd_hex_strings'][0]}")
        print(f"Detail: {decode_cmd_detail(result2['commands'][0])}")

    # 测试3: CRC8 和帧封装
    print("\n--- 测试3: 帧封装 ---")
    builder.reset()
    test_blocks3 = [
        {'step': 1, 'opcode': 'data_setvariableto', 'task_id': 1,
         'inputs': {'VALUE': 100}, 'fields': {}, 'is_nested': False, 'has_return': False},
        {'step': 2, 'opcode': 'operator_add', 'task_id': 1,
         'inputs': {'NUM1': 5, 'NUM2': 3}, 'fields': {}, 'is_nested': True, 'has_return': True},
    ]
    result3 = builder.build_commands(test_blocks3)
    print(f"总命令数: {result3['stats']['total_cmds']}")
    print(f"帧长度: {len(result3['frame'])} 字节")
    print(f"帧Hex:\n{result3['frame_hex']}")

    # 验证帧解析
    parsed = parse_frame(result3['frame'])
    print(f"\n帧解析: valid={parsed['valid']}, func_code={parsed['func_code']}, "
          f"cmds={len(parsed['commands'])}")

    print("\n" + "=" * 60)
    print("测试完成!")
