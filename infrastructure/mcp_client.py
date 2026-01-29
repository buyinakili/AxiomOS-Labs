#!/usr/bin/env python3
"""
MCP 客户端实现

用于连接 mcp_server_structured.py，执行工具调用，并解析返回的结构化结果。
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("警告: MCP 库未安装，请运行: pip install mcp")


class MCPClientError(Exception):
    """MCP 客户端错误"""
    pass


class ConnectionStatus(Enum):
    """连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPTool:
    """MCP 工具表示"""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPResponse:
    """MCP 响应结果"""
    success: bool
    message: str
    pddl_delta: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MCPClient:
    """MCP 客户端"""
    
    def __init__(
        self,
        server_command: str = None,
        server_args: List[str] = None,
        server_env: Dict[str, str] = None,
        connection_timeout: float = None,
        session_init_timeout: float = None,
        tool_list_timeout: float = None,
        tool_call_timeout: float = None,
        disconnect_timeout: float = None
    ):
        """
        初始化 MCP 客户端
        
        Args:
            server_command: 服务器命令 (如 "python3")
            server_args: 服务器参数 (如 ["mcp_server_structured.py"])
            server_env: 服务器环境变量
            connection_timeout: 连接超时时间（秒）
            session_init_timeout: 会话初始化超时（秒）
            tool_list_timeout: 获取工具列表超时（秒）
            tool_call_timeout: 工具调用超时（秒）
            disconnect_timeout: 断开连接超时（秒）
        """
        if not MCP_AVAILABLE:
            raise MCPClientError("MCP 库未安装，请运行: pip install mcp")
        
        # 导入配置
        from config.settings import Settings
        config = Settings.load_from_env()
        
        self.server_command = server_command or config.mcp_server_command
        self.server_args = server_args or [config.mcp_server_args]
        self.server_env = server_env or {}
        
        # 使用配置中的超时值，如果提供了参数则使用参数
        self.connection_timeout = connection_timeout or config.mcp_connection_timeout
        self.session_init_timeout = session_init_timeout or config.mcp_connection_timeout
        self.tool_list_timeout = tool_list_timeout or config.mcp_connection_timeout
        self.tool_call_timeout = tool_call_timeout or config.mcp_tool_call_timeout
        self.disconnect_timeout = disconnect_timeout or config.mcp_disconnect_timeout
        
        self.status = ConnectionStatus.DISCONNECTED
        self.session: Optional[ClientSession] = None
        self.tools: List[MCPTool] = []
        self.server_process: Optional[subprocess.Popen] = None
        self._connection_lock = asyncio.Lock()
        self._stdio_context = None
        self._session_context = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    async def connect(self) -> bool:
        """连接到 MCP 服务器，使用配置的超时值"""
        async with self._connection_lock:
            if self.status == ConnectionStatus.CONNECTED:
                return True
                
            self.status = ConnectionStatus.CONNECTING
            
            try:
                # 创建服务器参数
                server_params = StdioServerParameters(
                    command=self.server_command,
                    args=self.server_args,
                    env=self.server_env
                )
                
                # 创建 stdio 客户端上下文管理器
                self._stdio_context = stdio_client(server_params)
                # 进入上下文，获取流（使用连接超时）
                try:
                    self.read_stream, self.write_stream = await asyncio.wait_for(
                        self._stdio_context.__aenter__(),
                        timeout=self.connection_timeout
                    )
                except asyncio.TimeoutError:
                    print(f"[MCP] 连接超时: stdio上下文进入超时 ({self.connection_timeout}秒)", file=sys.stderr)
                    raise MCPClientError(f"连接超时: stdio上下文进入超时 ({self.connection_timeout}秒)")
                
                # 创建客户端会话上下文管理器（使用会话初始化超时）
                self.session = ClientSession(self.read_stream, self.write_stream)
                try:
                    self._session_context = await asyncio.wait_for(
                        self.session.__aenter__(),
                        timeout=self.session_init_timeout
                    )
                except asyncio.TimeoutError:
                    print(f"[MCP] 连接超时: 客户端会话创建超时 ({self.session_init_timeout}秒)", file=sys.stderr)
                    raise MCPClientError(f"连接超时: 客户端会话创建超时 ({self.session_init_timeout}秒)")
                
                # 初始化会话（使用会话初始化超时）
                try:
                    await asyncio.wait_for(self.session.initialize(), timeout=self.session_init_timeout)
                except asyncio.TimeoutError:
                    print(f"[MCP] 连接超时: 会话初始化超时 ({self.session_init_timeout}秒)", file=sys.stderr)
                    raise MCPClientError(f"连接超时: 会话初始化超时 ({self.session_init_timeout}秒)")
                
                # 获取工具列表（使用工具列表超时）
                try:
                    await asyncio.wait_for(self._refresh_tools(), timeout=self.tool_list_timeout)
                except asyncio.TimeoutError:
                    print(f"[MCP] 连接超时: 获取工具列表超时 ({self.tool_list_timeout}秒)", file=sys.stderr)
                    raise MCPClientError(f"连接超时: 获取工具列表超时 ({self.tool_list_timeout}秒)")
                
                self.status = ConnectionStatus.CONNECTED
                print(f"[MCP] 连接成功 ({len(self.tools)} 工具)", file=sys.stderr)
                return True
                        
            except Exception as e:
                self.status = ConnectionStatus.ERROR
                print(f"[MCP] 连接失败: {e}", file=sys.stderr)
                # 清理资源
                await self._cleanup()
                raise MCPClientError(f"连接失败: {e}")
    
    async def _refresh_tools(self):
        """刷新工具列表"""
        if not self.session:
            raise MCPClientError("会话未建立")
            
        try:
            result = await self.session.list_tools()
            self.tools = []
            
            # 处理返回结果：可能是 ListToolsResult 对象或元组列表
            tools_list = []
            
            if hasattr(result, 'tools'):
                # 如果是 ListToolsResult 对象
                tools_list = result.tools
            elif isinstance(result, (list, tuple)):
                # 如果是元组列表，查找 'tools' 键
                for item in result:
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        key, value = item
                        if key == 'tools' and isinstance(value, list):
                            tools_list = value
                            break
                # 如果没有找到，假设整个列表就是工具列表
                if not tools_list:
                    tools_list = result
            
            for tool in tools_list:
                # 提取工具信息
                name = ""
                description = ""
                input_schema = {}
                
                if hasattr(tool, 'name'):
                    # 如果是 Tool 对象
                    name = getattr(tool, 'name', '')
                    description = getattr(tool, 'description', '')
                    input_schema = getattr(tool, 'inputSchema', {})
                elif isinstance(tool, dict):
                    # 如果是字典
                    name = tool.get("name", "")
                    description = tool.get("description", "")
                    input_schema = tool.get("inputSchema", {})
                elif isinstance(tool, (list, tuple)) and len(tool) == 2:
                    # 如果是键值对元组
                    key, value = tool
                    if key == 'name':
                        name = value
                    # 其他情况忽略
                
                # 如果 inputSchema 是字符串，尝试解析为字典
                if isinstance(input_schema, str):
                    try:
                        import json
                        input_schema = json.loads(input_schema)
                    except:
                        input_schema = {}
                
                mcp_tool = MCPTool(
                    name=name,
                    description=description,
                    input_schema=input_schema
                )
                self.tools.append(mcp_tool)
                
        except Exception as e:
            print(f"[MCP] 获取工具列表失败: {e}", file=sys.stderr)
            self.tools = []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """
        调用 MCP 工具，使用配置的超时值
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            MCPResponse 对象
        """
        if not self.session:
            raise MCPClientError("会话未建立，请先调用 connect()")
        
        try:
            # 调用工具（使用工具调用超时）
            try:
                result = await asyncio.wait_for(
                    self.session.call_tool(tool_name, arguments),
                    timeout=self.tool_call_timeout
                )
            except asyncio.TimeoutError:
                print(f"[MCP] 工具调用超时: {tool_name} ({self.tool_call_timeout}秒)", file=sys.stderr)
                return MCPResponse(
                    success=False,
                    message=f"工具调用超时: {tool_name} ({self.tool_call_timeout}秒)",
                    error=f"Timeout after {self.tool_call_timeout} seconds"
                )
            
            # 检查是否是 CallToolResult 对象
            if hasattr(result, 'content'):
                # 提取 content 列表
                content_list = result.content
                is_error = getattr(result, 'isError', False)
                
                if not content_list or len(content_list) == 0:
                    return MCPResponse(
                        success=False,
                        message="工具调用返回空结果",
                        error="Empty content"
                    )
                
                # 获取第一个内容（通常是文本）
                first_content = content_list[0]
                
                # 检查内容类型
                if hasattr(first_content, 'type'):
                    content_type = first_content.type
                    if content_type != "text":
                        return MCPResponse(
                            success=False,
                            message=f"非文本返回类型: {content_type}",
                            error=f"Unexpected content type: {content_type}"
                        )
                    text = getattr(first_content, 'text', '')
                else:
                    # 可能是其他结构
                    text = str(first_content)
                
                # 解析 JSON 响应
                try:
                    response_data = json.loads(text)
                except json.JSONDecodeError:
                    # 如果不是 JSON，可能是纯文本
                    return MCPResponse(
                        success=not is_error,
                        message=text,
                        raw_response={"text": text}
                    )
                
                # 提取 metadata
                metadata = response_data.get("metadata", {})
                human_readable = response_data.get("human_readable", "")
                
                if metadata.get("status") == "success" and not is_error:
                    pddl_delta = metadata.get("pddl_delta", "")
                    message = metadata.get("message", human_readable)
                    
                    return MCPResponse(
                        success=True,
                        message=message,
                        pddl_delta=pddl_delta,
                        raw_response=response_data
                    )
                else:
                    error_msg = metadata.get("error", "Unknown error") if metadata else "Tool execution error"
                    return MCPResponse(
                        success=False,
                        message=error_msg,
                        error=error_msg,
                        raw_response=response_data
                    )
            else:
                # 未知返回类型
                return MCPResponse(
                    success=False,
                    message=f"未知返回类型: {type(result)}",
                    error=f"Unknown result type: {type(result)}"
                )
                
        except Exception as e:
            error_msg = f"工具调用失败: {str(e)}"
            print(f"[MCP] {error_msg}", file=sys.stderr)
            return MCPResponse(
                success=False,
                message=error_msg,
                error=str(e)
            )
    
    async def _cleanup(self):
        """清理资源"""
        async with self._connection_lock:
            try:
                if self._session_context is not None:
                    await self.session.__aexit__(None, None, None)
                    self._session_context = None
                    self.session = None
            except Exception:
                pass
            try:
                if self._stdio_context is not None:
                    await self._stdio_context.__aexit__(None, None, None)
                    self._stdio_context = None
                    self.read_stream = None
                    self.write_stream = None
            except Exception:
                pass
    
    async def disconnect(self):
        """断开连接，使用配置的超时值"""
        async with self._connection_lock:
            try:
                # 设置超时，防止清理操作无限挂起
                await asyncio.wait_for(self._cleanup(), timeout=self.disconnect_timeout)
            except asyncio.TimeoutError:
                # 超时后强制清理资源
                print(f"[MCP] 断开连接超时 ({self.disconnect_timeout}秒)，强制清理", file=sys.stderr)
                # 忽略进一步清理，直接重置状态
                self._stdio_context = None
                self._session_context = None
                self.session = None
                self.read_stream = None
                self.write_stream = None
            except Exception as e:
                print(f"[MCP] 断开连接异常: {e}", file=sys.stderr)
            finally:
                self.status = ConnectionStatus.DISCONNECTED
                # 静默断开，不输出日志
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return [tool.name for tool in self.tools]
    
    def has_tool(self, tool_name: str) -> bool:
        """检查是否包含指定工具"""
        return any(tool.name == tool_name for tool in self.tools)


