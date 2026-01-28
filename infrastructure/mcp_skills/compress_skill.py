#!/usr/bin/env python3
"""
压缩文件技能
"""
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class CompressSkill(MCPBaseSkill):
    """压缩文件"""
    
    @property
    def name(self) -> str:
        return "compress"
    
    @property
    def description(self) -> str:
        return "压缩文件。\nPDDL作用: 创建新文件事实(is_created ?archive)，添加位置事实(at ?archive ?folder)，标记压缩关系(is_compressed ?file ?archive)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_name": {"type": "string", "description": "要压缩的文件名"},
                "folder": {"type": "string", "description": "文件所在文件夹"},
                "archive_name": {"type": "string", "description": "压缩包名称"}
            },
            "required": ["file_name", "folder", "archive_name"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_name = arguments["file_name"]
        folder = arguments["folder"]
        archive_name = arguments["archive_name"]
        
        # 简化模拟逻辑
        message = f"压缩 {file_name} 为 {archive_name}"
        pddl_delta = f"(is_created {archive_name}) (at {archive_name} {folder}) (is_compressed {file_name} {archive_name})"
        return self.create_success_response(message, pddl_delta)