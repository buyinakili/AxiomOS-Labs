"""粒度转换器实现 - Brain/Nerves环境事实转换

实现Brain/Nerves双层规划系统的环境事实粒度转换。
"""
from typing import Set, List, Dict, Optional
from abc import ABC, abstractmethod
import re


class IGranularityTranslator(ABC):
    """粒度转换器接口"""
    
    @abstractmethod
    def translate(self, facts: Set[str], context: Optional[Dict] = None) -> Set[str]:
        """
        转换环境事实
        
        :param facts: 输入的事实集合
        :param context: 可选上下文信息
        :return: 转换后的事实集合
        """
        pass


class Nerves2BrainTranslator(IGranularityTranslator):
    """Nerves到Brain转换器：物理事实 → 逻辑谓词
    
    功能：
    1. 粒度转换（降采样）- 将详细物理事实转换为高层逻辑谓词
    2. 异常语义升级 - 将错误信息转换为逻辑谓词
    3. 聚类抽象 - 将多个相关事实聚合成一个高层事实
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化转换器
        
        :param config: 配置字典，可包含转换规则等
        """
        self.config = config or {}
        self._init_rules()
    
    def _init_rules(self):
        """初始化转换规则"""
        # 基础谓词映射：Nerves谓词 -> Brain谓词
        self.predicate_rules = {
            # 文件位置相关
            "(at ?f ?d)": "(located ?f ?d)",  # 简化表示
            # 不再映射connected谓词，因为它已被删除
            
            # 状态相关
            "(scanned ?d)": "(known ?d)",
            "(is_created ?obj)": "(exists ?obj)",
            "(is_compressed ?f ?a)": "(compressed ?f)",
            
            # 权限相关
            "(has_admin_rights)": "(has_permission)",
            
            # 文件属性相关
            "(has_name ?f ?n)": "(named ?f ?n)",
            "(is_empty ?d)": "(empty ?d)",
            "(is_copied ?src ?dst)": "(copied ?src ?dst)",
        }
        
        # 复杂规则：基于多个事实的转换
        self.complex_rules = [
            # 规则1：多个文件在同一文件夹 -> 文件夹包含文件
            {
                "pattern": [r"\(at (\w+) (\w+)\)", r"\(at (\w+) (\w+)\)"],
                "condition": lambda matches: matches[0][1] == matches[1][1],  # 相同文件夹
                "output": "(contains {folder} {file1} {file2})",
                "extract": lambda matches: {
                    "folder": matches[0][1],
                    "file1": matches[0][0],
                    "file2": matches[1][0]
                }
            },
            # 规则2：文件大小超过阈值 -> is_large
            {
                "pattern": [r"\(size_greater_than (\w+) (\d+)\)"],
                "condition": lambda matches: int(matches[0][1]) > 1024,  # 大于1GB
                "output": "(is_large {file})",
                "extract": lambda matches: {"file": matches[0][0]}
            }
        ]
        
        # 错误语义升级规则
        self.error_rules = {
            "error_access_denied": "(not (has_permission ?user ?obj))",
            "error_file_not_found": "(not (exists ?obj))",
            "error_insufficient_space": "(not (has_space ?location))",
        }
    
    def translate(self, facts: Set[str], context: Optional[Dict] = None) -> Set[str]:
        """
        将Nerves层物理事实转换为Brain层逻辑谓词
        
        :param facts: Nerves层事实集合
        :param context: 可选上下文信息（如错误信息、文件属性等）
        :return: Brain层事实集合
        """
        brain_facts = set()
        
        # 1. 基础谓词转换
        for fact in facts:
            converted = self._translate_simple_fact(fact)
            if converted:
                brain_facts.add(converted)
        
        # 2. 复杂规则转换
        complex_converted = self._apply_complex_rules(facts)
        brain_facts.update(complex_converted)
        
        # 3. 错误语义升级（如果有上下文）
        if context and "errors" in context:
            error_converted = self._translate_errors(context["errors"])
            brain_facts.update(error_converted)
        
        # 4. 聚类抽象
        clustered = self._cluster_facts(brain_facts)
        
        return clustered
    
    def _translate_simple_fact(self, fact: str) -> Optional[str]:
        """转换简单谓词事实"""
        # 标准化事实格式（移除多余空格）
        fact = re.sub(r'\s+', ' ', fact.strip())
        
        # 简单字符串匹配和替换
        if fact == "(has_admin_rights)":
            return "(has_permission)"
        elif fact.startswith("(at "):
            # 尝试转换为 (located ...)
            match = re.match(r'\(at (\w+) (\w+)\)', fact)
            if match:
                file_name, folder_name = match.groups()
                return f"(located {file_name} {folder_name})"
        # 不再处理connected谓词，因为它已被删除
        elif fact.startswith("(scanned "):
            match = re.match(r'\(scanned (\w+)\)', fact)
            if match:
                folder = match.group(1)
                return f"(known {folder})"
        elif fact.startswith("(is_created "):
            match = re.match(r'\(is_created (\w+)\)', fact)
            if match:
                obj = match.group(1)
                return f"(exists {obj})"
        elif fact.startswith("(is_compressed "):
            match = re.match(r'\(is_compressed (\w+) (\w+)\)', fact)
            if match:
                file_name, archive_name = match.groups()
                return f"(compressed {file_name})"
        elif fact.startswith("(has_name "):
            match = re.match(r'\(has_name (\w+) (\w+)\)', fact)
            if match:
                file_name, name = match.groups()
                return f"(named {file_name} {name})"
        elif fact.startswith("(is_empty "):
            match = re.match(r'\(is_empty (\w+)\)', fact)
            if match:
                folder = match.group(1)
                return f"(empty {folder})"
        elif fact.startswith("(is_copied "):
            match = re.match(r'\(is_copied (\w+) (\w+)\)', fact)
            if match:
                src, dst = match.groups()
                return f"(copied {src} {dst})"
        
        # 如果没有匹配规则，返回原事实
        return fact
    
    def _downsample_fact(self, fact: str) -> str:
        """降采样事实 - 简化详细事实"""
        # 移除过于详细的参数
        if fact.startswith("(at "):
            # 保持原样，但可以简化
            return fact
        elif fact.startswith("(has_name "):
            # 名称信息可能对Brain层不重要，可以忽略
            return ""
        
        return fact
    
    def _apply_complex_rules(self, facts: Set[str]) -> Set[str]:
        """应用复杂转换规则"""
        converted = set()
        fact_list = list(facts)
        
        for rule in self.complex_rules:
            # 简化实现：只处理第一个规则
            break
        
        return converted
    
    def _translate_errors(self, errors: List[str]) -> Set[str]:
        """转换错误信息为逻辑谓词"""
        error_facts = set()
        
        for error in errors:
            if error in self.error_rules:
                error_facts.add(self.error_rules[error])
        
        return error_facts
    
    def _cluster_facts(self, facts: Set[str]) -> Set[str]:
        """聚类相关事实"""
        # 简单实现：按谓词类型分组
        clustered = set()
        
        # 按谓词首单词分组
        groups = {}
        for fact in facts:
            if not fact:
                continue
            match = re.match(r'\((\w+)', fact)
            if match:
                predicate = match.group(1)
                if predicate not in groups:
                    groups[predicate] = []
                groups[predicate].append(fact)
        
        # 对于某些谓词，可以合并
        for predicate, fact_list in groups.items():
            if predicate == "at" and len(fact_list) > 3:
                # 太多at事实，合并为一个contains
                folders = set()
                for fact in fact_list:
                    match = re.match(r'\(at (\w+) (\w+)\)', fact)
                    if match:
                        folders.add(match.group(2))
                for folder in folders:
                    clustered.add(f"(contains {folder} multiple_files)")
            else:
                clustered.update(fact_list)
        
        return clustered


