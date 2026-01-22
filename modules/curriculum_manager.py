# modules/curriculum_manager.py
import os
import json
import time

class CurriculumManager:
    def __init__(self, llm_client, domain_path, storage_path="./storage"):
        self.client = llm_client
        self.domain_path = domain_path
        self.storage_path = storage_path

    def _get_env_snapshot(self):
        """扫描 storage 目录，生成环境快照，防止 LLM 凭空臆造路径"""
        snapshot = []
        if not os.path.exists(self.storage_path):
            return "当前存储空间 (storage) 为空。"
        
        # 遍历基础存储目录
        for root, dirs, files in os.walk(self.storage_path):
            # 获取相对于 storage 的路径名
            rel_path = os.path.relpath(root, self.storage_path)
            # 在 PDDL 逻辑中，根目录通常叫 root
            logic_path = "root" if rel_path == "." else rel_path
            
            # 清理一下文件名（转义点号）
            safe_files = [f.replace(".", "_dot_") for f in files]
            snapshot.append(f"- 目录 [{logic_path}] 包含文件夹: {dirs}, 包含文件: {safe_files}")
        
        return "\n".join(snapshot)

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

        # 2. 获取环境快照
        env_info = self._get_env_snapshot()
        
        # 3. 获取当前执行器里已有的技能名
        available_skills = executor.get_registered_skills()

        prompt = f"""
你现在是 AIOS 的【首席训练教官】。

【当前沙盒物理环境 (World State)】:
这些是目前存储空间中真实存在的路径和文件：
{env_info}

【当前系统能力 (PDDL Domain)】:
{domain_content}

【可用预设动作 (Setup Actions)】:
你可以使用以下技能来准备测试环境: {available_skills}

【你的任务】:
提出一个具有挑战性的、目前系统无法完成的文件系统任务。

【要求】:
1. 必须基于【物理环境】中存在的目录（如 root）出题。
2. 任务目标必须是当前 Domain 中没有对应 Action 的。
3. 如果任务需要特定文件，请在 setup_actions 中先创建它。
4. 所有的文件名点号必须转义，如 'a.txt' 写作 'a_dot_txt'。
5. 【解耦原则】：setup_actions 仅允许使用 create_file 或 create_folder 来初始化文件实体。
6. 【禁止预设感知】：严禁在 setup_actions 中加入 'scan' 动作。AI 必须在任务开始后自己学会先 scan 才能发现文件。
7. 【禁止预设权限】：严禁在 setup_actions 中加入 'get_admin'。如果任务需要权限，AI 必须学会在 PDDL 规划中自行调用 get_admin。

【输出 JSON 格式】:
{{
    "task_name": "任务简称",
    "goal": "自然语言指令 (例如: 请把 root 下的 a.txt 重命名为 b.txt)",
    "rationale": "理由",
    "setup_actions": [
        ["create_file", "a_dot_txt", "root"]
    ]
}}
"""

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