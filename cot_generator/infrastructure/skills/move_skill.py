#!/usr/bin/env python3
"""
move技能实现
对应PDDL动作: (:action move :parameters (?f - file ?src - folder ?dst - folder))
"""

import os
import shutil
from typing import Set, Tuple
from .base_skill import BaseSkill, ExecutionResult


class MoveSkill(BaseSkill):
    """移动文件技能"""
    
    @property
    def name(self) -> str:
        return "move"
    
    @property
    def description(self) -> str:
        return "将文件从一个文件夹移动到另一个文件夹"
    
    @property
    def pddl_signature(self) -> str:
        return "(:action move :parameters (?f - file ?src - folder ?dst - folder))"
    
    def execute(self, file_name: str, src_folder: str, dst_folder: str) -> ExecutionResult:
        """
        执行移动
        
        :param file_name: 文件名称（PDDL对象名）
        :param src_folder: 源文件夹名称
        :param dst_folder: 目标文件夹名称
        :return: 执行结果
        """
        try:
            # 将PDDL对象名转换为实际路径
            src_path = self._safe_path(src_folder, file_name)
            dst_path = self._safe_path(dst_folder, file_name)
            
            # 检查源文件是否存在
            if not os.path.exists(src_path):
                return ExecutionResult(
                    success=False,
                    message=f"源文件不存在: {src_path}",
                    add_facts=set(),
                    del_facts=set()
                )
            
            # 检查目标文件夹是否存在
            dst_dir = os.path.dirname(dst_path)
            if not os.path.exists(dst_dir):
                # 尝试创建目标文件夹
                try:
                    os.makedirs(dst_dir, exist_ok=True)
                except Exception as e:
                    return ExecutionResult(
                        success=False,
                        message=f"无法创建目标文件夹 {dst_dir}: {str(e)}",
                        add_facts=set(),
                        del_facts=set()
                    )
            
            # 检查目标文件是否已存在
            if os.path.exists(dst_path):
                return ExecutionResult(
                    success=False,
                    message=f"目标文件已存在: {dst_path}",
                    add_facts=set(),
                    del_facts=set()
                )
            
            # 执行移动操作
            try:
                shutil.move(src_path, dst_path)
            except PermissionError:
                return ExecutionResult(
                    success=False,
                    message=f"无权限移动文件: {src_path} -> {dst_path}",
                    add_facts=set(),
                    del_facts=set()
                )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    message=f"移动失败: {str(e)}",
                    add_facts=set(),
                    del_facts=set()
                )
            
            # 生成PDDL事实
            add_facts = {
                f"(at {file_name} {dst_folder})",
                f"(is_created {file_name})"
            }
            
            del_facts = {
                f"(at {file_name} {src_folder})"
            }
            
            message = f"成功移动文件: {src_path} -> {dst_path}"
            
            return ExecutionResult(
                success=True,
                message=message,
                add_facts=add_facts,
                del_facts=del_facts
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"移动失败: {str(e)}",
                add_facts=set(),
                del_facts=set()
            )
    
    def get_pddl_facts(self, file_name: str, src_folder: str, dst_folder: str) -> Tuple[Set[str], Set[str]]:
        """
        获取PDDL事实
        
        :param file_name: 文件名称
        :param src_folder: 源文件夹名称
        :param dst_folder: 目标文件夹名称
        :return: (添加的事实集合, 删除的事实集合)
        """
        add_facts = {
            f"(at {file_name} {dst_folder})",
            f"(is_created {file_name})"
        }
        del_facts = {
            f"(at {file_name} {src_folder})"
        }
        
        return add_facts, del_facts