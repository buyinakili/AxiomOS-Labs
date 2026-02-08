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
        return "复制文件到另一个文件夹。\nPDDL作用: 添加目标文件事实(at ?dst_file ?dst_folder)，标记为已复制(is_copied ?src_file ?dst_file)\n注意：使用物理路径作为参数，如 'storage_jail/root/document.txt' 和 'storage_jail/backup/document_copy.txt'"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_file": {"type": "string", "description": "源文件物理路径（如 'storage_jail/root/document.txt'）"},
                "target_file": {"type": "string", "description": "目标文件物理路径（如 'storage_jail/backup/document_copy.txt'）"}
            },
            "required": ["source_file", "target_file"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        source_file = arguments["source_file"]
        target_file = arguments["target_file"]
        
        # 构建完整文件路径
        src_path = self._safe_path(source_file)
        dst_path = self._safe_path(target_file)
        
        # 检查源文件是否存在
        if not os.path.exists(src_path):
            return self.create_error_response(f"源文件 {source_file} 不存在")
        
        # 检查目标文件夹是否存在，如果不存在则创建
        dst_dir = os.path.dirname(dst_path)
        if not os.path.exists(dst_dir):
            try:
                os.makedirs(dst_dir, exist_ok=True)
            except Exception as e:
                return self.create_error_response(f"无法创建目标文件夹 {dst_dir}: {str(e)}")
        
        # 检查目标文件是否已存在
        if os.path.exists(dst_path):
            return self.create_error_response(f"目标文件 {target_file} 已存在")
        
        try:
            # 复制文件
            shutil.copy2(src_path, dst_path)
            
            # 编码路径用于PDDL事实
            encoded_src_file = self._encode_path(source_file)
            encoded_dst_file = self._encode_path(target_file)
            
            # 提取源文件夹和目标文件夹路径
            src_folder = os.path.dirname(source_file)
            dst_folder = os.path.dirname(target_file)
            encoded_src_folder = self._encode_path(src_folder)
            encoded_dst_folder = self._encode_path(dst_folder)
            
            pddl_delta = f"+(at {encoded_dst_file} {encoded_dst_folder}) +(is_copied {encoded_src_file} {encoded_dst_file})"
            message = f"复制文件 {source_file} 到 {target_file}"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"复制失败: {str(e)}")