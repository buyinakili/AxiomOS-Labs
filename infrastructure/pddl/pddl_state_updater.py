#!/usr/bin/env python3
"""
PDDL 状态更新器

负责解析 pddl_delta 字符串并更新 problem.pddl 文件中的 (:init) 部分。
"""

import re
import os
from typing import List, Tuple, Set
from dataclasses import dataclass


@dataclass
class PDDLDelta:
    """PDDL 增量变更"""
    add_facts: List[str]  # 要添加的事实列表，如 ["(scanned root)", "(at file folder)"]
    del_facts: List[str]  # 要删除的事实列表，如 ["(at file folder)"]
    
    @classmethod
    def parse(cls, delta_str: str) -> "PDDLDelta":
        """
        解析 pddl_delta 字符串
        
        格式示例:
        - "(scanned root)"  # 单个添加
        - "-(at file folder)"  # 单个删除
        - "(is_created archive) (at archive folder)"  # 多个添加
        - "-(at file folder) (scanned root)"  # 混合
        - "(and (not (at file folder)) (at new_file folder) (is_created new_file))"  # and表达式
        
        注意: 事实之间用空格分隔，删除事实以 '-' 开头
        """
        add_facts = []
        del_facts = []
        
        # 处理空字符串
        delta_str = delta_str.strip()
        if not delta_str:
            return cls(add_facts=add_facts, del_facts=del_facts)
        
        # 处理 and 表达式
        if delta_str.startswith('(and ') and delta_str.endswith(')'):
            # 提取 and 内部的内容（去掉 "(and " 和 ")"）
            inner = delta_str[5:-1].strip()
            # and 表达式内部可能包含多个事实，需要分别解析
            # 使用括号计数法分割内部的事实
            inner_facts = []
            i = 0
            while i < len(inner):
                if inner[i] == '(':
                    # 找到匹配的右括号
                    paren_count = 0
                    j = i
                    while j < len(inner):
                        if inner[j] == '(':
                            paren_count += 1
                        elif inner[j] == ')':
                            paren_count -= 1
                            if paren_count == 0:
                                # 找到完整的事实
                                fact = inner[i:j+1]
                                inner_facts.append(fact)
                                i = j  # 移动索引到右括号之后
                                break
                        j += 1
                i += 1
            
            # 分别解析每个内部事实
            for fact_str in inner_facts:
                fact_delta = cls.parse(fact_str)
                add_facts.extend(fact_delta.add_facts)
                del_facts.extend(fact_delta.del_facts)
            
            return cls(add_facts=add_facts, del_facts=del_facts)
        
        # 处理 not 表达式
        if delta_str.startswith('(not ') and delta_str.endswith(')'):
            # 提取 not 内部的内容（去掉 "(not " 和 ")"）
            inner = delta_str[5:-1].strip()
            # not 表达式表示删除事实
            return cls(add_facts=[], del_facts=[inner])
        
        # 使用括号计数法提取所有完整的事实（包括嵌套括号）
        i = 0
        while i < len(delta_str):
            if delta_str[i] == '(':
                # 找到匹配的右括号
                paren_count = 0
                j = i
                while j < len(delta_str):
                    if delta_str[j] == '(':
                        paren_count += 1
                    elif delta_str[j] == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            # 找到完整的事实
                            fact = delta_str[i:j+1]
                            # 检查是否有前导减号（删除标记）
                            # 向前查找减号，忽略空格
                            k = i - 1
                            has_minus = False
                            while k >= 0 and delta_str[k].isspace():
                                k -= 1
                            if k >= 0 and delta_str[k] == '-':
                                has_minus = True
                                # 继续向前查找可能的连续减号
                                while k >= 0 and delta_str[k] == '-':
                                    k -= 1
                            
                            if has_minus:
                                del_facts.append(fact)
                            else:
                                add_facts.append(fact)
                            i = j  # 移动索引到右括号之后
                            break
                    j += 1
            i += 1
        
        # 如果没有找到任何事实，尝试简单分割（向后兼容）
        if not add_facts and not del_facts and delta_str.strip():
            parts = delta_str.strip().split()
            for part in parts:
                if part.startswith('-(') and part.endswith(')'):
                    del_facts.append(part[1:])  # 去掉减号
                elif part.startswith('-') and '(' in part:
                    # 类似 "-(at file folder)" 的格式
                    fact = part[1:].strip()
                    del_facts.append(fact)
                elif part.startswith('(') and part.endswith(')'):
                    add_facts.append(part)
        
        return cls(add_facts=add_facts, del_facts=del_facts)
    
    def is_empty(self) -> bool:
        """检查是否有变更"""
        return not (self.add_facts or self.del_facts)
    
    def __str__(self) -> str:
        parts = []
        for fact in self.del_facts:
            parts.append(f"-{fact}")
        for fact in self.add_facts:
            parts.append(fact)
        return " ".join(parts)


