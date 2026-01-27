#!/usr/bin/env python3
"""
MCP 动作执行器实现

通过 MCP 客户端调用远程工具，替代本地技能执行。
"""
import asyncio
import sys
from typing import Dict, List
from interface.executor import IExecutor, ExecutionResult
from infrastructure.mcp_client import SimpleMCPClient


class MCPActionExecutor(IExecutor):
    """基于 MCP 的动作执行器"""

    def __init__(self, storage_path: str = None, server_command: str = "python3", 
                 server_args: List[str] = None):
        """
        初始化 MCP 执行器
        
        Args:
            storage_path: 物理存储路径（保留用于兼容性）
            server_command: MCP 服务器命令
            server_args: MCP 服务器参数
        """
        self.storage_path = storage_path or ""
        self.execution_history: List[str] = []
        self.server_command = server_command
        self.server_args = server_args or ["mcp_server_structured.py"]
        self.client = SimpleMCPClient(
            server_command=server_command,
            server_args=self.server_args
        )
        self._connected = False
        print(f"[MCPExecutor] 初始化完成，服务器: {server_command} {' '.join(self.server_args)}", file=sys.stderr)

    def _ensure_connected(self) -> bool:
        """确保客户端已连接"""
        if not self._connected:
            try:
                print("[MCPExecutor] 正在连接到 MCP 服务器...", file=sys.stderr)
                success = self.client.connect()
                if success:
                    self._connected = True
                    print(f"[MCPExecutor] 连接成功，可用工具: {self.client.get_tool_names()}", file=sys.stderr)
                else:
                    print("[MCPExecutor] 连接失败", file=sys.stderr)
                    return False
            except Exception as e:
                print(f"[MCPExecutor] 连接异常: {e}", file=sys.stderr)
                return False
        return True

    def execute(self, action_str: str) -> ExecutionResult:
        """
        执行一个动作
        
        Args:
            action_str: 动作字符串（如 "move file_a folder_x folder_y"）
            
        Returns:
            ExecutionResult 对象
        """
        # 解析动作
        parts = action_str.strip().split()
        if not parts:
            return ExecutionResult(False, "动作字符串为空")

        action_name = parts[0]
        args = parts[1:]

        # 记录执行历史
        self.execution_history.append(action_name.lower())

        # 确保连接
        if not self._ensure_connected():
            return ExecutionResult(
                False,
                f"MCP 连接失败，无法执行动作: {action_name}"
            )

        # 构建参数字典（根据工具定义）
        # 这里需要根据动作名称映射到对应的工具参数
        # 简单实现：假设参数顺序与工具定义一致
        tool_name = action_name.lower()
        
        # 检查工具是否存在
        if not self.client.has_tool(tool_name):
            return ExecutionResult(
                False,
                f"MCP 工具不存在: {tool_name}"
            )

        # 根据工具名称构建参数
        arguments = {}
        if tool_name == "scan":
            if len(args) >= 1:
                arguments["folder"] = args[0]
            else:
                return ExecutionResult(False, "scan 需要 folder 参数")
        elif tool_name == "move":
            if len(args) >= 3:
                arguments["file_name"] = args[0]
                arguments["from_folder"] = args[1]
                arguments["to_folder"] = args[2]
            else:
                return ExecutionResult(False, "move 需要 file_name, from_folder, to_folder 参数")
        elif tool_name == "get_admin":
            # 无参数
            pass
        elif tool_name == "compress":
            if len(args) >= 3:
                arguments["file_name"] = args[0]
                arguments["folder"] = args[1]
                arguments["archive_name"] = args[2]
            else:
                return ExecutionResult(False, "compress 需要 file_name, folder, archive_name 参数")
        elif tool_name == "remove_file":
            if len(args) >= 2:
                arguments["file_name"] = args[0]
                arguments["folder_name"] = args[1]
            else:
                return ExecutionResult(False, "remove_file 需要 file_name, folder_name 参数")
        else:
            # 通用处理：将位置参数映射为 arg0, arg1, ...
            for i, arg in enumerate(args):
                arguments[f"arg{i}"] = arg

        # 调用工具
        try:
            response = self.client.call_tool(tool_name, arguments)
            if response.success:
                # 提取 pddl_delta 并添加到结果中
                pddl_delta = response.pddl_delta or ""
                return ExecutionResult(
                    True,
                    response.message,
                    add_facts=[pddl_delta] if pddl_delta and not pddl_delta.startswith("-") else [],
                    del_facts=[pddl_delta[1:]] if pddl_delta and pddl_delta.startswith("-") else []
                )
            else:
                return ExecutionResult(
                    False,
                    f"MCP 工具调用失败: {response.error}"
                )
        except Exception as e:
            return ExecutionResult(
                False,
                f"MCP 调用异常: {str(e)}"
            )

    def get_execution_history(self) -> List[str]:
        """获取执行历史记录"""
        return self.execution_history.copy()

    def clear_execution_history(self):
        """清空执行历史记录"""
        self.execution_history.clear()

    def register_skill(self, skill):
        """MCP 执行器不直接注册技能，所有工具通过 MCP 服务器提供"""
        print(f"[MCPExecutor] 警告: register_skill 被调用但忽略，技能 {skill.name} 不会注册", file=sys.stderr)

    def register_skill_from_file(self, file_path: str) -> bool:
        """MCP 执行器不支持从文件加载技能"""
        print(f"[MCPExecutor] 警告: register_skill_from_file 被调用但忽略", file=sys.stderr)
        return False

    def get_registered_skills(self) -> List[str]:
        """获取可用的工具名称"""
        if self._ensure_connected():
            return self.client.get_tool_names()
        return []

    def set_storage_path(self, path: str):
        """设置存储路径（用于兼容性）"""
        self.storage_path = path

    def disconnect(self):
        """断开 MCP 连接"""
        if self._connected:
            self.client.disconnect()
            self._connected = False
            print("[MCPExecutor] 已断开连接", file=sys.stderr)