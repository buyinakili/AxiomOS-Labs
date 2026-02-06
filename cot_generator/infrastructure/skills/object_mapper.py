#!/usr/bin/env python3
"""
对象映射器 - 将PDDL对象名映射到实际文件系统路径
"""

import os
from typing import Dict, Optional


class ObjectMapper:
    """PDDL对象到文件系统路径的映射器"""
    
    def __init__(self, base_path: str):
        """
        初始化对象映射器
        
        :param base_path: 基础路径
        """
        self.base_path = base_path
        self._mapping: Dict[str, str] = {}
        self._reverse_mapping: Dict[str, str] = {}
        
        # 初始化默认映射
        self._init_default_mapping()
    
    def _init_default_mapping(self):
        """初始化默认映射"""
        # 映射常见的PDDL对象名
        default_mappings = {
            "root": ".",
            "home": ".",
            "backup": "backup",
            "temp": "temp",
            "documents": "documents",
        }
        
        for pddl_name, fs_name in default_mappings.items():
            self.add_mapping(pddl_name, fs_name)
    
    def add_mapping(self, pddl_name: str, fs_name: str) -> None:
        """
        添加映射
        
        :param pddl_name: PDDL对象名
        :param fs_name: 文件系统名称（相对路径）
        """
        fs_path = os.path.join(self.base_path, fs_name)
        self._mapping[pddl_name] = fs_path
        self._reverse_mapping[fs_path] = pddl_name
    
    def get_path(self, pddl_name: str) -> Optional[str]:
        """
        获取PDDL对象对应的文件系统路径
        
        :param pddl_name: PDDL对象名
        :return: 文件系统路径，如果未找到则返回None
        """
        if pddl_name in self._mapping:
            return self._mapping[pddl_name]
        
        # 如果没有显式映射，尝试直接使用对象名作为路径
        # 注意：这可能需要根据实际需求调整
        potential_path = os.path.join(self.base_path, pddl_name)
        if os.path.exists(potential_path):
            self._mapping[pddl_name] = potential_path
            self._reverse_mapping[potential_path] = pddl_name
            return potential_path
        
        return None
    
    def get_pddl_name(self, fs_path: str) -> Optional[str]:
        """
        获取文件系统路径对应的PDDL对象名
        
        :param fs_path: 文件系统路径
        :return: PDDL对象名，如果未找到则返回None
        """
        # 尝试精确匹配
        if fs_path in self._reverse_mapping:
            return self._reverse_mapping[fs_path]
        
        # 尝试相对路径匹配
        rel_path = os.path.relpath(fs_path, self.base_path)
        if rel_path in self._mapping:
            return rel_path
        
        # 如果没有映射，创建新映射
        # 使用路径的最后一部分作为PDDL对象名
        pddl_name = os.path.basename(fs_path)
        if not pddl_name:
            pddl_name = "root"
        
        # 确保名称唯一
        counter = 1
        original_name = pddl_name
        while pddl_name in self._mapping:
            pddl_name = f"{original_name}_{counter}"
            counter += 1
        
        self.add_mapping(pddl_name, os.path.relpath(fs_path, self.base_path))
        return pddl_name
    
    def map_pddl_action(self, pddl_action: str) -> str:
        """
        映射PDDL动作中的对象名
        
        :param pddl_action: PDDL动作字符串，如 "(scan root)"
        :return: 映射后的PDDL动作字符串
        """
        if not pddl_action.startswith('(') or not pddl_action.endswith(')'):
            return pddl_action
        
        # 提取动作和参数
        content = pddl_action[1:-1]  # 移除括号
        parts = content.split()
        
        if not parts:
            return pddl_action
        
        # 第一个部分是动作名称，其余是参数
        action_name = parts[0]
        args = parts[1:]
        
        # 映射参数
        mapped_args = []
        for arg in args:
            # 检查是否是PDDL对象名（不是类型或其他标识符）
            if not arg.startswith('?') and not arg.startswith('-'):
                path = self.get_path(arg)
                if path:
                    # 使用实际路径
                    mapped_args.append(os.path.basename(path))
                else:
                    mapped_args.append(arg)
            else:
                mapped_args.append(arg)
        
        # 重新构建PDDL动作
        mapped_parts = [action_name] + mapped_args
        return f"({' '.join(mapped_parts)})"
    
    def create_file_mapping(self, file_path: str) -> str:
        """
        为文件创建PDDL对象名映射
        
        :param file_path: 文件路径
        :return: PDDL对象名
        """
        # 获取文件名（不含扩展名）作为基础
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        # 替换点号为下划线（PDDL兼容）
        pddl_name = name_without_ext.replace('.', '_dot_')
        
        # 确保名称唯一
        counter = 1
        original_name = pddl_name
        while pddl_name in self._mapping:
            pddl_name = f"{original_name}_{counter}"
            counter += 1
        
        self.add_mapping(pddl_name, os.path.relpath(file_path, self.base_path))
        return pddl_name
    
    def get_all_mappings(self) -> Dict[str, str]:
        """获取所有映射"""
        return self._mapping.copy()


# 快捷函数
def create_default_mapper(base_path: str) -> ObjectMapper:
    """创建默认对象映射器"""
    mapper = ObjectMapper(base_path)
    
    # 扫描基础路径，添加现有文件和文件夹的映射
    if os.path.exists(base_path):
        for root, dirs, files in os.walk(base_path):
            # 添加文件夹映射
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                mapper.get_pddl_name(dir_path)  # 这会自动创建映射
            
            # 添加文件映射
            for file_name in files:
                file_path = os.path.join(root, file_name)
                mapper.create_file_mapping(file_path)
    
    return mapper