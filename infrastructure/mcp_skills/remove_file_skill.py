#!/usr/bin/env python3
"""
删除文件技能
"""
import os
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class RemoveFileSkill(MCPBaseSkill):
    """删除文件"""
    
    @property
    def name(self) -> str:
        return "remove_file"
    
    @property
    def description(self) -> str:
        return "删除文件。\nPDDL作用: 删除文件存在事实(at ?file ?folder)\n注意：使用物理路径作为参数，如 'storage_jail/root/document.txt'"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "要删除的文件物理路径（如 'storage_jail/root/document.txt'）"}
            },
            "required": ["file_path"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_path = arguments["file_path"]
        
        target_path = self._safe_path(file_path)
        
        try:
            if not os.path.exists(target_path):
                return self.create_error_response(f"文件 {file_path} 不存在")
            
            os.remove(target_path)
            
            # 编码路径用于PDDL事实
            encoded_file = self._encode_path(file_path)
            
            # 提取文件夹路径
            folder_path = os.path.dirname(file_path)
            encoded_folder = self._encode_path(folder_path)
            
            message = f"删除 {file_path}"
            pddl_delta = f"-(at {encoded_file} {encoded_folder})"
            return self.create_success_response(message, pddl_delta)
        except Exception as e:
            return self.create_error_response(f"删除失败: {str(e)}")