# -*- coding: utf-8 -*-
"""
积木块解析配置文件
定义哪些积木需要解码输出，哪些不需要
"""

# 需要解码输出的积木类型
DECODE_OPCODES = {
    # === 控制类 ===
    "control_wait": "⏱️ 等待",
    "control_repeat": "🔄 重复执行",
    "control_forever": "♾️ 重复执行（无限）",
    "control_if": "❓ 如果",
    "control_if_else": "❓ 如果...否则",
    "control_wait_until": "⏱️ 等待直到",
    "control_stop": "🛑 停止",
    "control_start_as_clone": "👶 当作为克隆体启动时",
    "control_create_clone_of": "📋 创建克隆体",
    "control_delete_this_clone": "🗑️ 删除此克隆体",
    "control_all_at_once": "⚡ 同时执行",
    
    
    # === 运算符类 ===
    "operator_add": "➕ 加法",
    "operator_subtract": "➖ 减法",
    "operator_multiply": "✖️ 乘法",
    "operator_divide": "➗ 除法",
    "operator_random": "🎲 随机数",
    "operator_gt": "▶️ 大于",
    "operator_lt": "◀️ 小于",
    "operator_equals": "⚖️ 等于",
    "operator_and": "🔗 与",
    "operator_or": "🔗 或",
    "operator_not": "❌ 非",
    "operator_join": "🔗 连接字符串",
    "operator_letter_of": "🔤 字符串的第字符",
    "operator_length": "📏 长度",
    "operator_contains": "🔍 包含",
    "operator_mod": "🔢 取余",
    "operator_round": "🔢 四舍五入",
    "operator_mathop": "🔢 数学运算",
    
    # === 数据类（变量和列表）===
    "data_setvariableto": "📦 变量设为",
    "data_changevariableby": "📦 变量增加",
    "data_showvariable": "👁️ 显示变量",
    "data_hidevariable": "🙈 隐藏变量",
    "data_addtolist": "📋 添加到列表",
    "data_deleteoflist": "🗑️ 删除列表项",
    "data_deletealloflist": "🗑️ 清空列表",
    "data_insertatlist": "📋 插入到列表",
    "data_replaceitemoflist": "📋 替换列表项",
    "data_itemoflist": "📊 列表项",
    "data_itemnumoflist": "📊 列表项编号",
    "data_lengthoflist": "📊 列表长度",
    "data_listcontainsitem": "🔍 列表包含",
    "data_showlist": "👁️ 显示列表",
    "data_hidelist": "🙈 隐藏列表",
    
    # === 自定义扩展类 ===
    "smartpi_whenInfraredPressed": "🔘 SmartPi 当红外按键按下",
    "smartpi_isAnyKeyPressed": "🔘 SmartPi 红外按键按下?",
    "smartpi_playNoteFor": "🎵 SmartPi 播放音符",
    "smartpi_setLEDColor": "💡 SmartPi 设置 LED 颜色",
    "smartpi_setLEDBrightness": "💡 SmartPi 设置 LED 亮度",
    "smartpi_motorOnFor": "🤖 SmartPi 电机运转",
    "smartpi_motorOn": "🤖 SmartPi 电机开启",
    "smartpi_motorOff": "🤖 SmartPi 电机关闭",
    "smartpi_setMotorPower": "⚡ SmartPi 设置电机功率",
    "smartpi_setMotorDirection": "🔄 SmartPi 设置电机转向",
    "smartpi_getDistance": "📏 SmartPi 距离",
    "smartpi_getAngle": "📐 SmartPi 角度",
    "smartpi_whenTilted": "📐 SmartPi 当倾斜",
    "smartpi_whenDistance": "📏 SmartPi 当距离比较",
    "smartpi_setTempo": "🎵 SmartPi 设置演奏速度",
    "smartpi_playSoundEffect": "🔊 SmartPi 演奏音效",
    "smartpi_getSensorValue": "📊 SmartPi 获取传感器值",
    "smartpi_getButtonState": "🔘 SmartPi 获取按钮状态",
    "smartpi_setMotorSpeed": "⚡ SmartPi 设置电机速度",
    "smartpi_motorForward": "⬆️ SmartPi 电机正转",
    "smartpi_motorBackward": "⬇️ SmartPi 电机反转",
    "smartpi_motorStop": "🛑 SmartPi 电机停止",
}

