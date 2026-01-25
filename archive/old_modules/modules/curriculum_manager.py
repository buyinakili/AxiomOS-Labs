import os
import json
import time
import re  # 导入正则用于提取技能名

class CurriculumManager:
    def __init__(self, llm_client, domain_path, storage_path="./storage"):
        self.client = llm_client
        self.domain_path = domain_path
        self.storage_path = storage_path

    def _get_env_snapshot(self):
        """扫描 storage 目录，生成环境快照"""
        snapshot = []
        if not os.path.exists(self.storage_path):
            return "当前存储空间 (storage) 为空。"
        
        for root, dirs, files in os.walk(self.storage_path):
            rel_path = os.path.relpath(root, self.storage_path)
            logic_path = "root" if rel_path == "." else rel_path
            safe_files = [f.replace(".", "_dot_") for f in files]
            snapshot.append(f"- 目录 [{logic_path}] 包含文件夹: {dirs}, 包含文件: {safe_files}")
        
        return "\n".join(snapshot)

    def _extract_learned_actions(self, domain_content):
        """从 PDDL 文本中提取所有已存在的 action 名称"""
        actions = re.findall(r"\(:action\s+([^\s\)]+)", domain_content)
        return actions

    def propose_next_task(self, executor):
        """
        分析当前 Domain 和物理环境，提出进化目标
        """
        # 1. 读取当前 PDDL 能力
        if os.path.exists(self.domain_path):
            with open(self.domain_path, 'r', encoding='utf-8') as f:
                domain_content = f.read()
        else:
            domain_content = "未知"

        # 2. 动态提取已学会的技能列表（关键修改点！）
        learned_skills = self._extract_learned_actions(domain_content)

        # 3. 获取环境快照
        env_info = self._get_env_snapshot()
        
        # 4. 获取当前执行器里已有的技能名
        available_skills = executor.get_registered_skills()

        # 修改后的 Prompt，加入了强制排他逻辑
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
        # ... 后续逻辑（调用 LLM、解析 JSON）保持不变 ...
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你只输出 JSON 格式的任务定义。"},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={ 'type': 'json_object' },
                    timeout=30.0
                )
                
                content = response.choices[0].message.content
                task_data = json.loads(content)
                print(f"\n[Curriculum] 教官出题成功: {task_data['goal']}")
                return task_data
            except Exception as e:
                print(f"[Curriculum] 出题尝试 {attempt+1} 失败: {e}")
                time.sleep(2)
        return None