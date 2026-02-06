#!/usr/bin/env python3
"""
CoT数据生成器技能基类
所有九大原子动作技能应继承此类
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Set
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """技能执行结果"""
    success: bool
    message: str
    add_facts: Set[str] = None  # 执行成功后需要添加的PDDL事实
    del_facts: Set[str] = None  # 执行成功后需要删除的PDDL事实
    
    def __post_init__(self):
        if self.add_facts is None:
            self.add_facts = set()
        if self.del_facts is None:
            self.del_facts = set()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "message": self.message,
            "add_facts": list(self.add_facts),
            "del_facts": list(self.del_facts)
        }


class BaseSkill(ABC):
    """技能基类"""
    
    def __init__(self, base_path: str = None):
        """
        初始化技能
        
        :param base_path: 基础路径，技能只能操作此路径下的文件
        """
        self.base_path = base_path or os.getcwd()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称，对应PDDL动作名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述"""
        pass
    
    @property
    @abstractmethod
    def pddl_signature(self) -> str:
        """PDDL签名，格式: (:action name :parameters (...))"""
        pass
    
    @abstractmethod
    def execute(self, *args) -> ExecutionResult:
        """
        执行技能
        
        :param args: 参数列表，顺序必须与PDDL :parameters 顺序严格一致
        :return: 执行结果
        """
        pass
    
    def _safe_path(self, *parts: str) -> str:
        """
        安全构建路径，将PDDL格式的文件名（可能包含 _dot_）转换回实际文件名
        
        :param parts: 路径部分
        :return: 安全路径
        """
        # 将 _dot_ 转换回 .
        processed_parts = []
        for part in parts:
            if isinstance(part, str):
                part = part.replace('_dot_', '.')
            processed_parts.append(part)
        
        path = os.path.join(*processed_parts)
        
        # 确保路径在base_path内
        abs_path = os.path.abspath(path)
        abs_base = os.path.abspath(self.base_path)
        
        if not abs_path.startswith(abs_base):
            raise ValueError(f"路径 {abs_path} 不在基础路径 {abs_base} 内")
        
        return path
    
    def _extract_pddl_args(self, pddl_action: str) -> List[str]:
        """
        从PDDL动作字符串中提取参数
        
        :param pddl_action: PDDL动作字符串，如 "(move file1 root backup)"
        :return: 参数列表
        """
        # 移除括号和动作名称
        if pddl_action.startswith('(') and pddl_action.endswith(')'):
            pddl_action = pddl_action[1:-1]
        
        parts = pddl_action.split()
        if len(parts) < 2:
            return []
        
        # 第一个部分是动作名称，其余是参数
        return parts[1:]
    
    def execute_from_pddl(self, pddl_action: str) -> ExecutionResult:
        """
        从PDDL动作字符串执行技能
        
        :param pddl_action: PDDL动作字符串
        :return: 执行结果
        """
        args = self._extract_pddl_args(pddl_action)
        return self.execute(*args)
    
    def validate_args(self, *args) -> Tuple[bool, str]:
        """
        验证参数
        
        :param args: 参数列表
        :return: (是否有效, 错误信息)
        """
        # 基础验证：确保参数数量正确
        expected_params = self._parse_pddl_parameters()
        if len(args) != len(expected_params):
            return False, f"参数数量错误: 期望 {len(expected_params)} 个，实际 {len(args)} 个"
        
        # 可以添加更多验证逻辑
        return True, ""
    
    def _parse_pddl_parameters(self) -> List[str]:
        """
        解析PDDL签名中的参数
        
        :return: 参数类型列表
        """
        # 简单解析，实际实现需要更复杂的解析
        # 格式: (:action name :parameters (?f - file ?src - folder ?dst - folder))
        import re
        match = re.search(r':parameters\s*\(([^)]+)\)', self.pddl_signature)
        if not match:
            return []
        
        params_str = match.group(1)
        # 提取参数名（忽略类型）
        params = []
        for param in params_str.split('?'):
            if param.strip():
                # 获取参数名（第一个单词）
                param_name = param.strip().split()[0]
                params.append(param_name)
        
        return params
    
    def get_pddl_facts(self, *args) -> Tuple[Set[str], Set[str]]:
        """
        获取PDDL事实（用于测试和验证）
        
        :param args: 参数列表
        :return: (添加的事实集合, 删除的事实集合)
        """
        # 默认实现，子类可以覆盖
        return set(), set()


class SkillRegistry:
    """技能注册表"""
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
    
    def register(self, skill: BaseSkill) -> None:
        """注册技能"""
        self._skills[skill.name] = skill
    
    def get_skill(self, name: str) -> BaseSkill:
        """获取技能"""
        if name not in self._skills:
            raise KeyError(f"技能未注册: {name}")
        return self._skills[name]
    
    def get_all_skills(self) -> Dict[str, BaseSkill]:
        """获取所有技能"""
        return self._skills.copy()
    
    def get_skill_names(self) -> List[str]:
        """获取所有技能名称"""
        return list(self._skills.keys())
    
    def execute_skill(self, pddl_action: str, base_path: str = None) -> ExecutionResult:
        """
        执行PDDL动作
        
        :param pddl_action: PDDL动作字符串
        :param base_path: 基础路径
        :return: 执行结果
        """
        # 提取动作名称
        if pddl_action.startswith('(') and pddl_action.endswith(')'):
            pddl_action = pddl_action[1:-1]
        
        parts = pddl_action.split()
        if not parts:
            return ExecutionResult(False, "空的PDDL动作")
        
        action_name = parts[0]
        
        if action_name not in self._skills:
            return ExecutionResult(False, f"未知技能: {action_name}")
        
        skill = self._skills[action_name]
        if base_path:
            # 创建新的技能实例使用指定的基础路径
            import copy
            new_skill = copy.copy(skill)
            new_skill.base_path = base_path
            return new_skill.execute_from_pddl(pddl_action)
        else:
            return skill.execute_from_pddl(pddl_action)