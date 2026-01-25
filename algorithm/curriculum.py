"""课程生成算法 - 纯算法逻辑"""
import os
import json
import time
import re
from typing import Dict, Optional
from interface.executor import IExecutor
from interface.llm import ILLM
from interface.storage import IStorage


class CurriculumAlgorithm:
    """
    课程生成算法 - 负责智能出题
    纯算法逻辑，只依赖接口
    """

    def __init__(self, llm: ILLM, storage: IStorage):
        """
        初始化课程算法

        :param llm: LLM客户端
        :param storage: 存储接口
        """
        self.llm = llm
        self.storage = storage

    def propose_next_task(self, executor: IExecutor) -> Optional[Dict]:
        """
        自主出题：根据当前系统能力提出下一个学习任务

        :param executor: 执行器实例
        :return: 任务数据
        """
        # 1. 读取当前PDDL能力
        domain_content = self.storage.read_domain("file_management")

        # 2. 提取已学会的技能列表
        learned_skills = self._extract_learned_actions(domain_content)

        # 3. 获取环境快照
        env_info = self._get_env_snapshot()

        # 4. 获取当前执行器里已有的技能名
        available_skills = executor.get_registered_skills()

        # 构建Prompt
        prompt = f"""
你现在是 AIOS 的【首席训练教官】。

【系统进化状态】:
目前系统已经完全掌握并严禁重复出现的技能: {learned_skills}

【当前沙盒物理环境 (World State)】:
{env_info}

【当前系统详细能力 (PDDL Domain)】:
{domain_content}

【可用预设动作 (Setup Actions)】:
{available_skills}

【你的任务】:
提出一个目前系统【无法完成】的文件系统新任务。

【核心要求 - 违者扣分】:
1. 严禁出题：严禁提出任何可以使用上述已掌握技能（如 {learned_skills}）完成的任务。
2. 简单原则：新任务必须尽可能简单，只需添加【一个】新功能即可实现。
3. 真实性：必须基于【物理环境】中存在的目录出题。
4. 所有的文件名点号必须转义，如 'test.log' 写作 'test_dot_log'。
5. 【解耦】：setup_actions 仅允许使用 create_file 或 create_folder。
6. 【禁止预设感知/权限】：严禁在 setup_actions 中加入 'scan' 或 'get_admin'。

【输出 JSON 格式】:
{{
    "task_name": "任务简称",
    "goal": "自然语言指令 (例如: 将 root 下的 a_dot_txt 修改权限为只读)",
    "rationale": "为什么这个任务目前无法完成？(例如: 当前 Domain 中没有 chmod 动作)",
    "setup_actions": [
        ["create_file", "a_dot_txt", "root"]
    ]
}}
"""

        # 调用LLM
        return self._call_llm_with_retry(prompt)

    def propose_specific_task(self, task_goal: str, executor: IExecutor) -> Optional[Dict]:
        """
        指定出题：根据用户指定的目标生成学习任务

        :param task_goal: 用户指定的任务目标
        :param executor: 执行器实例
        :return: 任务数据
        """
        # 1. 读取当前PDDL能力
        domain_content = self.storage.read_domain("file_management")

        # 2. 提取已学会的技能列表
        learned_skills = self._extract_learned_actions(domain_content)

        # 3. 获取环境快照
        env_info = self._get_env_snapshot()

        # 4. 获取当前执行器里已有的技能名
        available_skills = executor.get_registered_skills()

        # 构建Prompt
        prompt = f"""
你现在是 AIOS 的【首席训练教官】。

【用户指定的学习目标】:
{task_goal}

【系统进化状态】:
目前系统已经完全掌握的技能: {learned_skills}

【当前沙盒物理环境 (World State)】:
{env_info}

【当前系统详细能力 (PDDL Domain)】:
{domain_content}

【可用预设动作 (Setup Actions)】:
{available_skills}

【你的任务】:
根据用户指定的目标，设计一个具体的学习任务。

【核心要求】:
1. 任务必须与用户指定的目标相关
2. 任务应该尽可能简单，易于学习
3. 真实性：必须基于【物理环境】中存在的目录出题
4. 所有的文件名点号必须转义，如 'test.log' 写作 'test_dot_log'
5. setup_actions 仅允许使用 create_file 或 create_folder
6. 严禁在 setup_actions 中加入 'scan' 或 'get_admin'

【输出 JSON 格式】:
{{
    "task_name": "任务简称",
    "goal": "自然语言指令",
    "rationale": "为什么需要学习这个任务",
    "setup_actions": [
        ["create_file", "test_dot_txt", "root"]
    ]
}}
"""

        return self._call_llm_with_retry(prompt)

    def _get_env_snapshot(self) -> str:
        """扫描storage目录，生成环境快照"""
        storage_path = self.storage.get_storage_path()
        snapshot = []

        if not os.path.exists(storage_path):
            return "当前存储空间 (storage) 为空。"

        for root, dirs, files in os.walk(storage_path):
            rel_path = os.path.relpath(root, storage_path)
            logic_path = "root" if rel_path == "." else rel_path
            safe_files = [f.replace(".", "_dot_") for f in files]
            snapshot.append(f"- 目录 [{logic_path}] 包含文件夹: {dirs}, 包含文件: {safe_files}")

        return "\n".join(snapshot)

    def _extract_learned_actions(self, domain_content: str) -> list:
        """从PDDL文本中提取所有已存在的action名称"""
        actions = re.findall(r"\(:action\s+([^\s\)]+)", domain_content)
        return actions

    def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[Dict]:
        """调用LLM并重试"""
        for attempt in range(max_retries):
            try:
                response = self.llm.chat(
                    messages=[
                        {"role": "system", "content": "你只输出 JSON 格式的任务定义。"},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={'type': 'json_object'}
                )

                task_data = json.loads(response)
                print(f"\n[Curriculum] 教官出题成功: {task_data['goal']}")
                return task_data
            except Exception as e:
                print(f"[Curriculum] 出题尝试 {attempt+1} 失败: {e}")
                time.sleep(2)

        return None
