#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, sys, os, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from block_parser import BlockParser

sb3 = r"F:\myScratch\Scratch作品3.sb3"
with zipfile.ZipFile(sb3) as z:
    pj = json.load(z.open('project.json'))

p = BlockParser()
for idx, t in enumerate(pj.get('targets', [])):
    p.parse_target(t, idx)

# 只输出包含"条件"或"repeat_until"的行
print("\n" + "="*70)
print("🔍 条件执行相关输出:")
print("="*70)
for line in p.output_lines:
    if '条件' in line or 'until' in line or '🔁' in line or '[条件]' in line:
        print(line)
print("="*70)
