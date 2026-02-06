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
        return "创建新文件。\nPDDL作用: 添加文件存在事实(at ?file ?folder)和文件名事实(has_name ?file ?name)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "文件名（PDDL格式，可能包含 _dot_）"},
                "name": {"type": "string", "description": "文件名称（不含扩展名）"},
                "folder": {"type": "string", "description": "文件所在文件夹名称"},
                "content": {"type": "string", "description": "文件内容（可选）", "default": ""}
            },
            "required": ["file", "name", "folder"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        file = arguments["file"]
        name = arguments["name"]
        folder = arguments["folder"]
        content = arguments.get("content", "")
        
        # 构建完整文件路径
        file_path = self._safe_path(folder, file)
        
        # 检查文件是否已存在
        if os.path.exists(file_path):
            return self.create_error_response(f"文件 {file} 在文件夹 {folder} 中已存在")
        
        # 检查文件夹是否存在，如果不存在则创建
        folder_path = self._safe_path(folder)
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception as e:
                return self.create_error_response(f"无法创建文件夹 {folder}: {str(e)}")
        
        try:
            # 创建文件并写入内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 生成PDDL事实
            # 注意：PDDL中的文件名需要转换（. -> _dot_）
            pddl_file = file.replace('.', '_dot_')
            pddl_name = name.replace('.', '_dot_')
            
            pddl_delta = f"+(at {pddl_file} {folder}) +(has_name {pddl_file} {pddl_name})"
            message = f"创建文件 {file} 在文件夹 {folder}，名称: {name}"
            
            if content:
                message += f"，内容长度: {len(content)} 字符"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"创建文件失败: {str(e)}")