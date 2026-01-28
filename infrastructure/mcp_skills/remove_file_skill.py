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
        return "删除文件。\nPDDL作用: 删除文件存在事实(at ?file ?folder)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_name": {"type": "string", "description": "要删除的文件名"},
                "folder_name": {"type": "string", "description": "文件所在文件夹"}
            },
            "required": ["file_name", "folder_name"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_name = arguments["file_name"]
        folder_name = arguments["folder_name"]
        
        target_path = self._safe_path(folder_name, file_name)
        
        try:
            if not os.path.exists(target_path):
                return self.create_error_response(f"文件 {file_name} 在 {folder_name} 中不存在")
            
            os.remove(target_path)
            message = f"删除 {file_name} 从 {folder_name}"
            pddl_delta = f"-(at {file_name} {folder_name})"
            return self.create_success_response(message, pddl_delta)
        except Exception as e:
            return self.create_error_response(f"删除失败: {str(e)}")