# 不需要解码输出的积木类型（通常是菜单、影子积木等）
SKIP_OPCODES = {
    # === 事件类 ===
    "event_whenflagclicked": "🟢 当绿旗被点击",
    "event_whenkeypressed": "⌨️ 当按键被按下",
    "event_whenthisspriteclicked": "🖱️ 当角色被点击",
    "event_whenbackdropswitchesto": "🎨 当背景切换到",
    "event_whengreaterthan": "📊 当大于",
    "event_whenbroadcastreceived": "📡 当接收到广播",
    "event_broadcast": "📤 发送广播",
    "event_broadcastandwait": "📤 发送广播并等待",
    
    # === 运动类 ===
    "motion_movesteps": "🚶 移动步数",
    "motion_turnright": "↩️ 右转角度",
    "motion_turnleft": "↪️ 左转角度",
    "motion_goto": "📍 移到位置",
    "motion_gotoxy": "📍 移到坐标",
    "motion_glideto": "🛫 滑行到",
    "motion_glidesecstoxy": "🛫 滑行到坐标",
    "motion_pointindirection": "🧭 面向方向",
    "motion_pointtowards": "🧭 面向角色",
    "motion_changexby": "↔️ X 坐标增加",
    "motion_setx": "↔️ X 坐标设为",
    "motion_changeyby": "↕️ Y 坐标增加",
    "motion_sety": "↕️ Y 坐标设为",
    "motion_ifonedgebounce": "🏀 碰到边缘就反弹",
    "motion_setrotationstyle": "🔄 设置旋转样式",
    "motion_xposition": "📊 X 坐标",
    "motion_yposition": "📊 Y 坐标",
    "motion_direction": "🧭 方向",
    
    # === 外观类 ===
    "looks_say": "💬 说出",
    "looks_sayforsecs": "💬 说出秒数",
    "looks_think": "💭 思考",
    "looks_thinkforsecs": "💭 思考秒数",
    "looks_show": "👁️ 显示",
    "looks_hide": "🙈 隐藏",
    "looks_switchcostumeto": "🎨 切换造型",
    "looks_nextcostume": "⏭️ 下一个造型",
    "looks_nextbackdrop": "⏭️ 下一个背景",
    "looks_switchbackdropto": "🎨 切换背景到",
    "looks_changeeffectby": "🎭 特效改变",
    "looks_seteffectto": "🎭 特效设为",
    "looks_cleargraphiceffects": "🧹 清除特效",
    "looks_changesizeby": "📏 大小改变",
    "looks_setsizeto": "📏 大小设为",
    "looks_gotofrontback": "📚 移到最前/后层",
    "looks_goforwardbackwardlayers": "📚 前移/后移层",
    "looks_size": "📊 大小",
    "looks_costumenumbername": "📊 造型编号/名称",
    "looks_backdropnumbername": "📊 背景编号/名称",
    
    # === 声音类 ===
    "sound_play": "🔊 播放声音",
    "sound_playuntildone": "🔊 播放声音直到完成",
    "sound_stopallsounds": "🔇 停止所有声音",
    "sound_changeeffectby": "🎵 音效改变",
    "sound_seteffectto": "🎵 音效设为",
    "sound_cleareffects": "🧹 清除音效",
    "sound_setvolumeto": "🔈 音量设为",
    "sound_changevolumeby": "🔈 音量改变",
    "sound_volume": "📊 音量",

    # === 侦测类 ===
    "sensing_touchingobject": "👆 碰到",
    "sensing_touchingcolor": "👆 碰到颜色",
    "sensing_coloristouchingcolor": "🎨 颜色碰到颜色",
    "sensing_distanceto": "📏 到...的距离",
    "sensing_askandwait": "❓ 询问并等待",
    "sensing_answer": "💬 回答",
    "sensing_keypressed": "⌨️ 按键按下",
    "sensing_mousedown": "🖱️ 鼠标按下",
    "sensing_mousex": "🖱️ 鼠标 X",
    "sensing_mousey": "🖱️ 鼠标 Y",
    "sensing_setdragmode": "🖱️ 设置拖拽模式",
    "sensing_loudness": "🎤 音量",
    "sensing_loud": "🎤 响度",
    "sensing_timer": "⏱️ 计时器",
    "sensing_resettimer": "⏱️ 重置计时器",
    "sensing_current": "📅 当前",
    "sensing_dayssince2000": "📅 2000年至今的天数",
    "sensing_username": "👤 用户名",

    # === 自定义扩展类 ===
    "wedo2_motorOnFor": "🤖 WeDo2 电机运转",
    "wedo2_motorOn": "🤖 WeDo2 电机启动",
    "wedo2_motorOff": "🤖 WeDo2 电机关闭",
    "wedo2_startMotorPower": "🤖 WeDo2 电机功率",
    "wedo2_setLightHue": "💡 WeDo2 灯光颜色",
    "wedo2_menu_MOTOR_ID": "🤖 WeDo2 电机选择",
    "wedo2_whenDistance": "🤖 WeDo2 当距离",
    "wedo2_whenTilted": "🤖 WeDo2 当倾斜",
    "wedo2_getDistance": "🤖 WeDo2 获取距离",
    "wedo2_getTiltAngle": "🤖 WeDo2 获取倾斜角度",

    # === 菜单类（仅提供选择值）===
    # "motion_pointtowards_menu",
    # "motion_glideto_menu",
    # "motion_goto_menu",
    # "looks_switchcostumeto_menu",
    # "looks_switchbackdropto_menu",
    # "looks_gotofrontback_menu",
    # "sound_play_menu",
    # "sound_sounds_menu",
    # "control_stop_menu",
    # "control_create_clone_of_menu",
    # "sensing_distanceto_menu",
    # "sensing_touchingobjectmenu",
    # "sensing_setdragmode_menu",
    # "sensing_current_menu",
    # "data_listcontents",
    
    # === 影子积木（仅提供值的占位符）===
    # 这些在代码中通过 shadow: true 标识
}

# 循环类积木（需要特殊处理开始和结束）
LOOP_OPCODES = {
    "control_repeat": "🔄 重复执行",
    "control_forever": "♾️ 重复执行（无限）",
}

# 条件类积木（需要特殊处理）
CONDITION_OPCODES = {
    "control_if": "❓ 如果",
    "control_if_else": "❓ 如果...否则",
}

# 事件类积木（通常是程序入口）
EVENT_OPCODES = {
    "event_whenflagclicked",
    "event_whenkeypressed",
    "event_whenthisspriteclicked",
    "event_whenbackdropswitchesto",
    "event_whenbroadcastreceived",
}

# 积木类别映射（用于分类输出）
CATEGORY_MAP = {
    "event": "🎯 事件",
    "motion": "🚶 运动",
    "looks": "🎨 外观",
    "sound": "🔊 声音",
    "control": "🎛️ 控制",
    "sensing": "📡 侦测",
    "operator": "🔢 运算符",
    "data": "📦 数据",
    "wedo2": "🤖 WeDo2",
    "smartpi": "🎵 SmartPi",
}
