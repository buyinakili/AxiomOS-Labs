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
from infrastructure.pddl.pddl_state_updater import PDDLDelta


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
        import os
        # 优先使用环境变量中的SANDBOX_STORAGE_PATH，如果不存在则使用传入的storage_path
        sandbox_storage_path = os.environ.get("SANDBOX_STORAGE_PATH")
        if sandbox_storage_path:
            self.storage_path = sandbox_storage_path
            print(f"[MCP Executor] 使用环境变量SANDBOX_STORAGE_PATH: {self.storage_path}")
        else:
            self.storage_path = storage_path or ""
            if self.storage_path:
                print(f"[MCP Executor] 使用传入的storage_path: {self.storage_path}")
        
        self.execution_history: List[str] = []
        self.server_command = server_command
        self.server_args = server_args or ["mcp_server_structured.py"]
        # 保存当前环境变量，用于传递给MCP服务器子进程
        self.server_env = os.environ.copy()
        self.client = SimpleMCPClient(
            server_command=server_command,
            server_args=self.server_args,
            server_env=self.server_env
        )
        self._connected = False
        # 初始化日志已移除，由工厂统一输出

    def _ensure_connected(self) -> bool:
        """确保客户端已连接"""
        if not self._connected:
            try:
                success = self.client.connect()
                if success:
                    self._connected = True
                    tool_names = self.client.get_tool_names()
                    print(f"[MCP] 连接成功 ({len(tool_names)} 工具)", file=sys.stderr)
                else:
                    print("[MCP] 连接失败", file=sys.stderr)
                    return False
            except Exception as e:
                print(f"[MCP] 连接异常: {e}", file=sys.stderr)
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
        elif tool_name == "rename_file":
            if len(args) >= 3:
                arguments["old_file"] = args[0]
                arguments["new_file"] = args[1]
                arguments["folder"] = args[2]
            else:
                return ExecutionResult(False, "rename_file 需要 old_file, new_file, folder 参数")
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
                print(f"[MCP Executor DEBUG] tool={tool_name}, pddl_delta={pddl_delta}", file=sys.stderr)
                # 解析 delta 字符串为单独的事实
                delta = PDDLDelta.parse(pddl_delta)
                return ExecutionResult(
                    True,
                    response.message,
                    add_facts=delta.add_facts,
                    del_facts=delta.del_facts
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
        # 静默忽略，不输出警告
        pass

    def register_skill_from_file(self, file_path: str) -> bool:
        """
        在沙盒模式下，将技能文件部署到沙盒的 skills 目录
        
        注意：此方法仅在沙盒环境中有效，用于进化算法临时加载新技能
        """
        import os
        import shutil
        
        # 检查是否为沙盒环境（通过存储路径判断）
        # 沙盒环境的 storage_path 通常由沙盒管理器设置
        if not self.storage_path:
            # 非沙盒环境，保持原行为（静默忽略）
            return False
        
        # 确保文件存在
        if not os.path.exists(file_path):
            return False
        
        # 关键修复：不再复制文件，因为evolution.py已经将文件创建在正确的位置
        # 我们只需要设置环境变量并重启MCP客户端（仅在技能目录变化时）
        
        # 获取技能文件所在的目录（应该是沙盒的skills目录）
        skill_dir = os.path.dirname(file_path)
        
        # 验证技能目录是否是沙盒的skills目录
        # 检查路径中是否包含"skills"并且是沙盒路径的一部分
        if "skills" not in skill_dir:
            print(f"[MCP Executor] 警告：技能文件不在skills目录中: {file_path}")
            # 仍然尝试使用，但记录警告
        
        print(f"[MCP Executor] 使用现有技能文件: {file_path}")
        
        # 检查技能目录是否发生变化
        current_skill_dir = self.server_env.get("SANDBOX_MCP_SKILLS_DIR")
        skill_dir_changed = current_skill_dir != skill_dir
        
        # 设置环境变量（当前进程和MCP服务器子进程）
        self.server_env["SANDBOX_MCP_SKILLS_DIR"] = skill_dir
        os.environ["SANDBOX_MCP_SKILLS_DIR"] = skill_dir
        
        # 设置沙盒存储路径环境变量
        # 优先使用当前进程的环境变量（由evolution.py设置），如果不存在则使用self.storage_path
        sandbox_storage_path = os.environ.get("SANDBOX_STORAGE_PATH", self.storage_path)
        self.server_env["SANDBOX_STORAGE_PATH"] = sandbox_storage_path
        os.environ["SANDBOX_STORAGE_PATH"] = sandbox_storage_path
        
        # 仅在技能目录变化时才重启MCP客户端
        if skill_dir_changed:
            print(f"[MCP Executor] 技能目录变化 ({current_skill_dir} -> {skill_dir})，重启MCP客户端")
            self._restart_mcp_client()
        else:
            print(f"[MCP Executor] 技能目录未变化，跳过重启，依赖服务器动态加载")
            # 可选：强制刷新工具列表（轻量级）
            self._force_reconnect()
        
        return True
    
    def _restart_mcp_client(self):
        """重启MCP客户端以应用新的环境变量和技能目录，带异常处理"""
        print("[MCP Executor] 重启MCP客户端以应用沙盒技能...")
        
        # 断开当前连接（忽略任何异常）
        if self._connected:
            try:
                self.client.disconnect()
            except Exception as e:
                print(f"[MCP Executor] 断开连接时发生异常（忽略）: {e}", file=sys.stderr)
            finally:
                self._connected = False
        
        # 重新创建MCP客户端，传递更新后的环境变量
        try:
            from infrastructure.mcp_client import SimpleMCPClient
            self.client = SimpleMCPClient(
                server_command=self.server_command,
                server_args=self.server_args,
                server_env=self.server_env
            )
        except Exception as e:
            print(f"[MCP Executor] 创建MCP客户端失败: {e}", file=sys.stderr)
            # 即使失败，也继续执行，因为可能后续连接会恢复
        
        # 强制下次执行时重新连接
        print("[MCP Executor] MCP客户端已重启，等待下次执行时连接")
    
    def _force_reconnect(self):
        """强制重新连接MCP客户端以获取最新工具列表"""
        if self._connected:
            print("[MCP Executor] 重新连接MCP客户端以刷新工具列表...")
            self.client.disconnect()
            self._connected = False
            # 下次执行时会自动重新连接

    def get_registered_skills(self) -> List[str]:
        """获取可用的工具名称"""
        if self._ensure_connected():
            return self.client.get_tool_names()
        return []

    def set_storage_path(self, path: str):
        """设置存储路径（用于兼容性）"""
        self.storage_path = path
        # 同时更新server_env中的SANDBOX_STORAGE_PATH环境变量
        self.server_env["SANDBOX_STORAGE_PATH"] = path

    def disconnect(self):
        """断开 MCP 连接"""
        if self._connected:
            self.client.disconnect()
            self._connected = False
            # 静默断开，不输出日志