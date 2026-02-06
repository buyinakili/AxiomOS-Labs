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
        return "重命名文件。\nPDDL作用: 删除旧名称事实(has_name ?file ?old_name)，添加新名称事实(has_name ?file ?new_name)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_name": {"type": "string", "description": "文件名（PDDL格式，可能包含 _dot_）"},
                "old_name": {"type": "string", "description": "旧文件名（不含扩展名）"},
                "new_name": {"type": "string", "description": "新文件名（不含扩展名）"},
                "folder": {"type": "string", "description": "文件所在文件夹名称"}
            },
            "required": ["file_name", "old_name", "new_name", "folder"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_name = arguments["file_name"]
        old_name = arguments["old_name"]
        new_name = arguments["new_name"]
        folder = arguments["folder"]
        
        # 构建完整文件路径
        old_path = self._safe_path(folder, file_name)
        
        if not os.path.exists(old_path):
            return self.create_error_response(f"文件 {file_name} 在文件夹 {folder} 中不存在")
        
        # 提取文件扩展名
        base_name, ext = os.path.splitext(file_name)
        
        # 构建新文件名（保持相同扩展名）
        new_file_name = f"{new_name}{ext}"
        new_path = self._safe_path(folder, new_file_name)
        
        # 检查新文件是否已存在
        if os.path.exists(new_path):
            return self.create_error_response(f"目标文件 {new_file_name} 已存在")
        
        try:
            # 重命名文件
            os.rename(old_path, new_path)
            
            # 生成PDDL事实
            # 注意：PDDL中的文件名需要转换（. -> _dot_）
            pddl_old_name = old_name.replace('.', '_dot_')
            pddl_new_name = new_name.replace('.', '_dot_')
            pddl_file_name = file_name.replace('.', '_dot_')
            
            pddl_delta = f"-(has_name {pddl_file_name} {pddl_old_name}) +(has_name {pddl_file_name} {pddl_new_name})"
            message = f"重命名文件 {file_name} 为 {new_file_name} 在文件夹 {folder}"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"重命名失败: {str(e)}")