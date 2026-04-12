#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
积木块解析 WebSocket 服务
前端通过 WebSocket 调用解析功能，支持实时解析和命令转换

依赖:
    pip install websockets

启动:
    python block_server.py
    python block_server.py 8765  # 自定义端口
"""

import asyncio
import json
import sys
import os
import atexit
import signal
from datetime import datetime
import websockets

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Logger:
    """安全的日志输出类，避免编码问题"""

    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}", flush=True)

    @staticmethod
    def success(msg):
        print(f"[OK] {msg}", flush=True)

    @staticmethod
    def error(msg):
        print(f"[ERROR] {msg}", flush=True, file=sys.stderr)

    @staticmethod
    def warning(msg):
        print(f"[WARN] {msg}", flush=True)

# 全局变量：保存服务器实例
server_instance = None

def cleanup_on_exit():
    """进程退出时自动执行的清理函数"""
    global server_instance
    if server_instance:
        Logger.info("正在关闭 WebSocket 服务...")
        # 断开所有客户端连接
        for ws in list(server_instance.clients):
            try:
                # 使用 asyncio 创建临时事件循环来关闭连接
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(ws.close())
                loop.close()
            except:
                pass
        server_instance.clients.clear()
        Logger.info("清理完成")
    sys.stdout.flush()
    sys.stderr.flush()

# 注册退出处理器
atexit.register(cleanup_on_exit)

# Windows 控制台事件处理
if sys.platform == 'win32':
    try:
        import ctypes
        from ctypes import wintypes

        # 定义控制台事件处理器
        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
        def console_handler(ctrl_type):
            if ctrl_type in (0, 2):  # CTRL_C_EVENT 或 CTRL_CLOSE_EVENT
                Logger.warning("收到停止信号，正在安全关闭...")
                cleanup_on_exit()
                return True
            return False

        # 注册控制台事件处理器
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.SetConsoleCtrlHandler(console_handler, True)
    except Exception as e:
        # 如果注册失败，忽略（不影响正常运行）
        pass

from block_parser import BlockParser


class BlockParseServer:
    """积木解析 WebSocket 服务器"""
    
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.parser = BlockParser()
        self.request_count = 0
    
    async def handle_client(self, websocket):
        """处理客户端连接"""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        Logger.success(f"[{datetime.now().strftime('%H:%M:%S')}] 客户端已连接: {client_addr}")
        Logger.info(f"   当前连接数: {len(self.clients)}")
        
        try:
            # 发送欢迎消息
            await websocket.send(json.dumps({
                'type': 'welcome',
                'message': '已连接到积木解析服务',
                'server_time': datetime.now().strftime('%H:%M:%S')
            }, ensure_ascii=False))
            
            # 处理消息
            async for message in websocket:
                await self.process_request(websocket, message)
        
        except asyncio.CancelledError:
            Logger.warning(f"  连接被取消: {client_addr}")
        except Exception as e:
            Logger.error(f"处理客户端消息时出错: {e}")
        finally:
            self.clients.discard(websocket)
            Logger.error(f"[{datetime.now().strftime('%H:%M:%S')}] 客户端断开连接: {client_addr}")
            Logger.info(f"   当前连接数: {len(self.clients)}")
    
    async def process_request(self, websocket, message):
        """处理解析请求"""
        try:
            self.request_count += 1
            request_id = f"REQ-{self.request_count:04d}"
            
            # 解析 JSON 请求
            request = json.loads(message)
            action = request.get('action')
            req_id = request.get('id', request_id)
            
            Logger.info(f"[{request_id}] 收到请求: action={action}")
            
            if action == 'parse_project':
                # 解析项目数据
                project_data = request.get('project_data')
                if not project_data:
                    await self.send_error(websocket, '缺少 project_data 参数', req_id)
                    return
                
                result = self.parse_project_data(project_data)
                await self.send_response(websocket, result, req_id)
            
            elif action == 'parse_json_file':
                # 解析 JSON 文件
                file_path = request.get('file_path')
                if not file_path:
                    await self.send_error(websocket, '缺少 file_path 参数', req_id)
                    return
                
                result = self.parse_json_file(file_path)
                await self.send_response(websocket, result, req_id)
            
            elif action == 'ping':
                # 心跳检测
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'id': req_id,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }))
            
            elif action == 'get_server_info':
                # 获取服务器信息
                await websocket.send(json.dumps({
                    'type': 'server_info',
                    'id': req_id,
                    'version': '1.0.0',
                    'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'request_count': self.request_count,
                    'connected_clients': len(self.clients)
                }, ensure_ascii=False))
            
            else:
                await self.send_error(websocket, f'未知的操作: {action}', req_id)
        
        except json.JSONDecodeError:
            await self.send_error(websocket, '无效的 JSON 格式', request.get('id', 'UNKNOWN'))
        except Exception as e:
            await self.send_error(websocket, f'服务器错误: {str(e)}', request.get('id', 'UNKNOWN'))
    
    def parse_project_data(self, project_data):
        """解析项目数据（直接传入 dict）"""
        try:
            start_time = datetime.now()
            Logger.info("开始解析项目数据...")
            
            # 重置解析器
            self.parser = BlockParser()
            self.parser.execution_order = 0
            self.parser.output_lines = []
            
            # 解析所有目标
            targets = project_data.get('targets', [])
            Logger.info(f"   找到 {len(targets)} 个目标")
            
            for idx, target in enumerate(targets):
                self.parser.parse_target(target, idx)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            Logger.success(f"解析完成，共 {self.parser.execution_order} 个步骤，耗时 {elapsed:.3f} 秒")
            
            return {
                'status': 'success',
                'steps': self.parser.execution_order,
                'output': self.parser.output_lines,
                'elapsed': elapsed
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stderr)
            return {
                'status': 'error',
                'message': f'解析失败: {str(e)}'
            }
    
    def parse_json_file(self, file_path):
        """解析 JSON 文件"""
        if not os.path.exists(file_path):
            return {
                'status': 'error',
                'message': f'文件不存在: {file_path}'
            }
        
        try:
            Logger.info(f"读取文件: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            Logger.success(f"文件读取成功，大小: {len(json.dumps(project_data))} 字节")
            return self.parse_project_data(project_data)
        
        except json.JSONDecodeError as e:
            return {
                'status': 'error',
                'message': f'JSON 格式错误: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'读取文件失败: {str(e)}'
            }
    
    async def send_response(self, websocket, data, req_id):
        """发送响应"""
        response = {
            'id': req_id,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            **data
        }
        await websocket.send(json.dumps(response, ensure_ascii=False))
        Logger.info(f"[{req_id}] 响应已发送: status={data.get('status', 'unknown')}")
    
    async def send_error(self, websocket, message, req_id):
        """发送错误响应"""
        Logger.error(f"[{req_id}] 错误: {message}")
        await websocket.send(json.dumps({
            'id': req_id,
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, ensure_ascii=False))
    
    async def start_server(self):
        """启动服务器"""
        global server_instance
        server_instance = self  # 保存实例引用，供清理函数使用
        
        Logger.info("=" * 60)
        Logger.success("积木解析 WebSocket 服务")
        Logger.info("=" * 60)
        Logger.info(f"地址: ws://{self.host}:{self.port}")
        Logger.info(f"功能: 解析 Scratch 项目积木块")
        Logger.info("=" * 60)
        Logger.info("\n等待客户端连接...\n")
        
        try:
            server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            Logger.success(f"服务已启动，监听 {self.host}:{self.port}")
            Logger.info("按 Ctrl+C 停止服务\n")
            
            await server.wait_closed()
        
        except OSError as e:
            if hasattr(e, 'winerror') and e.winerror == 10048:
                Logger.error(f"端口 {self.port} 已被占用，请关闭其他实例或更换端口")
            else:
                Logger.error(f"启动失败: {e}")
        except KeyboardInterrupt:
            Logger.warning("\n收到停止信号，正在关闭服务...")
        finally:
            Logger.info("服务已关闭")


def main():
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            Logger.error(f"无效的端口号: {sys.argv[1]}")
            sys.exit(1)
    
    server = BlockParseServer(port=port)
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        Logger.warning("服务已停止")
    except Exception as e:
        Logger.error(f"服务异常: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
    finally:
        global server_instance
        server_instance = None  # 清除全局引用
        sys.stdout.flush()
        sys.stderr.flush()


if __name__ == '__main__':
    main()
