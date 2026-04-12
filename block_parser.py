# -*- coding: utf-8 -*-
"""
Scratch project.json 积木块解析器
按执行逻辑逐个解析积木块并输出解码信息
"""

import json
import os
import sys

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from block_config import (
    DECODE_OPCODES,
    SKIP_OPCODES,
    LOOP_OPCODES,
    CONDITION_OPCODES,
    EVENT_OPCODES,
    CATEGORY_MAP
)


class BlockParser:
    """积木块解析器"""
    
    def __init__(self):
        self.execution_order = 0  # 执行顺序计数器
        self.output_lines = []    # 输出日志
        
    def parse_project(self, project_json_path):
        """解析整个 project.json 文件"""
        print(f"\n{'='*70}")
        print(f"📋 开始解析 project.json")
        print(f"📂 文件: {project_json_path}")
        print(f"{'='*70}\n")
        
        # 读取 JSON 文件
        with open(project_json_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # 解析所有目标（舞台和角色）
        targets = project_data.get('targets', [])
        for idx, target in enumerate(targets):
            self.parse_target(target, idx)
        
        # 输出总结
        print(f"\n{'='*70}")
        print(f"✅ 解析完成！共 {self.execution_order} 个执行步骤")
        print(f"{'='*70}\n")
        
        return self.output_lines
    
    def parse_target(self, target, target_idx):
        """解析单个目标（舞台或角色）"""
        is_stage = target.get('isStage', False)
        name = target.get('name', '未命名')
        
        # 输出目标信息
        if is_stage:
            header = f"🎭 舞台 (Stage)"
        else:
            header = f"🎨 角色: {name}"
        
        print(f"\n{'─'*70}")
        print(f"{header}")
        print(f"{'─'*70}")
        
        self._log(0, f"{'='*60}")
        self._log(0, f"{header}")
        self._log(0, f"{'='*60}")
        
        # 解析变量
        self._parse_variables(target)
        
        # 解析列表
        self._parse_lists(target)
        
        # 解析积木块
        blocks = target.get('blocks', {})
        if blocks:
            print(f"\n🧱 积木块解析:")
            self._parse_blocks(blocks)
        else:
            print(f"\n📝 该目标没有积木块")
    
    def _parse_variables(self, target):
        """解析变量"""
        variables = target.get('variables', {})
        if variables:
            print(f"\n📊 变量:")
            for var_id, var_data in variables.items():
                var_name = var_data[0] if isinstance(var_data, list) else str(var_data)
                var_value = var_data[1] if isinstance(var_data, list) else ""
                print(f"   📦 {var_name} = {var_value}")
                self._log(0, f"📊 变量: {var_name} = {var_value}")
    
    def _parse_lists(self, target):
        """解析列表"""
        lists = target.get('lists', {})
        if lists:
            print(f"\n📋 列表:")
            for list_id, list_data in lists.items():
                list_name = list_data[0] if isinstance(list_data, list) else str(list_data)
                list_items = list_data[1] if isinstance(list_data, list) else []
                print(f"   📋 {list_name} = {list_items}")
                self._log(0, f"📋 列表: {list_name} = {list_items}")
    
    def _parse_blocks(self, blocks):
        """解析所有积木块 - 多任务独立工作序列"""
        # 1. 找到所有顶级积木（任务入口）
        top_level_blocks = []
        for block_id, block in blocks.items():
            if block.get('topLevel', False):
                top_level_blocks.append((block_id, block))
        
        if not top_level_blocks:
            return

        self._log(0, f"🧱 积木块解析:")
        
        # 最多记录 8 个任务
        task_count = min(len(top_level_blocks), 8)
        self._log(0, f"🌐 #0 全局任务初始化 (共 {task_count} 个并行任务)")
        
        # 2. 依次处理每个主流程（任务）
        for task_id, (block_id, block) in enumerate(top_level_blocks, start=1):
            # 初始化当前任务上下文
            self.current_task_id = task_id
            self.current_step = 0  # 重置当前任务的工作序号
            
            self._log(0, f"📦 [任务 {task_id}] #0 创建任务/初始化")
            
            # 3. 执行该任务下的积木 (序号从 1 开始累加)
            self._execute_block(block_id, block, blocks, indent=0)
            
            self._log(0, f"🏁 [任务 {task_id}] 工作序列结束\n")

    def _execute_block(self, block_id, block, all_blocks, indent=0, is_nested_input=False):
        """递归执行积木块 - 严格白名单模式 + 任务独立计数"""
        opcode = block.get('opcode', '')
        description = DECODE_OPCODES.get(opcode)
        
        # 1. 白名单过滤
        if opcode not in DECODE_OPCODES:
            pass
        else:
            # ⭐ 核心修正：必须在获取 step 之前先执行嵌套积木！
            # 否则嵌套积木的序号会比父积木大，这违反了依赖逻辑。
            
            # 2.1 特殊处理：循环（循环通常不包含返回值嵌套，先分配序号）
            if opcode in LOOP_OPCODES:
                self.current_step += 1
                self._execute_loop(block_id, block, all_blocks, indent, self.current_step)
                return 

            # 2.2 特殊处理：条件
            if opcode in CONDITION_OPCODES:
                self.current_step += 1
                self._execute_condition(block_id, block, all_blocks, indent, self.current_step)
                return

            # 2.3 普通积木：先解析嵌套参数
            # 这一步会递归调用嵌套积木，导致 current_step 增加（例如变为 #6）
            params = self._parse_block_inputs(block, all_blocks, indent)
            
            # 2.4 嵌套积木执行完后，父积木才分配序号（例如变为 #7）
            self.current_step += 1
            step = self.current_step
            
            # 2.5 输出日志
            self._log(indent, f"📦 [任务 {self.current_task_id}] #{step} {description}{params}")

        # 3. 继续执行下一个积木
        if not is_nested_input:
            next_id = block.get('next')
            if next_id and next_id in all_blocks:
                next_block = all_blocks[next_id]
                self._execute_block(next_id, next_block, all_blocks, indent)

    def _execute_loop(self, block_id, block, all_blocks, indent, step):
        """执行循环类积木"""
        opcode = block.get('opcode', '')
        description = DECODE_OPCODES.get(opcode, opcode)
        
        # 获取循环次数
        times = self._get_input_value(block, 'TIMES', all_blocks) or '无限'
        
        self._log(indent, f"📦 [任务 {self.current_task_id}] #{step} 🔄 开始循环: 重复 {times} 次")
        self._log(indent, f"   ┌─ 循环体")
        
        # 执行循环体内的积木
        substack_id = block.get('inputs', {}).get('SUBSTACK', [None, None])[1]
        if substack_id and substack_id in all_blocks:
            substack_block = all_blocks[substack_id]
            self._execute_block(substack_id, substack_block, all_blocks, indent + 4)
        
        self._log(indent, f"   └─ 循环体结束")
        
        # 继续执行下一个积木
        next_id = block.get('next')
        if next_id and next_id in all_blocks:
            next_block = all_blocks[next_id]
            self._execute_block(next_id, next_block, all_blocks, indent)

    def _execute_condition(self, block_id, block, all_blocks, indent, step):
        """执行条件类积木（支持 if/else）"""
        opcode = block.get('opcode', '')
        description = DECODE_OPCODES.get(opcode, opcode)
        
        self._log(indent, f"📦 [任务 {self.current_task_id}] #{step} ❓ 条件判断")
        
        # 1. 执行“如果”分支 (SUBSTACK)
        substack_id = block.get('inputs', {}).get('SUBSTACK', [None, None])[1]
        if substack_id and substack_id in all_blocks:
            self._log(indent, f"   ┌─ 如果分支")
            substack_block = all_blocks[substack_id]
            self._execute_block(substack_id, substack_block, all_blocks, indent + 4)
            self._log(indent, f"   └─ 如果分支结束")
            
        # 2. ⭐ 新增：执行“否则”分支 (SUBSTACK2)
        substack2_id = block.get('inputs', {}).get('SUBSTACK2', [None, None])[1]
        if substack2_id and substack2_id in all_blocks:
            self._log(indent, f"   ┌─ 否则分支")
            substack2_block = all_blocks[substack2_id]
            self._execute_block(substack2_id, substack2_block, all_blocks, indent + 4)
            self._log(indent, f"   └─ 否则分支结束")
        
        # 3. 继续执行下一个积木
        next_id = block.get('next')
        if next_id and next_id in all_blocks:
            next_block = all_blocks[next_id]
            self._execute_block(next_id, next_block, all_blocks, indent)

    def _parse_block_inputs(self, block, all_blocks, indent=0):
        """解析积木块的输入参数（先执行嵌套积木）"""
        inputs = block.get('inputs', {})
        if not inputs:
            return ""

        param_parts = []

        for input_name, input_data in inputs.items():
            if not input_data:
                continue

            input_type = input_data[0] if len(input_data) > 0 else None

            # 类型 1: 普通值或影子积木引用
            if input_type == 1:
                value_data = input_data[1] if len(input_data) > 1 else None
                if isinstance(value_data, list):
                    # 直接值 [类型, 值]
                    value_type = value_data[0]
                    value = value_data[1]
                    param_parts.append(f"{input_name}={value}")
                elif isinstance(value_data, str):
                    # 影子积木引用，需要递归解析
                    if value_data in all_blocks:
                        shadow_block = all_blocks[value_data]
                        shadow_value = self._get_shadow_value(shadow_block)
                        if shadow_value is not None:
                            param_parts.append(f"{input_name}={shadow_value}")

            # 类型 2: 子积木堆（用于循环、条件等）
            elif input_type == 2:
                substack_id = input_data[1] if len(input_data) > 1 else None
                if substack_id:
                    param_parts.append(f"{input_name}=[子积木堆]")

            # 类型 3: 积木引用（用于嵌套积木）
            # ⭐ 关键：先执行嵌套积木，返回值给父积木
            elif input_type == 3:
                nested_block_id = input_data[1] if len(input_data) > 1 else None
                if nested_block_id and isinstance(nested_block_id, str) and nested_block_id in all_blocks:
                    nested_block = all_blocks[nested_block_id]
                    # 先执行嵌套积木（会输出 #12）
                    nested_value = self._execute_nested_block(nested_block_id, nested_block, all_blocks, indent + 2)
                    # 然后返回值给父积木
                    if nested_value is not None:
                        param_parts.append(f"{input_name}={nested_value}")
        
        if param_parts:
            return f" ({', '.join(param_parts)})"
        return ""
    
    def _execute_nested_block(self, block_id, block, all_blocks, indent):
        """执行嵌套积木并返回值"""
        opcode = block.get('opcode', '')
        
        # 检查白名单
        if opcode not in DECODE_OPCODES:
            return "[未配置]"

        # 增加工作序号
        self.current_step += 1
        step = self.current_step
        
        description = DECODE_OPCODES.get(opcode, opcode)
        
        # 解析参数
        params = self._parse_block_inputs(block, all_blocks, indent)
        
        # 输出日志（带上任务 ID 和序号）
        self._log(indent, f"📦 [任务 {self.current_task_id}] #{step} [嵌套] {description}{params}")
        
        # 根据积木类型返回值
        if opcode == 'operator_add':
            num1 = self._get_input_value(block, 'NUM1', all_blocks)
            num2 = self._get_input_value(block, 'NUM2', all_blocks)
            if num1 is not None and num2 is not None:
                result = float(num1) + float(num2)
                self._log(indent, f"     → 返回值: {result}")
                return result
        
        return "[嵌套积木执行]"
    
    def _get_shadow_value(self, block):
        """获取影子积木的值"""
        if not block:
            return None
        
        fields = block.get('fields', {})
        if fields:
            # 返回第一个字段的值
            for field_name, field_data in fields.items():
                if isinstance(field_data, list):
                    return field_data[0]
                return field_data
        
        return None
    
    def _get_input_value(self, block, input_name, all_blocks):
        """获取输入值"""
        inputs = block.get('inputs', {})
        input_data = inputs.get(input_name)
        
        if not input_data:
            return None
        
        input_type = input_data[0] if len(input_data) > 0 else None
        
        if input_type == 1:
            value_data = input_data[1] if len(input_data) > 1 else None
            if isinstance(value_data, list):
                return value_data[1]
            elif isinstance(value_data, str) and value_data in all_blocks:
                shadow_block = all_blocks[value_data]
                return self._get_shadow_value(shadow_block)
        
        return None
    
    def _log(self, indent, message):
        """输出日志"""
        prefix = " " * indent
        full_message = f"{prefix}{message}"
        print(full_message)
        self.output_lines.append(full_message)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python block_parser.py <project.json 文件路径>")
        print("\n示例: python block_parser.py F:\\myScratch\\extracted\\project.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if not os.path.exists(json_path):
        print(f"❌ 错误: 文件不存在 - {json_path}")
        sys.exit(1)
    
    parser = BlockParser()
    parser.parse_project(json_path)


if __name__ == '__main__':
    main()
