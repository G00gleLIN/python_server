# -*- coding: utf-8 -*-
"""端到端测试：解析 .sb3 → 生成 CMD 命令帧"""
import json, zipfile, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from block_parser import BlockParser
from cmd_builder import CmdBuilder

sb3_path = r'F:\myScratch\Scratch作品3.sb3'
with zipfile.ZipFile(sb3_path) as z:
    pj = json.load(z.open('project.json'))

p = BlockParser()
for idx, t in enumerate(pj.get('targets', [])):
    p.parse_target(t, idx)

print(f'解析完成: {len(p.cmd_data)} 个积木块收集到CMD数据')
print(f'变量: {list(p.variables_found.keys())}')
print(f'列表: {list(p.lists_found.keys())}')
print()

if p.cmd_data:
    builder = CmdBuilder()
    result = builder.build_commands(
        block_list=p.cmd_data,
        variables=p.variables_found,
        lists=p.lists_found,
    )
    stats = result['stats']
    print(f'CMD 命令: {stats["total_cmds"]} 条')
    print(f'帧长度: {len(result["frame"])} 字节')
    print(f'错误数: {stats["error_count"]}')
    print()
    
    hex_strings = result['cmd_hex_strings']
    for i in range(min(10, len(hex_strings))):
        print(f'  CMD[{i+1}]: {hex_strings[i]}')
    if len(hex_strings) > 10:
        print(f'  ... 共 {len(hex_strings)} 条')
else:
    print('没有收集到CMD数据!')
