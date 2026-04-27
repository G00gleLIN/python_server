#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 generate_commands_data 的逐条打印功能"""
import json, zipfile, sys
sys.path.insert(0, '.')

from block_server import BlockParseServer

server = BlockParseServer()
sb3_path = r'F:\myScratch\Scratch作品3.sb3'

with zipfile.ZipFile(sb3_path) as z:
    pj = json.load(z.open('project.json'))

result = server.generate_commands_data(pj)

print(f'\n返回状态: {result["status"]}')
print(f'cmd_details 条数: {len(result["cmd_details"])}')

if result['cmd_details']:
    print('\n前3条详情示例:')
    for i, d in enumerate(result['cmd_details'][:3]):
        print(f'  CMD[{i+1}]:')
        for line in d:
            print(f'      {line}')
