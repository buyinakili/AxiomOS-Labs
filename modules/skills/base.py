# modules/skills/base.py
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SkillResult:
    is_success: bool
    message: str
    # 关键优化：直接返回 PDDL 事实，而不是让 LLM 去猜
    add_facts: List[str] = field(default_factory=list) 
    del_facts: List[str] = field(default_factory=list)

class BaseSkill(ABC):
    def __init__(self):
        self.base_path = os.path.abspath("./storage")

    @property
    @abstractmethod
    def name(self) -> str:
        """对应 PDDL 中的 action name，如 'move', 'scan'"""
        pass

    @abstractmethod
    def execute(self, args: List[str]) -> SkillResult:
        """
        args: PDDL action 的参数列表，例如 ['report_dot_txt', 'root', 'backup']
        """
        pass

    def _safe_path(self, *parts):
        """辅助函数：处理 _dot_ 转义并生成绝对路径"""
        clean_parts = [p.replace("_dot_", ".") for p in parts]
        return os.path.join(self.base_path, *clean_parts)