class PDDLStateUpdater:
    """PDDL 状态更新器"""
    
    def __init__(self, problem_path: str):
        """
        初始化
        
        Args:
            problem_path: problem.pddl 文件路径
        """
        self.problem_path = problem_path
    
    def update(self, delta_str: str) -> bool:
        """
        根据 pddl_delta 更新 problem 文件
        
        Args:
            delta_str: pddl_delta 字符串
            
        Returns:
            是否成功
        """
        if not os.path.exists(self.problem_path):
            print(f"[PDDLStateUpdater] 错误: problem 文件不存在: {self.problem_path}")
            return False
        
        # 解析 delta
        delta = PDDLDelta.parse(delta_str)
        if delta.is_empty():
            print("[PDDLStateUpdater] 警告: delta 为空，无需更新")
            return True
        
        print(f"[PDDLStateUpdater] 解析 delta: 添加 {len(delta.add_facts)} 个事实, 删除 {len(delta.del_facts)} 个事实")
        
        # 读取 problem 文件
        with open(self.problem_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用括号计数法定位完整的 (:init ... ) 块
        init_start = content.find('(:init')
        if init_start == -1:
            print("[PDDLStateUpdater] 错误: 未找到 (:init) 部分")
            return False
        
        # 从 init_start 开始扫描，找到匹配的右括号
        paren_count = 0
        in_string = False
        escape = False
        i = init_start
        
        # 跳过 "(:init"
        i += len('(:init')
        
        # 扫描直到找到匹配的右括号
        while i < len(content):
            ch = content[i]
            
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = not in_string
            elif not in_string:
                if ch == '(':
                    paren_count += 1
                elif ch == ')':
                    if paren_count == 0:
                        # 找到匹配的右括号
                        init_end = i  # 这个右括号的位置
                        break
                    paren_count -= 1
            i += 1
        else:
            print("[PDDLStateUpdater] 错误: 未找到匹配的右括号")
            return False
        
        # init_start 到 init_end 包含整个 (:init ... ) 块
        # 我们需要替换的是 (:init 和 ) 之间的内容，不包括两端的括号
        # 找到 (:init 之后的第一个非空格字符
        inner_start = init_start + len('(:init')
        while inner_start < init_end and content[inner_start].isspace():
            inner_start += 1
        
        # 找到 ) 之前的最后一个非空格字符
        inner_end = init_end - 1
        while inner_end > inner_start and content[inner_end].isspace():
            inner_end -= 1
        inner_end += 1  # 包含最后一个字符
        
        # 提取内部内容
        init_content = content[inner_start:inner_end]
        
        # 解析现有事实
        existing_facts = self._parse_init_facts(init_content)
        print(f"[PDDLStateUpdater] 现有事实数量: {len(existing_facts)}")
        
        # 应用变更
        # 删除事实
        for del_fact in delta.del_facts:
            # 标准化事实格式（移除多余空格）
            normalized_del = self._normalize_fact(del_fact)
            existing_facts = [f for f in existing_facts if self._normalize_fact(f) != normalized_del]
        
        # 添加事实
        for add_fact in delta.add_facts:
            normalized_add = self._normalize_fact(add_fact)
            # 检查是否已存在
            if not any(self._normalize_fact(f) == normalized_add for f in existing_facts):
                existing_facts.append(add_fact)
        
        # 生成新的 init 内容
        new_init_content = "\n    " + "\n    ".join(existing_facts) if existing_facts else ""
        
        # 替换原内容（只替换内部内容，保留外层的 (:init 和 )）
        new_content = (
            content[:inner_start] +
            new_init_content +
            content[inner_end:]
        )
        
        # 写回文件
        with open(self.problem_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"[PDDLStateUpdater] 成功更新 problem 文件: {self.problem_path}")
        print(f"  新事实数量: {len(existing_facts)}")
        return True
    
    def _parse_init_facts(self, init_content: str) -> List[str]:
        """
        解析 (:init ... ) 中的事实列表
        
        Args:
            init_content: (:init 和 ) 之间的内容
            
        Returns:
             事实字符串列表
        """
        facts = []
        # 移除注释
        lines = init_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            # 使用括号计数法提取所有完整的事实（包括嵌套括号）
            i = 0
            while i < len(line):
                if line[i] == '(':
                    # 找到匹配的右括号
                    paren_count = 0
                    j = i
                    while j < len(line):
                        if line[j] == '(':
                            paren_count += 1
                        elif line[j] == ')':
                            paren_count -= 1
                            if paren_count == 0:
                                # 找到完整的事实
                                fact = line[i:j+1]
                                facts.append(fact)
                                i = j  # 移动索引到右括号之后
                                break
                        j += 1
                i += 1
        
        return facts
    
    def _normalize_fact(self, fact: str) -> str:
        """
        标准化事实字符串（移除多余空格）
        
        Args:
            fact: 事实字符串，如 "(at file folder)"
            
        Returns:
            标准化后的字符串，如 "(at file folder)"
        """
        # 移除开头和结尾的空格
        fact = fact.strip()
        # 确保括号外无空格
        if fact.startswith('(') and fact.endswith(')'):
            # 移除括号内的多余空格
            inner = fact[1:-1].strip()
            # 将多个空格合并为一个
            inner = ' '.join(inner.split())
            return f"({inner})"
        return fact
    
    def get_current_facts(self) -> List[str]:
        """
        获取当前 (:init) 中的所有事实
        
        Returns:
            事实列表
        """
        if not os.path.exists(self.problem_path):
            return []
        
        with open(self.problem_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用括号计数法定位完整的 (:init ... ) 块
        init_start = content.find('(:init')
        if init_start == -1:
            return []
        
        # 从 init_start 开始扫描，找到匹配的右括号
        paren_count = 0
        in_string = False
        escape = False
        i = init_start
        
        # 跳过 "(:init"
        i += len('(:init')
        
        # 扫描直到找到匹配的右括号
        while i < len(content):
            ch = content[i]
            
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = not in_string
            elif not in_string:
                if ch == '(':
                    paren_count += 1
                elif ch == ')':
                    if paren_count == 0:
                        # 找到匹配的右括号
                        init_end = i  # 这个右括号的位置
                        break
                    paren_count -= 1
            i += 1
        else:
            return []
        
        # 提取内部内容
        inner_start = init_start + len('(:init')
        while inner_start < init_end and content[inner_start].isspace():
            inner_start += 1
        
        inner_end = init_end - 1
        while inner_end > inner_start and content[inner_end].isspace():
            inner_end -= 1
        inner_end += 1
        
        init_content = content[inner_start:inner_end]
        return self._parse_init_facts(init_content)


# 测试函数
def test_pddl_state_updater():
    """测试 PDDL 状态更新器"""
    import tempfile
    import os
    
    # 创建临时 problem 文件
    test_problem = """(define (problem test)
    (:domain file-manager)
    (:objects 
        file1 - file
        root - folder
        backup - folder
    )
    (:init
        (at file1 root)
        (connected root backup)
        (connected backup root)
        (= (total-cost) 0)
    )
    (:goal (at file1 backup))
    (:metric minimize (total-cost))
)"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pddl', delete=False) as f:
        f.write(test_problem)
        temp_path = f.name
    
    try:
        updater = PDDLStateUpdater(temp_path)
        
        # 测试解析
        delta = PDDLDelta.parse("(scanned root) -(at file1 root)")
        print(f"解析 delta: {delta}")
        assert len(delta.add_facts) == 1
        assert len(delta.del_facts) == 1
        assert delta.add_facts[0] == "(scanned root)"
        assert delta.del_facts[0] == "(at file1 root)"
        
        # 测试更新
        success = updater.update("(scanned root) -(at file1 root)")
        assert success
        
        # 检查结果
        facts = updater.get_current_facts()
        print(f"更新后事实: {facts}")
        
        # 验证
        assert "(scanned root)" in facts
        assert "(at file1 root)" not in facts
        assert "(connected root backup)" in facts
        assert "(= (total-cost) 0)" in facts
        
        print("✅ 测试通过")
        
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    test_pddl_state_updater()