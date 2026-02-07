"""BrainLLM实现 - 高层任务分解"""
from typing import List, Set, Optional, Dict, Any
import re
from interface.llm import ILLM
from interface.brain_llm import IBrainLLM


class BrainLLM(IBrainLLM):
    """BrainLLM实现 - 将用户任务分解为高层任务链"""

    def __init__(
        self,
        llm: ILLM,
        domain_actions: Dict[str, List[str]],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化BrainLLM

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

    def get_available_actions(self, domain: str) -> List[str]:
        """
        获取指定领域可用的动作列表

        :param domain: 领域名称
        :return: 可用动作列表
        """
        return self.domain_actions.get(domain, [])

    def decompose_task(
        self,
        user_goal: str,
        current_facts: Set[str],
        available_actions: List[str],
        previous_failure_reason: Optional[str] = None
    ) -> List[str]:
        """
        将用户任务分解为PDDL格式的任务链

        :param user_goal: 用户目标描述
        :param current_facts: 当前环境事实集合
        :param available_actions: 可用动作列表（PDDL格式）
        :param previous_failure_reason: 上一次失败的原因（用于重试）
        :return: PDDL格式任务链列表
        """
        # 构建提示词
        prompt = self._build_prompt(
            user_goal, current_facts, available_actions, previous_failure_reason
        )
        
        if self.debug:
            print(f"[BrainLLM Debug] 提示词:\n{prompt}")
        
        # 调用LLM
        messages = [{"role": "user", "content": prompt}]
        
        for retry in range(self.max_retries):
            try:
                response = self.llm.chat(
                    messages=messages,
                    temperature=self.default_temperature
                )
                
                # 解析响应
                chain_of_mission = self._parse_response(response)
                
                # 验证任务链
                if self._validate_chain(chain_of_mission, available_actions):
                    return chain_of_mission
                else:
                    # 验证失败，准备重试
                    if retry < self.max_retries - 1:
                        failure_reason = "任务链包含不可用动作或格式错误"
                        prompt = self._build_prompt(
                            user_goal, current_facts, available_actions, failure_reason
                        )
                        messages = [{"role": "user", "content": prompt}]
                        continue
                    
            except Exception as e:
                if retry < self.max_retries - 1:
                    if self.debug:
                        print(f"[BrainLLM Debug] 第{retry+1}次尝试失败: {e}")
                    continue
                else:
                    raise
        
        # 所有重试都失败
        raise ValueError(f"无法在{self.max_retries}次尝试内生成有效的任务链")

    def _build_prompt(
        self,
        user_goal: str,
        current_facts: Set[str],
        available_actions: List[str],
        failure_reason: Optional[str] = None
    ) -> str:
        """构建改进的LLM提示词"""
        # 从环境事实中提取可用对象
        available_objects = self._extract_objects_from_facts(current_facts)
        
        prompt_lines = [
            "你是一个任务规划器。给定以下任务和环境事实，请将其分解为PDDL格式的任务序列。",
            "",
            f"任务: \"{user_goal}\"",
            "",
            "当前环境事实:"
        ]
        
        # 添加环境事实（每行一个）
        for fact in sorted(current_facts):
            prompt_lines.append(f"  {fact}")
        
        prompt_lines.extend([
            "",
            "可用对象（从环境事实中提取）:"
        ])
        
        # 添加可用对象
        for obj_type, obj_list in available_objects.items():
            if obj_list:
                prompt_lines.append(f"  {obj_type}: {', '.join(obj_list)}")
        
        prompt_lines.extend([
            "",
            "可用动作模板（?表示参数占位符，需要替换为具体对象）:"
        ])
        
        # 添加可用动作模板
        for action in available_actions:
            prompt_lines.append(f"  {action}")
        
        prompt_lines.extend([
            "",
            "动作参数说明:",
            "  ?d, ?src, ?dst: 文件夹对象（如 root, workspace）",
            "  ?f, ?src, ?dst: 文件对象（如 file1, file2）",
            "  ?a: 归档文件对象",
            "  ?name, ?old_name, ?new_name: 文件名",
            "  ?parent: 父文件夹",
            "",
            "要求:",
            "1. 只能使用上述动作模板，但需要将参数占位符替换为具体的可用对象",
            "2. 每个任务必须是完整的PDDL格式（如 '(scan root)' 或 '(move file1 root workspace)'）",
            "3. 考虑动作的前置条件（如 scan 需要 has_admin_rights）",
            "4. 输出格式：每个任务一行，不要编号，不要额外文字",
            "5. 确保任务序列能实现用户目标",
            "6. 优先使用简单的动作序列",
            "7. 如果动作需要特定对象但环境中没有，可以使用默认对象（如 root 文件夹）",
            ""
        ])
        
        if failure_reason:
            prompt_lines.extend([
                f"注意：上一次规划失败，原因: {failure_reason}",
                "请根据这个反馈修正你的规划。",
                ""
            ])
        
        prompt_lines.append("任务序列（将参数占位符替换为具体对象）:")
        
        return "\n".join(prompt_lines)

    def _parse_response(self, response: str) -> List[str]:
        """解析LLM响应，提取任务链"""
        tasks = []
        
        # 按行分割，清理空白
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 提取PDDL格式的任务（如 "(scan root)"）
            # 使用正则表达式匹配括号内的内容
            match = re.match(r'^\s*\(([^)]+)\)\s*$', line)
            if match:
                task_content = match.group(1)
                tasks.append(f"({task_content})")
            else:
                # 尝试直接匹配括号格式
                if line.startswith('(') and line.endswith(')'):
                    tasks.append(line)
        
        return tasks

    def _extract_objects_from_facts(self, facts: Set[str]) -> Dict[str, List[str]]:
        """
        从环境事实中提取可用对象
        
        :param facts: 环境事实集合
        :return: 对象类型到对象名称列表的映射
        """
        objects = {
            "folder": ["root"],  # 默认文件夹
            "file": [],
            "archive": [],
            "filename": []
        }
        
        # 解析事实中的对象
        for fact in facts:
            # 匹配 (at ?file ?folder) 格式
            match = re.match(r'^\s*\(at\s+(\w+)\s+(\w+)\)\s*$', fact)
            if match:
                file_name, folder_name = match.groups()
                if file_name not in objects["file"]:
                    objects["file"].append(file_name)
                if folder_name not in objects["folder"]:
                    objects["folder"].append(folder_name)
            
            # 匹配 (connected ?folder1 ?folder2) 格式
            match = re.match(r'^\s*\(connected\s+(\w+)\s+(\w+)\)\s*$', fact)
            if match:
                folder1, folder2 = match.groups()
                if folder1 not in objects["folder"]:
                    objects["folder"].append(folder1)
                if folder2 not in objects["folder"]:
                    objects["folder"].append(folder2)
            
            # 匹配 (has_name ?file ?filename) 格式
            match = re.match(r'^\s*\(has_name\s+(\w+)\s+(\w+)\)\s*$', fact)
            if match:
                file_name, filename = match.groups()
                if file_name not in objects["file"]:
                    objects["file"].append(file_name)
                if filename not in objects["filename"]:
                    objects["filename"].append(filename)
        
        return objects

    def _validate_chain(self, chain: List[str], available_actions: List[str]) -> bool:
        """验证任务链是否有效"""
        if not chain:
            return False
        
        # 提取动作名称（第一个单词）
        action_pattern = re.compile(r'^\s*\((\w+)')
        
        for task in chain:
            match = action_pattern.match(task)
            if not match:
                return False
            
            action_name = match.group(1)
            
            # 检查动作是否在可用动作列表中
            # 注意：这里只检查动作名称，不检查完整参数匹配
            action_found = False
            for available_action in available_actions:
                if available_action.startswith(f"({action_name}"):
                    action_found = True
                    break
            
            if not action_found:
                return False
        
        return True

    def decompose_task_with_domain(
        self,
        user_goal: str,
        current_facts: Set[str],
        domain: str,
        previous_failure_reason: Optional[str] = None
    ) -> List[str]:
        """
        使用领域名称分解任务（便捷方法）

        :param user_goal: 用户目标描述
        :param current_facts: 当前环境事实集合
        :param domain: 领域名称
        :param previous_failure_reason: 上一次失败的原因
        :return: PDDL格式任务链列表
        """
        available_actions = self.get_available_actions(domain)
        if not available_actions:
            raise ValueError(f"领域 '{domain}' 没有可用的动作")
        
        return self.decompose_task(
            user_goal, current_facts, available_actions, previous_failure_reason
        )


# 工厂函数
def create_brain_llm(
    llm: ILLM,
    domain_actions: Optional[Dict[str, List[str]]] = None,
    config: Optional[Dict[str, Any]] = None
) -> BrainLLM:
    """创建BrainLLM实例"""
    if domain_actions is None:
        # 默认领域动作（文件管理）
        domain_actions = {
            "file_management": [
                "(scan ?d)",
                "(move ?f ?src ?dst)",
                "(remove ?f ?d)",
                "(rename ?f ?old_name ?new_name ?d)",
                "(copy ?src ?dst ?src_folder ?dst_folder)",
                "(compress ?f ?d ?a)",
                "(uncompress ?a ?d ?f)",
                "(create_file ?f ?name ?d)",
                "(create_folder ?d ?parent)",
                "(get_admin)",
                "(connect_folders ?d1 ?d2)",
            ]
        }
    
    return BrainLLM(llm, domain_actions, config)