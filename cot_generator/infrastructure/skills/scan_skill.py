#!/usr/bin/env python3
"""
scan技能实现
对应PDDL动作: (:action scan :parameters (?d - folder))
"""

import os
from typing import Set, Tuple
from .base_skill import BaseSkill, ExecutionResult


class ScanSkill(BaseSkill):
    """扫描文件夹技能"""
    
    @property
    def name(self) -> str:
        return "scan"
    
    @property
    def description(self) -> str:
        return "扫描文件夹，获取文件夹内容信息"
    
    @property
    def pddl_signature(self) -> str:
        return "(:action scan :parameters (?d - folder))"
    
    def execute(self, folder_name: str) -> ExecutionResult:
        """
        执行扫描
        
        :param folder_name: 文件夹名称（PDDL对象名）
        :return: 执行结果
        """
        try:
            # 将PDDL对象名转换为实际路径
            # 假设文件夹名就是路径名（实际项目中可能需要映射）
            folder_path = self._safe_path(folder_name)
            
            # 检查文件夹是否存在
            if not os.path.exists(folder_path):
                return ExecutionResult(
                    success=False,
                    message=f"文件夹不存在: {folder_path}",
                    add_facts=set(),
                    del_facts=set()
                )
            
            if not os.path.isdir(folder_path):
                return ExecutionResult(
                    success=False,
                    message=f"路径不是文件夹: {folder_path}",
                    add_facts=set(),
                    del_facts=set()
                )
            
            # 扫描文件夹内容
            files = []
            subdirs = []
            try:
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isfile(item_path):
                        files.append(item)
                    elif os.path.isdir(item_path):
                        subdirs.append(item)
            except PermissionError:
                return ExecutionResult(
                    success=False,
                    message=f"无权限扫描文件夹: {folder_path}",
                    add_facts=set(),
                    del_facts=set()
                )
            
            # 生成PDDL事实
            add_facts = {
                f"(scanned {folder_name})"  # 主要事实：文件夹已扫描
            }
            
            # 可以添加更多事实，如文件夹中的文件列表
            # 在实际系统中，可能需要将扫描结果存储到知识库
            
            message = f"成功扫描文件夹: {folder_path}\n"
            message += f"  文件数: {len(files)}\n"
            message += f"  子文件夹数: {len(subdirs)}"
            
            if files:
                message += f"\n  文件示例: {', '.join(files[:5])}" + ("..." if len(files) > 5 else "")
            
            return ExecutionResult(
                success=True,
                message=message,
                add_facts=add_facts,
                del_facts=set()
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"扫描失败: {str(e)}",
                add_facts=set(),
                del_facts=set()
            )
    
    def get_pddl_facts(self, folder_name: str) -> Tuple[Set[str], Set[str]]:
        """
        获取PDDL事实
        
        :param folder_name: 文件夹名称
        :return: (添加的事实集合, 删除的事实集合)
        """
        add_facts = {
            f"(scanned {folder_name})"
        }
        del_facts = set()
        
        return add_facts, del_facts