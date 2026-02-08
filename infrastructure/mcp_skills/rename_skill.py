#!/usr/bin/env python3
"""
重命名文件技能
"""
import os
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class RenameSkill(MCPBaseSkill):
    """重命名文件技能"""
    
    @property
    def name(self) -> str:
        return "rename"
    
    @property
    def description(self) -> str:
        return "重命名文件。\nPDDL作用: 删除旧名称事实(has_name ?file ?old_name)，添加新名称事实(has_name ?file ?new_name)\n注意：使用物理路径作为参数，如 'storage_jail/root/document.txt' 和 'new_document'"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "源文件物理路径（如 'storage_jail/root/document.txt'）"},
                "new_filename": {"type": "string", "description": "新文件名（如 'new_document.txt' 或 'new_document'）"}
            },
            "required": ["file_path", "new_filename"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_path = arguments["file_path"]
        new_filename = arguments["new_filename"]
        
        # 构建完整文件路径
        old_path = self._safe_path(file_path)
        
        if not os.path.exists(old_path):
            return self.create_error_response(f"文件 {file_path} 不存在")
        
        # 提取目录和旧文件名
        dir_path = os.path.dirname(file_path)
        old_filename = os.path.basename(file_path)
        
        # 如果新文件名没有扩展名，保持原扩展名
        if '.' not in new_filename and '.' in old_filename:
            _, ext = os.path.splitext(old_filename)
            new_filename_with_ext = new_filename + ext
        else:
            new_filename_with_ext = new_filename
        
        # 构建新文件路径
        new_file_path = os.path.join(dir_path, new_filename_with_ext)
        new_path = self._safe_path(new_file_path)
        
        # 检查新文件是否已存在
        if os.path.exists(new_path):
            return self.create_error_response(f"目标文件 {new_filename_with_ext} 已存在")
        
        try:
            # 重命名文件
            os.rename(old_path, new_path)
            
            # 编码路径用于PDDL事实
            encoded_old_file = self._encode_path(file_path)
            encoded_new_file = self._encode_path(new_file_path)
            
            # 提取旧文件名和新文件名（不含扩展名）用于has_name谓词
            old_name_without_ext = os.path.splitext(old_filename)[0]
            new_name_without_ext = os.path.splitext(new_filename_with_ext)[0]
            encoded_old_name = self._encode_path(old_name_without_ext)
            encoded_new_name = self._encode_path(new_name_without_ext)
            
            pddl_delta = f"-(has_name {encoded_old_file} {encoded_old_name}) +(has_name {encoded_new_file} {encoded_new_name})"
            message = f"重命名文件 {file_path} 为 {new_file_path}"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"重命名失败: {str(e)}")