#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
积木解析调试工具
支持 VSCode Debug 模式，可设置断点逐步调试 block_parser.py

使用方法:
  1. 在 VSCode 中打开此文件
  2. 按 F5 启动调试
  3. 在 block_parser.py 中设置断点
  4. 逐步执行查看解析过程
"""

import json
import sys
import os
import zipfile

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from block_parser import BlockParser


class DebugTool:
    """积木解析调试工具"""
    
    def __init__(self, sb3_path=None):
        # 默认路径，可通过 VSCode 调试配置修改
        self.sb3_path = sb3_path or r"F:\myScratch\Scratch作品3.sb3"
        self.project_data = None
        self.parser = BlockParser()
    
    def load_sb3(self):
        """加载 .sb3 文件并提取 project.json"""
        if not os.path.exists(self.sb3_path):
            print(f"❌ 文件不存在: {self.sb3_path}")
            return False
        
        print(f"📂 加载文件: {self.sb3_path}")
        
        try:
            # .sb3 是 ZIP 格式，提取 project.json
            with zipfile.ZipFile(self.sb3_path, 'r') as z:
                if 'project.json' not in z.namelist():
                    print("❌ 文件中未找到 project.json")
                    return False
                
                with z.open('project.json') as f:
                    self.project_data = json.load(f)
            
            print(f"✅ 加载成功")
            print(f"   目标数量: {len(self.project_data.get('targets', []))}")
            return True
            
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return False
    
    def find_blocks_by_opcode(self, opcode):
        """查找指定 opcode 的所有积木"""
        results = []
        
        for target in self.project_data.get('targets', []):
            blocks = target.get('blocks', {})
            for bid, block in blocks.items():
                if block.get('opcode') == opcode:
                    results.append({
                        'target': target.get('name', 'Unknown'),
                        'block_id': bid,
                        'block': block
                    })
        
        return results
    
    def print_block_details(self, block_info):
        """打印积木详细信息"""
        print(f"\n{'='*70}")
        print(f"🎯 目标: {block_info['target']}")
        print(f"🆔 ID: {block_info['block_id']}")
        print(f"🧱 Opcode: {block_info['block'].get('opcode')}")
        print(f"📝 完整数据:")
        print(json.dumps(block_info['block'], ensure_ascii=False, indent=2))
        print(f"{'='*70}")
    
    def parse_project(self):
        """解析项目（可在此方法内设置断点）"""
        print(f"\n{'='*70}")
        print(f"🧱 开始解析项目")
        print(f"{'='*70}\n")
        
        # 重置解析器
        self.parser = BlockParser()
        self.parser.execution_order = 0
        self.parser.output_lines = []
        
        # 解析所有目标
        targets = self.project_data.get('targets', [])
        for idx, target in enumerate(targets):
            self.parser.parse_target(target, idx)
        
        # 输出总结
        print(f"\n{'='*70}")
        print(f"✅ 解析完成！共 {self.parser.execution_order} 个执行步骤")
        print(f"{'='*70}\n")
        
        return self.parser.output_lines
    
    def run(self, opcode_filter=None):
        """运行调试工具
        
        Args:
            opcode_filter: 可选，只查找指定 opcode 的积木
        """
        print("🔧 积木解析调试工具")
        print(f"{'='*70}\n")
        
        # 1. 加载文件
        if not self.load_sb3():
            return
        
        # 2. 查找特定积木
        if opcode_filter:
            print(f"\n🔍 查找 opcode: {opcode_filter}")
            results = self.find_blocks_by_opcode(opcode_filter)
            
            if results:
                print(f"✅ 找到 {len(results)} 个积木:")
                for r in results:
                    self.print_block_details(r)
            else:
                print(f"❌ 未找到 opcode 为 {opcode_filter} 的积木")
        
        # 3. 完整解析（可在此处设置断点调试 block_parser.py）
        input("\n⏸️ 按 Enter 开始完整解析（可在此之前设置断点）...")
        
        output = self.parse_project()
        
        # 4. 检查输出
        print("\n📊 解析结果检查:")
        print(f"{'='*70}")
        
        # 输出所有解析行
        for line in output:
            print(f"   {line}")
        
        print(f"\n{'='*70}")
        
        # 统计信息
        stats = {
            '总步骤': self.parser.execution_order,
            '输出行数': len(output),
        }
        
        print("\n📈 统计信息:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
        
        print(f"\n{'='*70}")
        print("✅ 调试工具执行完成")
        print("💡 提示: 在 block_parser.py 的 _execute_block / _execute_loop 等方法中设置断点可逐步调试")


def main():
    """主函数 - VSCode 调试入口点"""
    
    # ===== 调试配置区 =====
    # 修改此处的路径来测试不同的 .sb3 文件
    SB3_PATH = r"F:\myScratch\Scratch作品3.sb3"
    
    # 可选：只查找特定 opcode 的积木（设为 None 则不筛选）
    # 常用值: 'control_repeat_until', 'control_repeat', 'control_forever', 'control_if'
    OPCODE_FILTER = 'control_repeat_until'
    # =====================
    
    # 创建调试工具实例
    debugger = DebugTool(sb3_path=SB3_PATH)
    
    # 运行调试
    # 💡 在此行之后设置断点，可以逐步进入 parse_project() 查看解析过程
    debugger.run(opcode_filter=OPCODE_FILTER)


if __name__ == '__main__':
    main()
