#!/usr/bin/env python3
"""
移动文件技能
"""
import os
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
        return "移动文件到另一个文件夹。\nPDDL作用: 删除源位置事实(at ?file ?from_folder)，添加目标位置事实(at ?file ?to_folder)\n注意：使用物理路径作为参数，如 'storage_jail/root/document.txt' 和 'storage_jail/backup'"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_file": {"type": "string", "description": "源文件物理路径（如 'storage_jail/root/document.txt'）"},
                "target_folder": {"type": "string", "description": "目标文件夹物理路径（如 'storage_jail/backup'）"}
            },
            "required": ["source_file", "target_folder"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        source_file = arguments["source_file"]
        target_folder = arguments["target_folder"]
        
        # 提取文件名
        filename = os.path.basename(source_file)
        # 构建目标文件路径
        target_file = os.path.join(target_folder, filename)
        
        src_path = self._safe_path(source_file)
        dst_path = self._safe_path(target_file)
        
        # 检查源文件是否存在
        if not os.path.exists(src_path):
            return self.create_error_response(f"源文件 {source_file} 不存在")
        
        # 检查目标文件夹是否存在，如果不存在则创建
        target_folder_path = self._safe_path(target_folder)
        if not os.path.exists(target_folder_path):
            try:
                os.makedirs(target_folder_path, exist_ok=True)
            except Exception as e:
                return self.create_error_response(f"无法创建目标文件夹 {target_folder}: {str(e)}")
        
        try:
            shutil.move(src_path, dst_path)
            
            # 编码路径用于PDDL事实
            encoded_source_file = self._encode_path(source_file)
            encoded_target_file = self._encode_path(target_file)
            
            # 提取源文件夹和目标文件夹路径
            source_folder = os.path.dirname(source_file)
            encoded_source_folder = self._encode_path(source_folder)
            encoded_target_folder = self._encode_path(target_folder)
            
            message = f"移动 {source_file} 到 {target_folder}"
            pddl_delta = f"-(at {encoded_source_file} {encoded_source_folder}) +(at {encoded_target_file} {encoded_target_folder})"
            return self.create_success_response(message, pddl_delta)
        except Exception as e:
            return self.create_error_response(f"移动失败: {str(e)}")