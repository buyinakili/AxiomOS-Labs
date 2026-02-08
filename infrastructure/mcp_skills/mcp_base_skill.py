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
    
    def _encode_path(self, path: str) -> str:
        """
        将物理路径编码为PDDL标识符
        
        PDDL标识符不能包含斜杠，所以将 / 替换为 _slash_
        同时处理 . 替换为 _dot_
        
        :param path: 物理路径（如 "storage_jail/root" 或 "run_20260208_173552/storage_jail/root"）
        :return: 编码后的PDDL标识符
        """
        # 首先处理 . 替换为 _dot_
        encoded = path.replace('.', '_dot_')
        # 然后处理 / 替换为 _slash_
        encoded = encoded.replace('/', '_slash_')
        # 处理可能出现的多个连续斜杠
        encoded = encoded.replace('//', '_slash_')
        # 处理开头的斜杠
        if encoded.startswith('_slash_'):
            encoded = encoded[7:]
        logger.debug(f"_encode_path: 原始路径={path}, 编码后={encoded}")
        return encoded
    
    def _decode_path(self, encoded_path: str) -> str:
        """
        将PDDL标识符解码回物理路径
        
        :param encoded_path: 编码后的PDDL标识符
        :return: 原始物理路径
        """
        # 首先处理 _slash_ 替换为 /
        decoded = encoded_path.replace('_slash_', '/')
        # 然后处理 _dot_ 替换为 .
        decoded = decoded.replace('_dot_', '.')
        logger.debug(f"_decode_path: 编码路径={encoded_path}, 解码后={decoded}")
        return decoded
    
    def _safe_path(self, *parts: str) -> str:
        """
        安全构建路径，支持物理路径和抽象路径
        
        注意：MCP服务器在沙盒模式下会改变工作目录到沙盒存储路径
        因此这里直接使用当前工作目录作为基础路径
        
        :param parts: 路径组成部分，可以是物理路径或抽象名称
        :return: 绝对路径
        """
        # 由于MCP服务器已经改变了工作目录到沙盒存储路径（如果设置了SANDBOX_STORAGE_PATH）
        # 或者保持在项目根目录（正常模式）
        # 这里直接使用当前工作目录作为基础路径
        
        safe_parts = []
        for part in parts:
            # 如果部分包含 _slash_，说明是编码的物理路径，需要解码
            if '_slash_' in part:
                part = self._decode_path(part)
            # 将 _dot_ 替换回 .
            if '_dot_' in part:
                part = part.replace('_dot_', '.')
            safe_parts.append(part)
        
        # 如果当前工作目录以 storage_jail 结尾，且解码后的路径以 storage_jail/ 开头，
        # 则去除该前缀，避免重复的 storage_jail 目录
        cwd = os.getcwd()
        if cwd.endswith('storage_jail'):
            normalized_parts = []
            for part in safe_parts:
                if part.startswith('storage_jail/'):
                    part = part[len('storage_jail/'):]
                normalized_parts.append(part)
            safe_parts = normalized_parts
        
        # 构建完整路径
        full_path = os.path.join(cwd, *safe_parts)
        logger.debug(f"_safe_path: 工作目录={cwd}, 部分={parts}, 完整路径={full_path}")
        return full_path
    
    def _to_pddl_name(self, filename: str) -> str:
        """
        将实际文件名转换为PDDL格式
        
        处理 . 替换为 _dot_，并处理路径分隔符
        
        :param filename: 实际文件名或路径
        :return: PDDL格式的标识符
        """
        # 首先处理 . 替换为 _dot_
        encoded = filename.replace('.', '_dot_')
        # 如果包含路径分隔符，也需要编码
        if '/' in encoded:
            encoded = encoded.replace('/', '_slash_')
        return encoded