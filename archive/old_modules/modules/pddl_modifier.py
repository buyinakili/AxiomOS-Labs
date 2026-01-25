import re
import os

class PDDLModifier:
    @staticmethod
    def add_action_to_domain(domain_path, action_pddl):
        """
        将 LLM 生成的 PDDL Action 片段插入到 domain 文件的最后一个右括号之前
        """
        if not os.path.exists(domain_path):
            print(f"[Error] 找不到 Domain 文件: {domain_path}")
            return False

        with open(domain_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # 算法逻辑：
        # 1. 检查 action 是否已经存在（防止重复注入）
        action_name_match = re.search(r":action\s+([^\s\n\(]+)", action_pddl)
        if action_name_match:
            action_name = action_name_match.group(1)
            if f":action {action_name}" in content:
                print(f"[Modifier] Action '{action_name}' 已存在，跳过注入。")
                return True

        # 2. 寻找最后一个闭合括号
        # PDDL 文件结构是 (define (domain ...) ... )
        last_bracket_index = content.rfind(')')
        if last_bracket_index == -1:
            return False
        
        if action_pddl.count('(') != action_pddl.count(')'):
            print("[Error] LLM 生成的 PDDL 片段括号不匹配！")
            return False

        # 3. 拼接内容
        new_content = (
            content[:last_bracket_index] + 
            "\n  ;; --- AI Generated Action ---\n" + 
            action_pddl + 
            "\n)"
        )

        with open(domain_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"[Modifier] 成功将新 Action 注入到: {domain_path}")
        return True