class Brain2NervesTranslator(IGranularityTranslator):
    """Brain到Nerves转换器：逻辑谓词 → 物理事实
    
    功能：
    1. 具身化转换 - 将抽象逻辑谓词具体化为物理事实
    2. 对象实例化 - 将逻辑对象映射到具体物理对象
    3. 参数具体化 - 将抽象参数填充为具体值
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化转换器
        
        :param config: 配置字典，可包含对象映射等
        """
        self.config = config or {}
        self._init_rules()
    
    def _init_rules(self):
        """初始化转换规则"""
        # 反向映射：Brain谓词 -> Nerves谓词
        self.reverse_rules = {
            "(located ?f ?d)": "(at ?f ?d)",
            # 不再映射accessible谓词，因为connected谓词已被删除
            "(known ?d)": "(scanned ?d)",
            "(exists ?obj)": "(is_created ?obj)",
            "(compressed ?f)": "(is_compressed ?f ?a)",  # 需要生成archive对象
            "(has_permission)": "(has_admin_rights)",
            "(named ?f ?n)": "(has_name ?f ?n)",
            "(empty ?d)": "(is_empty ?d)",
            "(copied ?src ?dst)": "(is_copied ?src ?dst)",
        }
        
        # 对象实例化规则
        self.object_instantiation = {
            "?a": "archive_{timestamp}",  # 示例：生成唯一archive名称
        }
        
        # 参数具体化规则
        self.parameter_concretization = {
            "?location": "root",  # 默认位置
            "?user": "admin",     # 默认用户
        }
    
    def translate(self, facts: Set[str], context: Optional[Dict] = None) -> Set[str]:
        """
        将Brain层逻辑谓词转换为Nerves层物理事实
        
        :param facts: Brain层事实集合
        :param context: 可选上下文信息（如具体对象映射、参数值等）
        :return: Nerves层事实集合
        """
        nerves_facts = set()
        
        # 合并上下文配置
        config = self.config.copy()
        if context:
            config.update(context)
        
        for fact in facts:
            converted = self._translate_fact(fact, config)
            if converted:
                nerves_facts.update(converted)
        
        return nerves_facts
    
    def _translate_fact(self, fact: str, config: Dict) -> List[str]:
        """转换单个事实"""
        # 标准化事实格式
        fact = re.sub(r'\s+', ' ', fact.strip())
        
        # 简单字符串匹配和替换
        if fact == "(has_permission)":
            return ["(has_admin_rights)"]
        elif fact.startswith("(located "):
            match = re.match(r'\(located (\w+) (\w+)\)', fact)
            if match:
                file_name, folder_name = match.groups()
                return [f"(at {file_name} {folder_name})"]
        # 不再处理accessible谓词，因为connected谓词已被删除
        elif fact.startswith("(known "):
            match = re.match(r'\(known (\w+)\)', fact)
            if match:
                folder = match.group(1)
                return [f"(scanned {folder})"]
        elif fact.startswith("(exists "):
            match = re.match(r'\(exists (\w+)\)', fact)
            if match:
                obj = match.group(1)
                return [f"(is_created {obj})"]
        elif fact.startswith("(compressed "):
            match = re.match(r'\(compressed (\w+)\)', fact)
            if match:
                file_name = match.group(1)
                archive_name = config.get("archive_name", "archive_1")
                return [f"(is_compressed {file_name} {archive_name})"]
        elif fact.startswith("(named "):
            match = re.match(r'\(named (\w+) (\w+)\)', fact)
            if match:
                file_name, name = match.groups()
                return [f"(has_name {file_name} {name})"]
        elif fact.startswith("(empty "):
            match = re.match(r'\(empty (\w+)\)', fact)
            if match:
                folder = match.group(1)
                return [f"(is_empty {folder})"]
        elif fact.startswith("(copied "):
            match = re.match(r'\(copied (\w+) (\w+)\)', fact)
            if match:
                src, dst = match.groups()
                return [f"(is_copied {src} {dst})"]
        elif fact.startswith("(is_large "):
            match = re.match(r'\(is_large (\w+)\)', fact)
            if match:
                file_name = match.group(1)
                return [f"(size_greater_than {file_name} 1025)"]
        elif fact.startswith("(contains "):
            match = re.match(r'\(contains (\w+) (.*)\)', fact)
            if match:
                folder = match.group(1)
                files_str = match.group(2)
                files = files_str.split()
                if "multiple_files" in files:
                    return []
                else:
                    return [f"(at {file} {folder})" for file in files]
        
        # 默认返回原事实（假设已经是Nerves层事实）
        return [fact]


# 工厂函数
def create_nerves2brain_translator(config: Optional[Dict] = None) -> Nerves2BrainTranslator:
    """创建Nerves到Brain转换器"""
    return Nerves2BrainTranslator(config)


def create_brain2nerves_translator(config: Optional[Dict] = None) -> Brain2NervesTranslator:
    """创建Brain到Nerves转换器"""
    return Brain2NervesTranslator(config)


# 测试函数
if __name__ == "__main__":
    # 测试Nerves2Brain转换
    nerves_facts = {
        "(at file1 root)",
        "(at file2 root)",
        "(connected root backup)",
        "(has_admin_rights)",
        "(scanned root)",
    }
    
    translator = Nerves2BrainTranslator()
    brain_facts = translator.translate(nerves_facts)
    
    print("Nerves2Brain转换测试:")
    print("输入:", nerves_facts)
    print("输出:", brain_facts)
    
    # 测试Brain2Nerves转换
    brain_facts = {
        "(located file1 root)",
        "(accessible root backup)",
        "(has_permission)",
    }
    
    translator = Brain2NervesTranslator()
    nerves_facts = translator.translate(brain_facts)
    
    print("\nBrain2Nerves转换测试:")
    print("输入:", brain_facts)
    print("输出:", nerves_facts)