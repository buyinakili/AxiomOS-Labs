#!/usr/bin/env python3
"""
创建文件技能
"""
import os
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class CreateFileSkill(MCPBaseSkill):
    """创建文件技能"""
    
    @property
    def name(self) -> str:
        return "create_file"
    
    @property
    def description(self) -> str:
        return "创建新文件。\nPDDL作用: 添加文件存在事实(at ?file ?folder)和文件名事实(has_name ?file ?name)\n注意：使用物理路径作为参数，如 'document.txt' 和 'storage_jail/root'"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "文件名（如 'document.txt'）"},
                "folder": {"type": "string", "description": "文件夹物理路径（如 'storage_jail/root'）"},
                "content": {"type": "string", "description": "文件内容（可选）", "default": ""}
            },
            "required": ["filename", "folder"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        filename = arguments["filename"]
        folder_path = arguments["folder"]
        content = arguments.get("content", "")
        
        # 构建完整文件路径
        file_full_path = os.path.join(folder_path, filename)
        file_path = self._safe_path(file_full_path)
        
        # 检查文件是否已存在
        if os.path.exists(file_path):
            return self.create_error_response(f"文件 {filename} 在文件夹 {folder_path} 中已存在")
        
        # 检查文件夹是否存在，如果不存在则创建
        folder_full_path = self._safe_path(folder_path)
        if not os.path.exists(folder_full_path):
            try:
                os.makedirs(folder_full_path, exist_ok=True)
            except Exception as e:
                return self.create_error_response(f"无法创建文件夹 {folder_path}: {str(e)}")
        
        try:
            # 创建文件并写入内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 编码路径用于PDDL事实
            encoded_file = self._encode_path(file_full_path)
            encoded_folder = self._encode_path(folder_path)
            
            # 提取文件名（不含扩展名）用于has_name谓词
            name_without_ext = os.path.splitext(filename)[0]
            encoded_name = self._encode_path(name_without_ext)
            
            pddl_delta = f"+(at {encoded_file} {encoded_folder}) +(has_name {encoded_file} {encoded_name})"
            message = f"创建文件 {filename} 在文件夹 {folder_path}"
            
            if content:
                message += f"，内容长度: {len(content)} 字符"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"创建文件失败: {str(e)}")