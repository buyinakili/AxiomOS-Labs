#!/usr/bin/env python3
"""
移动文件技能
"""
import shutil
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class MoveSkill(MCPBaseSkill):
    """移动文件到另一个文件夹"""
    
    @property
    def name(self) -> str:
        return "move"
    
    @property
    def description(self) -> str:
        return "移动文件到另一个文件夹。\nPDDL作用: 删除源位置事实(at ?file ?from_folder)，添加目标位置事实(at ?file ?to_folder)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_name": {"type": "string", "description": "文件名（PDDL格式，可能包含 _dot_）"},
                "from_folder": {"type": "string", "description": "源文件夹名称"},
                "to_folder": {"type": "string", "description": "目标文件夹名称"}
            },
            "required": ["file_name", "from_folder", "to_folder"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_name = arguments["file_name"]
        from_folder = arguments["from_folder"]
        to_folder = arguments["to_folder"]
        
        src_path = self._safe_path(from_folder, file_name)
        dst_path = self._safe_path(to_folder, file_name)
        
        try:
            shutil.move(src_path, dst_path)
            message = f"移动 {file_name} 从 {from_folder} 到 {to_folder}"
            pddl_delta = f"-(at {file_name} {from_folder}) +(at {file_name} {to_folder})"
            return self.create_success_response(message, pddl_delta)
        except Exception as e:
            return self.create_error_response(f"移动失败: {str(e)}")