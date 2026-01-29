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
        
        注意：MCP服务器在沙盒模式下会改变工作目录到沙盒存储路径
        因此这里直接使用当前工作目录作为基础路径
        
        :param parts: 路径组成部分
        :return: 绝对路径
        """
        # 由于MCP服务器已经改变了工作目录到沙盒存储路径（如果设置了SANDBOX_STORAGE_PATH）
        # 或者保持在项目根目录（正常模式）
        # 这里直接使用当前工作目录作为基础路径
        
        safe_parts = []
        for part in parts:
            # 将 _dot_ 替换回 .
            if '_dot_' in part:
                part = part.replace('_dot_', '.')
            safe_parts.append(part)
        
        # 构建完整路径
        full_path = os.path.join(os.getcwd(), *safe_parts)
        logger.debug(f"_safe_path: 工作目录={os.getcwd()}, 部分={parts}, 完整路径={full_path}")
        return full_path
    
    def _to_pddl_name(self, filename: str) -> str:
        """将实际文件名转换为PDDL格式（. 替换为 _dot_）"""
        return filename.replace('.', '_dot_')