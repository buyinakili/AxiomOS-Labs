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
        return "创建新文件夹。\nPDDL作用: 添加文件夹事实(is_empty ?new_folder)和(is_created ?new_folder)\n注意：使用物理路径作为参数，如 'new_folder' 和 'storage_jail/root'"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "新文件夹名称（相对路径）"},
                "parent": {"type": "string", "description": "父文件夹物理路径（如 'storage_jail/root'）"}
            },
            "required": ["folder", "parent"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        folder_name = arguments["folder"]
        parent_path = arguments["parent"]
        
        # 解码参数（如果包含编码）
        # 注意：参数可能是编码的PDDL对象名（如 storage_jail_slash_test）
        # 我们需要将其解码为物理路径（如 storage_jail/test）
        decoded_folder_name = self._decode_path(folder_name) if '_slash_' in folder_name or '_dot_' in folder_name else folder_name
        decoded_parent_path = self._decode_path(parent_path) if '_slash_' in parent_path or '_dot_' in parent_path else parent_path
        
        # 如果解码后的文件夹名以解码后的父路径开头，则去除前缀
        # 例如：decoded_folder_name = "storage_jail/test", decoded_parent_path = "storage_jail"
        # 那么文件夹基本名应为 "test"
        if decoded_folder_name.startswith(decoded_parent_path + '/'):
            folder_basename = decoded_folder_name[len(decoded_parent_path) + 1:]
        else:
            folder_basename = decoded_folder_name
        
        # 构建完整文件夹路径（使用父路径和文件夹基本名）
        folder_full_path = os.path.join(decoded_parent_path, folder_basename)
        folder_path = self._safe_path(folder_full_path)
        
        # 检查文件夹是否已存在
        if os.path.exists(folder_path):
            return self.create_error_response(f"文件夹 {folder_name} 在父文件夹 {parent_path} 中已存在")
        
        # 检查父文件夹是否存在
        parent_full_path = self._safe_path(decoded_parent_path)
        if not os.path.exists(parent_full_path):
            return self.create_error_response(f"父文件夹 {parent_path} 不存在")
        
        try:
            # 创建文件夹
            os.makedirs(folder_path, exist_ok=True)
            
            # 编码路径用于PDDL事实（使用原始参数，因为PDDL事实需要编码名称）
            # 注意：PDDL事实使用编码的对象名，而不是物理路径
            encoded_folder = self._encode_path(folder_full_path)
            encoded_parent = self._encode_path(decoded_parent_path)
            
            # 根据PDDL定义，create_folder动作生成(is_empty ?d)和(is_created ?d)事实
            # 不再生成connected事实，因为connected谓词已被删除
            pddl_delta = f"+(is_empty {encoded_folder}) +(is_created {encoded_folder})"
            message = f"创建文件夹 {folder_name} 在父文件夹 {parent_path} 中"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"创建文件夹失败: {str(e)}")