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
                    "1. 文件名转义：所有的 '.' 必须替换为 '_dot_'（如 test.txt → test_dot_txt）",
                    "2. 路径连通性：必须在 (:init) 中定义文件夹双向连接（如 (connected root backup) (connected backup root)）",
                    "3. 实体声明：(:objects) 必须包含所有在 init 和 goal 中出现的 file 和 folder，并声明类型",
                    "4. 对象命名规则：",
                    "   - 【完整文件名】：用户明确说了带扩展名的文件（如'移动 test.txt'），可以在 init 中添加 (at test_dot_txt folder)",
                    "   - 【模糊描述】：用户只说了类型或泛指（如'txt文件'、'某个文件'），不能猜测对象名，必须将目标设为 (scanned folder)，且 init 中不能有任何文件对象",
                    "5. 扫描规则：",
                    "   - 如果不知道文件的完整名称，目标必须**仅包含** (scanned folder)，不能包含其他谓词",
                    "   - init 中不能预先设置 (scanned ...) 谓词",
                    "6. 严禁幻觉：严禁在 init 或 goal 中使用已知事实未提到的文件对象",
                    "7. 移动任务：目标必须同时满足：(1) 文件到达目标位置，(2) 文件不在原位置",
                    "8. 创建任务：目标中必须包含文件的目标位置，防止规划器随意选择位置"
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
任务：根据"已知事实"将用户目标转化为 PDDL Problem。

[通用 PDDL 生成原则]:
1. 严禁幻觉：仅能使用"已知事实"中明确提到的对象、位置和状态。
2. 信息缺失处理：如果"已知事实"中没有提到具体信息，你绝对不能猜测，必须将目标设置为获取信息的操作（如 scan）。
3. 成本初始化：必须在 (:init) 中包含 (= (total-cost) 0)。
4. 优化目标：必须在 PDDL 末尾添加 (:metric minimize (total-cost))。
5. 禁用关键字：严禁在 PDDL 中使用 exists、forall 等高级特性。
6. 完成检测：如果"已知事实"已经完全满足了"用户最终目标"，请不要输出 PDDL，直接输出: GOAL_FINISHED_ALREADY

[领域专家规则]:
{rules_str}

[Domain 定义]:
{domain_content}

[当前状态与目标]:
{memory_context}

[输出要求]:
仅输出 PDDL Problem 代码 或 GOAL_FINISHED_ALREADY，不要有任何其他解释。
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