"""NervesLLM实现 - 原子动作分解"""
from typing import List, Set, Optional, Dict, Any
import re
from interface.llm import ILLM
from interface.nerves_llm import INervesLLM


class NervesLLM(INervesLLM):
    """NervesLLM实现 - 将单个任务分解为原子动作链"""

    def __init__(
        self,
        llm: ILLM,
        domain_actions: Dict[str, List[str]],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化NervesLLM

        :param llm: 基础LLM客户端
        :param domain_actions: 领域动作映射 {domain_name: [action1, action2, ...]}
        :param config: 配置字典
        """
        self.llm = llm
        self.domain_actions = domain_actions
        self.config = config or {}
        
        # 默认配置
        self.default_temperature = self.config.get("temperature", 0.1)
        self.max_retries = self.config.get("max_retries", 3)
        self.debug = self.config.get("debug", False)
        
        # 对象提取模式
        self.object_patterns = {
            "file_management": {
                "file": r'\b(file\d+|file_\w+|\w+\.txt|\w+\.pdf)\b',
                "folder": r'\b(root|backup|folder\d+|home|documents)\b',
                "archive": r'\b(archive\d+|archive_\w+|compressed\.zip)\b',
                "filename": r'\b(name\d+|\w+\.\w+)\b',
            }
        }

    def extract_objects_from_facts(self, facts: Set[str], domain: str) -> Set[str]:
        """
        从环境事实中提取对象列表

        :param facts: 环境事实集合
        :param domain: 领域名称
        :return: 对象名称集合
        """
        objects = set()
        
        # 简单实现：从事实中提取所有单词（排除谓词和括号）
        for fact in facts:
            # 移除括号和谓词
            content = fact.strip("()")
            parts = content.split()
            if len(parts) > 1:
                # 第一个部分是谓词，其余部分是参数（可能是对象）
                for obj in parts[1:]:
                    # 清理对象名称
                    obj_clean = obj.strip("?")
                    if obj_clean and not obj_clean.startswith("("):
                        objects.add(obj_clean)
        
        return objects

    def decompose_action(
        self,
        task: str,
        current_facts: Set[str],
        domain: str,
        previous_failure_reason: Optional[str] = None
    ) -> List[str]:
        """
        将单个任务分解为PDDL格式的原子动作链

        :param task: PDDL格式任务
        :param current_facts: 当前环境事实集合
        :param domain: 领域名称
        :param previous_failure_reason: 上一次失败的原因
        :return: PDDL格式原子动作链列表
        """
        # 获取领域特定的可用动作
        available_actions = self.domain_actions.get(domain, [])
        if not available_actions:
            raise ValueError(f"领域 '{domain}' 没有可用的动作")
        
        # 提取任务中的对象
        task_objects = self._extract_objects_from_task(task)
        
        # 从环境事实中提取对象
        env_objects = self.extract_objects_from_facts(current_facts, domain)
        
        # 所有可用对象
        all_objects = task_objects.union(env_objects)
        
        # 构建提示词
        prompt = self._build_prompt(
            task, current_facts, available_actions, all_objects, domain, previous_failure_reason
        )
        
        if self.debug:
            print(f"[NervesLLM Debug] 提示词:\n{prompt}")
        
        # 调用LLM
        messages = [{"role": "user", "content": prompt}]
        
        for retry in range(self.max_retries):
            try:
                response = self.llm.chat(
                    messages=messages,
                    temperature=self.default_temperature
                )
                
                # 解析响应
                chain_of_action = self._parse_response(response)
                
                # 验证动作链
                if self._validate_chain(chain_of_action, available_actions, all_objects):
                    return chain_of_action
                else:
                    # 验证失败，准备重试
                    if retry < self.max_retries - 1:
                        failure_reason = "动作链包含不可用动作、未知对象或格式错误"
                        prompt = self._build_prompt(
                            task, current_facts, available_actions, all_objects, 
                            domain, failure_reason
                        )
                        messages = [{"role": "user", "content": prompt}]
                        continue
                    
            except Exception as e:
                if retry < self.max_retries - 1:
                    if self.debug:
                        print(f"[NervesLLM Debug] 第{retry+1}次尝试失败: {e}")
                    continue
                else:
                    raise
        
        # 所有重试都失败
        raise ValueError(f"无法在{self.max_retries}次尝试内生成有效的动作链")

    def _extract_objects_from_task(self, task: str) -> Set[str]:
        """从任务中提取对象"""
        objects = set()
        
        # 移除括号
        content = task.strip("()")
        parts = content.split()
        
        if len(parts) > 1:
            # 第一个部分是动作名称，其余部分是参数
            for obj in parts[1:]:
                # 清理对象名称
                obj_clean = obj.strip("?")
                if obj_clean and not obj_clean.startswith("("):
                    objects.add(obj_clean)
        
        return objects

    def _build_prompt(
        self,
        task: str,
        current_facts: Set[str],
        available_actions: List[str],
        available_objects: Set[str],
        domain: str,
        failure_reason: Optional[str] = None
    ) -> str:
        """构建LLM提示词"""
        prompt_lines = [
            "你是一个动作规划器。给定以下任务和环境事实，请将其分解为PDDL格式的原子动作序列。",
            "",
            f"任务: {task}",
            f"领域: {domain}",
            "",
            "当前环境事实:"
        ]
        
        # 添加环境事实（每行一个）
        for fact in sorted(current_facts):
            prompt_lines.append(f"  {fact}")
        
        prompt_lines.extend([
            "",
            "可用对象（只能使用这些对象）:"
        ])
        
        # 添加可用对象
        for obj in sorted(available_objects):
            prompt_lines.append(f"  {obj}")
        
        prompt_lines.extend([
            "",
            "可用动作（只能使用这些动作）:"
        ])
        
        # 添加可用动作
        for action in available_actions:
            prompt_lines.append(f"  {action}")
        
        prompt_lines.extend([
            "",
            "要求:",
            "1. 只能使用上述可用动作和对象",
            "2. 每个动作必须是PDDL格式（如 '(get_admin)' 或 '(scan root)'）",
            "3. 考虑动作的前置条件（如执行scan需要has_admin_rights）",
            "4. 输出格式：每个动作一行，不要编号，不要额外文字",
            "5. 确保动作序列能完成给定任务",
            "6. 动作序列应该是最小且有效的",
            ""
        ])
        
        if failure_reason:
            prompt_lines.extend([
                f"注意：上一次规划失败，原因: {failure_reason}",
                "请根据这个反馈修正你的规划。",
                ""
            ])
        
        prompt_lines.append("原子动作序列:")
        
        return "\n".join(prompt_lines)

    def _parse_response(self, response: str) -> List[str]:
        """解析LLM响应，提取动作链"""
        actions = []
        
        # 按行分割，清理空白
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 提取PDDL格式的动作
            match = re.match(r'^\s*\(([^)]+)\)\s*$', line)
            if match:
                action_content = match.group(1)
                actions.append(f"({action_content})")
            else:
                # 尝试直接匹配括号格式
                if line.startswith('(') and line.endswith(')'):
                    actions.append(line)
        
        return actions

    def _validate_chain(
        self, 
        chain: List[str], 
        available_actions: List[str],
        available_objects: Set[str]
    ) -> bool:
        """验证动作链是否有效"""
        if not chain:
            return False
        
        # 提取动作名称（第一个单词）
        action_pattern = re.compile(r'^\s*\((\w+)')
        
        for action in chain:
            match = action_pattern.match(action)
            if not match:
                return False
            
            action_name = match.group(1)
            
            # 检查动作是否在可用动作列表中
            action_found = False
            for available_action in available_actions:
                if available_action.startswith(f"({action_name}"):
                    action_found = True
                    break
            
            if not action_found:
                return False
            
            # 检查动作中的对象是否在可用对象中
            # 提取动作中的所有单词（排除动作名称）
            content = action.strip("()")
            parts = content.split()
            if len(parts) > 1:
                for obj in parts[1:]:
                    obj_clean = obj.strip("?")
                    # 跳过变量（以?开头）和特殊标记
                    if obj_clean and not obj_clean.startswith("?") and obj_clean not in available_objects:
                        # 允许数字和常见值
                        if not (obj_clean.isdigit() or obj_clean in ["true", "false", "null"]):
                            return False
        
        return True


# 工厂函数
def create_nerves_llm(
    llm: ILLM,
    domain_actions: Optional[Dict[str, List[str]]] = None,
    config: Optional[Dict[str, Any]] = None
) -> NervesLLM:
    """创建NervesLLM实例"""
    if domain_actions is None:
        # 默认领域动作（文件管理）
        domain_actions = {
            "file_management": [
                "(get_admin)",
                "(scan ?d)",
                "(move ?f ?src ?dst)",
                "(remove ?f ?d)",
                "(rename ?f ?old_name ?new_name ?d)",
                "(copy ?src ?dst ?src_folder ?dst_folder)",
                "(compress ?f ?d ?a)",
                "(uncompress ?a ?d ?f)",
                "(create_file ?f ?name ?d)",
                "(create_folder ?d ?parent)",
                "(connect_folders ?d1 ?d2)",
            ]
        }
    
    return NervesLLM(llm, domain_actions, config)