class SimpleMCPClient:
    """
    简化版 MCP 客户端（同步接口）
    
    为现有代码提供同步接口，内部使用异步调用
    """
    
    def __init__(self, **kwargs):
        self.client = MCPClient(**kwargs)
        self._loop = None
        
    def connect(self) -> bool:
        """同步连接"""
        if not self._loop:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
        return self._loop.run_until_complete(self.client.connect())
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """同步调用工具"""
        if not self._loop:
            raise MCPClientError("客户端未连接")
            
        return self._loop.run_until_complete(
            self.client.call_tool(tool_name, arguments)
        )
    
    def disconnect(self):
        """同步断开连接，带超时和异常处理"""
        if self._loop:
            try:
                # 设置整体超时，防止run_until_complete无限等待
                # 使用客户端的断开连接超时值
                future = asyncio.wait_for(self.client.disconnect(), timeout=self.client.disconnect_timeout)
                self._loop.run_until_complete(future)
            except asyncio.TimeoutError:
                print(f"[SimpleMCPClient] 断开连接超时 ({self.client.disconnect_timeout}秒)，强制关闭事件循环", file=sys.stderr)
            except Exception as e:
                print(f"[SimpleMCPClient] 断开连接异常: {e}", file=sys.stderr)
            finally:
                try:
                    self._loop.close()
                except Exception:
                    pass
                self._loop = None
    
    def get_tool_names(self) -> List[str]:
        """获取工具名称"""
        return self.client.get_tool_names()
    
    def has_tool(self, tool_name: str) -> bool:
        """检查工具"""
        return self.client.has_tool(tool_name)


# 测试函数
async def test_mcp_client():
    """测试 MCP 客户端"""
    print("测试 MCP 客户端...")
    
    try:
        client = MCPClient()
        
        # 连接
        if not await client.connect():
            print("❌ 连接失败")
            return False
        
        print(f"✅ 连接成功，工具: {client.get_tool_names()}")
        
        # 测试 scan 工具
        print("\n测试 scan 工具...")
        response = await client.call_tool("scan", {"folder": "root"})
        
        if response.success:
            print(f"✅ scan 调用成功")
            print(f"   消息: {response.message}")
            print(f"   pddl_delta: {response.pddl_delta}")
        else:
            print(f"❌ scan 调用失败: {response.error}")
            
        # 断开连接
        await client.disconnect()
        print("\n✅ 测试完成")
        return response.success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_mcp_client())
    sys.exit(0 if success else 1)