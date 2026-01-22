import os
import json

class PDDLTranslator:
    def __init__(self, llm_client, model_name="deepseek-chat"):
        self.client = llm_client
        self.model_name = model_name
        self.experts = {
            "file_management": {
                "domain_file": "tests/domain.pddl",
                "rules": [
                    "1. 文件名点号转义：所有的 '.' 必须替换为 '_dot_' ",
                    "2. 路径连通性：必须在 (:init) 中定义文件夹双向连接，如 (connected root backup) (connected backup root)。",
                    "3. 实体补全：(:objects) 必须包含所有在目标中出现的 file 和 folder。",
                    "4. 扫描优先：若不知文件确切信息（如位置，名称），目标必须仅包含 (scanned 文件夹)。",
                    "5. 若任务开始时已知文件位置，必须在init中写明"
                    "6. [严禁行为] 严禁在目标中对不存在于 (:init) 中的文件使用 at 谓词，除非该任务是 create_file。",
                    "7.凡是在 (:init) 中出现的所有对象（如 test_file_dot_txt），必须在 (:objects) 中声明其类型。"
                    "8.避免关键字：严禁出现exists"
                    "9.注意：如果用户的目标是‘移动’（move/transfer），你生成的 PDDL Goal 必须同时满足两个条件：1. 文件到达目标位置；2. 文件不再处于原始位置。如果当前事实显示文件在目标位置已存在，但原位置依然存在该文件，这不叫完成，请继续生成 PDDL 调用 remove_file 清理原位置。"
                ]
            },
            "network_operation": {
                "domain_file": "tests/network_domain.pddl",
                "rules": [
                    "未探测的IP不可直接操作，目标应设为(pinged ip)。"
                ]
            }
        }

    def route_task(self, user_goal):
        prompt = f"""
        请判断以下用户指令属于哪个领域。
        指令: "{user_goal}"
        可选领域: {list(self.experts.keys())}
        只需返回领域名称，不要其他文字。
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        choice = response.choices[0].message.content.strip().lower()
        return choice if choice in self.experts else "file_management"

    def generate_problem(self, memory_context, domain_choice, override_domain_path=None):
        expert = self.experts[domain_choice]
        target_domain_file = override_domain_path if override_domain_path else expert["domain_file"]
        
        if not os.path.exists(target_domain_file):
             # 回退保护
             target_domain_file = expert["domain_file"]

        with open(target_domain_file, "r") as f:
            domain_content = f.read()
            
        rules_str = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(expert['rules'])])
        prompt = f"""
你现在是 AIOS 的 [{domain_choice}] 逻辑专家。
任务：根据“已知事实”将用户目标转化为 PDDL Problem。

[核心原则 - 严禁幻觉]:
1. 仅能使用“已知事实”中明确提到的对象、位置和状态。
2. 如果“已知事实”中没有提到具体信息，你绝对不能猜测信息，优先将目标设置为获取信息的操作。
3. 必须在 (:init) 中包含 (= (total-cost) 0)。
4. 必须在 PDDL 末尾添加 (:metric minimize (total-cost)) 以追求最优路径。
5. 如果内存事实为空，请根据指令内容提取可能存在的初始状态,但不要违反原则2。
6.避免关键字：严禁出现exists
例如用户说“移动floder的 A”，你可以合理推断初始状态为 (at A floder)。


[特殊指令]:
如果“已知事实”已经完全满足了“用户最终目标”，请不要输出 PDDL，只需直接输出字符串: GOAL_FINISHED_ALREADY

[领域逻辑规则]:
{rules_str}

[Domain 定义]:
{domain_content}

[上下文事实与目标]:
{memory_context}

[输出要求]:
 仅输出 PDDL 代码 或 GOAL_FINISHED_ALREADY。
"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        pddl_code = response.choices[0].message.content
        if "```" in pddl_code:
            pddl_code = pddl_code.split("```")[1]
            if pddl_code.startswith("pddl") or pddl_code.startswith("lisp"):
                pddl_code = pddl_code.split("\n", 1)[1]
        print("\n" + "="*30 )
        print(memory_context)
        print(pddl_code)
        print("="*80 + "\n")
        return pddl_code.strip()

    def save_pddl(self, pddl_content, file_path):
        with open(file_path, "w") as f:
            f.write(pddl_content)