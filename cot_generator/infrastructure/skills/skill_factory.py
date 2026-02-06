#!/usr/bin/env python3
"""
技能工厂 - 创建和管理九大原子动作技能
"""

import os
from typing import Dict
from .base_skill import BaseSkill, SkillRegistry
from .scan_skill import ScanSkill
from .move_skill import MoveSkill


class SkillFactory:
    """技能工厂"""
    
    @staticmethod
    def create_skill_registry(base_path: str = None) -> SkillRegistry:
        """
        创建技能注册表并注册所有技能
        
        :param base_path: 基础路径
        :return: 技能注册表
        """
        registry = SkillRegistry()
        
        # 注册九大原子动作技能
        skills = [
            ScanSkill(base_path),
            MoveSkill(base_path),
            # 其他技能将在后续实现
            # RemoveSkill(base_path),
            # RenameSkill(base_path),
            # CopySkill(base_path),
            # CompressSkill(base_path),
            # UncompressSkill(base_path),
            # CreateFileSkill(base_path),
            # CreateFolderSkill(base_path),
        ]
        
        for skill in skills:
            registry.register(skill)
        
        return registry
    
    @staticmethod
    def get_nine_atomic_skills() -> Dict[str, str]:
        """获取九大原子动作描述"""
        return {
            "scan": "扫描文件夹，获取文件夹内容信息",
            "move": "将文件从一个文件夹移动到另一个文件夹",
            "remove": "删除文件",
            "rename": "重命名文件",
            "copy": "复制文件",
            "compress": "压缩文件",
            "uncompress": "解压文件",
            "create_file": "创建文件",
            "create_folder": "创建文件夹",
        }
    
    @staticmethod
    def get_skill_pddl_signatures() -> Dict[str, str]:
        """获取所有技能的PDDL签名"""
        return {
            "scan": "(:action scan :parameters (?d - folder))",
            "move": "(:action move :parameters (?f - file ?src - folder ?dst - folder))",
            "remove": "(:action remove :parameters (?f - file ?d - folder))",
            "rename": "(:action rename :parameters (?f - file ?old_name - filename ?new_name - filename ?d - folder))",
            "copy": "(:action copy :parameters (?src - file ?dst - file ?src_folder - folder ?dst_folder - folder))",
            "compress": "(:action compress :parameters (?f - file ?d - folder ?a - archive))",
            "uncompress": "(:action uncompress :parameters (?a - archive ?d - folder ?f - file))",
            "create_file": "(:action create_file :parameters (?f - file ?name - filename ?d - folder))",
            "create_folder": "(:action create_folder :parameters (?d - folder ?parent - folder))",
        }
    
    @staticmethod
    def validate_pddl_action(pddl_action: str, registry: SkillRegistry) -> tuple:
        """
        验证PDDL动作
        
        :param pddl_action: PDDL动作字符串
        :param registry: 技能注册表
        :return: (是否有效, 错误信息, 技能实例)
        """
        if not pddl_action.startswith('(') or not pddl_action.endswith(')'):
            return False, "PDDL动作格式错误: 必须以括号包裹", None
        
        # 提取动作名称
        pddl_action = pddl_action[1:-1]  # 移除括号
        parts = pddl_action.split()
        if not parts:
            return False, "空的PDDL动作", None
        
        action_name = parts[0]
        
        # 检查技能是否存在
        if action_name not in registry.get_skill_names():
            return False, f"未知技能: {action_name}", None
        
        # 获取技能实例
        skill = registry.get_skill(action_name)
        
        # 验证参数数量
        args = parts[1:]  # 动作名称后的所有部分都是参数
        expected_params = skill._parse_pddl_parameters()
        
        if len(args) != len(expected_params):
            return False, f"参数数量错误: 期望 {len(expected_params)} 个，实际 {len(args)} 个", None
        
        return True, "验证通过", skill
    
    @staticmethod
    def execute_pddl_action(pddl_action: str, registry: SkillRegistry, base_path: str = None) -> dict:
        """
        执行PDDL动作
        
        :param pddl_action: PDDL动作字符串
        :param registry: 技能注册表
        :param base_path: 基础路径
        :return: 执行结果字典
        """
        # 验证PDDL动作
        is_valid, error_msg, skill = SkillFactory.validate_pddl_action(pddl_action, registry)
        if not is_valid:
            return {
                "success": False,
                "message": error_msg,
                "pddl_action": pddl_action,
                "add_facts": [],
                "del_facts": []
            }
        
        # 执行技能
        if base_path:
            # 创建新的技能实例使用指定的基础路径
            import copy
            new_skill = copy.copy(skill)
            new_skill.base_path = base_path
            result = new_skill.execute_from_pddl(pddl_action)
        else:
            result = skill.execute_from_pddl(pddl_action)
        
        return {
            "success": result.success,
            "message": result.message,
            "pddl_action": pddl_action,
            "add_facts": list(result.add_facts),
            "del_facts": list(result.del_facts)
        }


# 快捷函数
def create_default_skill_registry() -> SkillRegistry:
    """创建默认技能注册表"""
    return SkillFactory.create_skill_registry()

def get_all_skill_names() -> list:
    """获取所有技能名称"""
    return list(SkillFactory.get_nine_atomic_skills().keys())

def get_skill_pddl_signature(skill_name: str) -> str:
    """获取技能的PDDL签名"""
    signatures = SkillFactory.get_skill_pddl_signatures()
    return signatures.get(skill_name, "")

def execute_pddl_sequence(pddl_actions: list, base_path: str = None) -> list:
    """
    执行PDDL动作序列
    
    :param pddl_actions: PDDL动作字符串列表
    :param base_path: 基础路径
    :return: 执行结果列表
    """
    registry = create_default_skill_registry()
    results = []
    
    for pddl_action in pddl_actions:
        result = SkillFactory.execute_pddl_action(pddl_action, registry, base_path)
        results.append(result)
    
    return results