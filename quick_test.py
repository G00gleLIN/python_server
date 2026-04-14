#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, sys, os, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from block_parser import BlockParser

sb3 = r"F:\myScratch\Scratch作品3.sb3"
with zipfile.ZipFile(sb3) as z:
    pj = json.load(z.open('project.json'))

p = BlockParser()

# 直接调用解析 targets
for idx, t in enumerate(pj.get('targets', [])):
    p.parse_target(t, idx)

out = '\n'.join(p.output_lines)
print("\n" + "="*60)
if '🔁' in out or 'repeat_until' in out or '重复执行直到' in out:
    print("✅ SUCCESS: control_repeat_until 已正确解析!")
else:
    print("❌ FAIL: 未找到 control_repeat_until")
print("="*60)
