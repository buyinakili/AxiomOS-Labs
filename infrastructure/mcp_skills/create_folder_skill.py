#!/usr/bin/env python3
"""
创建文件夹技能
"""
import os
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class CreateFolderSkill(MCPBaseSkill):
    """创建文件夹技能"""
    
    @property
    def name(self) -> str:
        return "create_folder"
    
    @property
    def description(self) -> str:
        return "创建新文件夹。\nPDDL作用: 添加文件夹连接事实(connected ?parent ?new_folder)，标记为已创建(is_created ?new_folder)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "新文件夹名称"},
                "parent": {"type": "string", "description": "父文件夹名称"}
            },
            "required": ["folder", "parent"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        folder = arguments["folder"]
        parent = arguments["parent"]
        
        # 构建完整文件夹路径
        folder_path = self._safe_path(parent, folder)
        
        # 检查文件夹是否已存在
        if os.path.exists(folder_path):
            return self.create_error_response(f"文件夹 {folder} 在父文件夹 {parent} 中已存在")
        
        # 检查父文件夹是否存在
        parent_path = self._safe_path(parent)
        if not os.path.exists(parent_path):
            return self.create_error_response(f"父文件夹 {parent} 不存在")
        
        try:
            # 创建文件夹
            os.makedirs(folder_path, exist_ok=True)
            
            # 生成PDDL事实
            # 注意：PDDL中的文件夹名需要转换（. -> _dot_）
            pddl_folder = folder.replace('.', '_dot_')
            pddl_parent = parent.replace('.', '_dot_')
            
            # 根据PDDL定义，create_folder动作生成(is_empty ?d)和(is_created ?d)事实
            # 注意：前提条件中已经要求(connected ?parent ?d)，所以不需要在效果中再次添加
            pddl_delta = f"+(is_empty {pddl_folder}) +(is_created {pddl_folder})"
            message = f"创建文件夹 {folder} 在父文件夹 {parent} 中"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"创建文件夹失败: {str(e)}")