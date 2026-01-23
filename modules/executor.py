# modules/executor.py

import importlib.util
import os
from typing import Dict
from .skills.base import BaseSkill, SkillResult
from .skills import filesystem 

class ActionExecutor:
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.register_all_skills()
        self.execution_history = []

    def register_all_skills(self):
        # 1. 首先加载硬编码的基础技能 (filesystem.py 里的)
        from .skills import filesystem
        self._register(filesystem.ScanSkill())
        self._register(filesystem.MoveSkill())
        self._register(filesystem.GetAdminSkill())
        self._register(filesystem.CompressSkill())

        # 2. 【关键修复】动态加载 skills 目录下所有新增的 _skill.py 文件
        skills_dir = os.path.join(os.path.dirname(__file__), "skills")
        for filename in os.listdir(skills_dir):
            if filename.endswith("_skill.py") and filename != "base.py":
                module_name = f"modules.skills.{filename[:-3]}" # 去掉 .py
                try:
                    module = importlib.import_module(module_name)
                    # 寻找模块中继承自 BaseSkill 的类（或者你约定的 GeneratedSkill）
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and attr_name.endswith("Skill") and attr_name != "BaseSkill":
                            self._register(attr())
                except Exception as e:
                    print(f"[Executor] 加载扩展技能 {filename} 失败: {e}")

    def _register(self, skill: BaseSkill):
        self.skills[skill.name] = skill
        print(f"[System] Skill Loaded: {skill.name}")

    #动态加载沙盒技能
    def register_dynamic_skill(self, file_path: str):
        """
        从指定路径动态加载一个 Python 模块并注册其中的技能类
        """
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 约定：新生成的脚本中必须包含一个名为 'GeneratedSkill' 的类
            if hasattr(module, 'GeneratedSkill'):
                skill_instance = module.GeneratedSkill()
                self._register(skill_instance)
                return True
            else:
                print(f"[Executor] 动态加载失败：{file_path} 中未找到 GeneratedSkill 类")
                return False
        except Exception as e:
            print(f"[Executor] 动态加载崩溃: {str(e)}")
            return False
    def get_registered_skills(self):
        return list(self.skills.keys())
    # modules/executor.py

    def execute_step(self, action_input, args=None) -> SkillResult:
        """
        兼容性修复：支持两种调用方式
        1. execute_step("rename_file a_dot_txt b_dot_txt root")
        2. execute_step("rename_file", ["a_dot_txt", "b_dot_txt", "root"])
        """
        if isinstance(action_input, str) and args is None:
            # 方式 1：解析字符串指令
            parts = action_input.strip().split()
            if not parts:
                return SkillResult(False, "指令为空")
            action_name = parts[0]
            actual_args = parts[1:]
        else:
            # 方式 2：传统的参数分离方式
            action_name = action_input
            actual_args = args if args is not None else []
        self.execution_history.append(action_name.lower())
        # 1. 检查技能是否存在
        if action_name not in self.skills:
            return SkillResult(False, f"系统错误: 未知指令 '{action_name}'")
        
        # 2. 记录执行历史（进化审计核心：必须记录！）
        

        try:
            # 3. 执行物理动作
            # 注意：这里调用技能的 execute 方法，传入解析后的参数列表
            result = self.skills[action_name].execute(actual_args)
            return result
        except Exception as e:
            return SkillResult(False, f"执行崩溃: {str(e)}")