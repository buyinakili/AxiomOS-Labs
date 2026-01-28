"""
MCP技能包
"""
from .mcp_base_skill import MCPBaseSkill
from .scan_skill import ScanSkill
from .move_skill import MoveSkill
from .get_admin_skill import GetAdminSkill
from .compress_skill import CompressSkill
from .remove_file_skill import RemoveFileSkill

__all__ = [
    "MCPBaseSkill",
    "ScanSkill",
    "MoveSkill",
    "GetAdminSkill",
    "CompressSkill",
    "RemoveFileSkill",
]