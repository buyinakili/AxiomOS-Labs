#!/usr/bin/env python3
"""
复制文件技能
"""
import os
import shutil
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class CopySkill(MCPBaseSkill):
    """复制文件技能"""
    
    @property
    def name(self) -> str:
        return "copy"
    
    @property
    def description(self) -> str:
        return "复制文件到另一个文件夹。\nPDDL作用: 添加目标文件事实(at ?dst_file ?dst_folder)，标记为已复制(is_copied ?src_file ?dst_file)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "src_file": {"type": "string", "description": "源文件名（PDDL格式）"},
                "dst_file": {"type": "string", "description": "目标文件名（PDDL格式）"},
                "src_folder": {"type": "string", "description": "源文件夹名称"},
                "dst_folder": {"type": "string", "description": "目标文件夹名称"}
            },
            "required": ["src_file", "dst_file", "src_folder", "dst_folder"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        src_file = arguments["src_file"]
        dst_file = arguments["dst_file"]
        src_folder = arguments["src_folder"]
        dst_folder = arguments["dst_folder"]
        
        # 构建完整文件路径
        src_path = self._safe_path(src_folder, src_file)
        dst_path = self._safe_path(dst_folder, dst_file)
        
        # 检查源文件是否存在
        if not os.path.exists(src_path):
            return self.create_error_response(f"源文件 {src_file} 在文件夹 {src_folder} 中不存在")
        
        # 检查目标文件夹是否存在，如果不存在则创建
        dst_dir = os.path.dirname(dst_path)
        if not os.path.exists(dst_dir):
            try:
                os.makedirs(dst_dir, exist_ok=True)
            except Exception as e:
                return self.create_error_response(f"无法创建目标文件夹 {dst_folder}: {str(e)}")
        
        # 检查目标文件是否已存在
        if os.path.exists(dst_path):
            return self.create_error_response(f"目标文件 {dst_file} 已存在")
        
        try:
            # 复制文件
            shutil.copy2(src_path, dst_path)
            
            # 生成PDDL事实
            # 注意：PDDL中的文件名需要转换（. -> _dot_）
            pddl_src_file = src_file.replace('.', '_dot_')
            pddl_dst_file = dst_file.replace('.', '_dot_')
            
            pddl_delta = f"+(at {pddl_dst_file} {dst_folder}) +(is_copied {pddl_src_file} {pddl_dst_file})"
            message = f"复制文件 {src_file} 从 {src_folder} 到 {dst_file} 在 {dst_folder}"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"复制失败: {str(e)}")