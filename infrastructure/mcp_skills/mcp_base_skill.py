#!/usr/bin/env python3
"""
MCP技能基类
所有MCP技能应继承此类，实现 name、description、input_schema 和 execute 方法。
"""
import json
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger("AxiomLabs_mcp_server")


class MCPBaseSkill(ABC):
    """MCP技能基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称，对应MCP工具名"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述，用于MCP工具描述"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """输入模式，符合JSON Schema格式"""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行技能逻辑，返回MCP结构化响应
        
        :param arguments: 工具调用参数
        :return: MCP响应列表，通常为包含单个文本项的列表
        """
        pass
    
    @staticmethod
    def create_success_response(message: str, pddl_delta: str) -> List[Dict[str, Any]]:
        """创建成功的结构化响应"""
        metadata = {
            "pddl_delta": pddl_delta,
            "status": "success",
            "message": message
        }
        
        response_text = json.dumps({
            "human_readable": message,
            "metadata": metadata
        }, ensure_ascii=False)
        
        return [{"type": "text", "text": response_text}]
    
    @staticmethod
    def create_error_response(error_message: str) -> List[Dict[str, Any]]:
        """创建错误的结构化响应"""
        metadata = {
            "status": "error",
            "error": error_message
        }
        
        response_text = json.dumps({
            "human_readable": f"错误: {error_message}",
            "metadata": metadata
        }, ensure_ascii=False)
        
        return [{"type": "text", "text": response_text}]
    
    def _safe_path(self, *parts: str) -> str:
        """
        安全构建路径，将PDDL格式的文件名（可能包含 _dot_）转换回实际文件名
        
        :param parts: 路径组成部分
        :return: 绝对路径
        """
        # 当前工作目录下的workspace作为根目录
        base = os.path.join(os.getcwd(), "workspace")
        safe_parts = []
        for part in parts:
            # 将 _dot_ 替换回 .
            if '_dot_' in part:
                part = part.replace('_dot_', '.')
            safe_parts.append(part)
        return os.path.join(base, *safe_parts)
    
    def _to_pddl_name(self, filename: str) -> str:
        """将实际文件名转换为PDDL格式（. 替换为 _dot_）"""
        return filename.replace('.', '_dot_')