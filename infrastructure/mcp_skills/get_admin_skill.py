#!/usr/bin/env python3
"""
获取管理员权限技能
"""
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class GetAdminSkill(MCPBaseSkill):
    """获取管理员权限"""
    
    @property
    def name(self) -> str:
        return "get_admin"
    
    @property
    def description(self) -> str:
        return "获取管理员权限。\nPDDL作用: 添加(has_admin_rights)事实，使后续需要权限的操作成为可能"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        message = "已获取管理员权限"
        pddl_delta = "(has_admin_rights)"
        return self.create_success_response(message, pddl_delta)