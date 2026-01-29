"""PDDL修改器实现"""
import re
import os
from typing import Optional
from interface.pddl_modifier import IPDDLModifier
from config.settings import Settings


class PDDLModifier(IPDDLModifier):
    """PDDL修改器实现"""
    
    def __init__(self, config: Optional[Settings] = None):
        """
        初始化PDDL修改器
        
        :param config: 系统配置，如果为None则使用默认配置
        """
        self.config = config or Settings.load_from_env()

    def add_action(self, domain_path: str, action_pddl: str) -> bool:
        """
        将LLM生成的PDDL Action片段插入到domain文件的最后一个右括号之前

        :param domain_path: Domain文件路径
        :param action_pddl: 要添加的Action PDDL代码
        :return: 是否成功
        """
        if not os.path.exists(domain_path):
            print(f"[Error] 找不到 Domain 文件: {domain_path}")
            return False

        with open(domain_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # 1. 检查action是否已经存在
        action_name_match = re.search(r":action\s+([^\s\n\(]+)", action_pddl)
        if action_name_match:
            action_name = action_name_match.group(1)
            if f":action {action_name}" in content:
                print(f"[Modifier] Action '{action_name}' 已存在，跳过注入。")
                return True

        # 2. 确保action_pddl括号匹配
        if action_pddl.count('(') != action_pddl.count(')'):
            print("[Error] LLM 生成的 PDDL 片段括号不匹配！")
            return False

        # 3. 在domain的最后闭合括号之前插入新动作
        # 找到最后一个闭合括号的位置
        last_bracket_index = content.rfind(')')
        if last_bracket_index == -1:
            return False

        # 在最后一个括号之前插入，保留原来的闭合括号
        new_content = (
            content[:last_bracket_index] +
            f"\n{self.config.pddl_ai_generated_comment}\n" +
            action_pddl + "\n" +
            content[last_bracket_index:]  # 保留原来的闭合括号
        )

        with open(domain_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"[Modifier] 成功将新 Action 注入到: {domain_path}")
        return True

    def remove_action(self, domain_path: str, action_name: str) -> bool:
        """
        从Domain文件中删除指定的Action

        :param domain_path: Domain文件路径
        :param action_name: 要删除的Action名称
        :return: 是否成功
        """
        if not os.path.exists(domain_path):
            print(f"[Error] 找不到 Domain 文件: {domain_path}")
            return False

        with open(domain_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用正则表达式匹配整个action块
        # 匹配 (:action action_name ... ) 整个块
        pattern = r'\(:action\s+' + re.escape(action_name) + r'\s+[^)]*(?:\([^)]*\)[^)]*)*\)'

        # 查找匹配
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            print(f"[Modifier] 未找到 Action: {action_name}")
            return False

        # 删除匹配的内容
        new_content = content[:match.start()] + content[match.end():]

        # 清理多余的空行
        new_content = re.sub(r'\n\s*\n', '\n\n', new_content)

        with open(domain_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"[Modifier] 成功删除 Action: {action_name}")
        return True

    def action_exists(self, domain_path: str, action_name: str) -> bool:
        """
        检查Action是否已存在

        :param domain_path: Domain文件路径
        :param action_name: Action名称
        :return: 是否存在
        """
        if not os.path.exists(domain_path):
            return False

        with open(domain_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return f":action {action_name}" in content
