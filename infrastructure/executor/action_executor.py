"""动作执行器实现"""
import os
import importlib.util
from typing import Dict, List
from interface.executor import IExecutor, ExecutionResult
from interface.skill import ISkill


class ActionExecutor(IExecutor):
    """动作执行器实现"""

    def __init__(self, storage_path: str = None):
        """
        初始化执行器

        :param storage_path: 物理存储路径
        """
        self.storage_path = storage_path or ""
        self.skills: Dict[str, ISkill] = {}
        self.execution_history: List[str] = []

    def execute(self, action_str: str) -> ExecutionResult:
        """
        执行一个动作

        :param action_str: 动作字符串（如 "move file_a folder_x folder_y"）
        :return: ExecutionResult对象
        """
        # 解析动作
        parts = action_str.strip().split()
        if not parts:
            return ExecutionResult(False, "动作字符串为空")

        action_name = parts[0]
        args = parts[1:]

        # 记录执行历史
        self.execution_history.append(action_name.lower())

        # 检查技能是否存在
        if action_name not in self.skills:
            return ExecutionResult(
                False,
                f"未知技能: {action_name}"
            )

        try:
            # 执行技能
            result = self.skills[action_name].execute(args)
            return result
        except Exception as e:
            return ExecutionResult(
                False,
                f"执行崩溃: {str(e)}"
            )

    def get_execution_history(self) -> List[str]:
        """
        获取执行历史记录

        :return: 执行过的动作名称列表
        """
        return self.execution_history.copy()

    def clear_execution_history(self):
        """清空执行历史记录"""
        self.execution_history.clear()

    def register_skill(self, skill: ISkill):
        """
        注册一个技能

        :param skill: 技能实例
        """
        # 设置技能的base_path
        if hasattr(skill, 'base_path'):
            skill.base_path = self.storage_path

        self.skills[skill.name] = skill
        print(f"[Executor] 技能已注册: {skill.name}")

    def register_skill_from_file(self, file_path: str) -> bool:
        """
        从Python文件动态加载技能

        :param file_path: 技能文件路径
        :return: 是否成功
        """
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找技能类
            if hasattr(module, 'GeneratedSkill'):
                skill_instance = module.GeneratedSkill()
                self.register_skill(skill_instance)
                return True
            else:
                print(f"[Executor] 文件中未找到GeneratedSkill类: {file_path}")
                return False

        except Exception as e:
            print(f"[Executor] 加载技能失败: {str(e)}")
            return False

    def get_registered_skills(self) -> List[str]:
        """
        获取已注册的技能列表

        :return: 技能名称列表
        """
        return list(self.skills.keys())

    def set_storage_path(self, path: str):
        """
        设置存储路径，并更新所有技能的base_path

        :param path: 存储路径
        """
        self.storage_path = path
        for skill in self.skills.values():
            if hasattr(skill, 'base_path'):
                skill.base_path = path
