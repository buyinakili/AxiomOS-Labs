"""AnalysisLLM实现 - 错误分析与修复建议"""
from typing import List, Set, Optional, Dict, Any
from interface.llm import ILLM
from interface.analysis_llm import IAnalysisLLM


class AnalysisLLM(IAnalysisLLM):
    """AnalysisLLM实现 - 分析错误并提供修复建议"""

    def __init__(
        self,
        llm: ILLM,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化AnalysisLLM

        :param llm: 基础LLM客户端
        :param config: 配置字典
        """
        self.llm = llm
        self.config = config or {}
        
        # 默认配置
        self.default_temperature = self.config.get("temperature", 0.3)
        self.debug = self.config.get("debug", False)

    def analyze_brain_failure(
        self,
        user_goal: str,
        current_facts: Optional[Set[str]],
        chain_of_mission: List[str],
        error_location: str,
        error_message: str
    ) -> str:
        """
        分析Brain层失败原因并提供修复建议

        :param user_goal: 用户目标描述
        :param current_facts: 当前环境事实集合（可选）
        :param chain_of_mission: 任务链
        :param error_location: 错误位置
        :param error_message: 错误信息
        :return: 修复建议描述
        """
        prompt = self._build_brain_analysis_prompt(
            user_goal, current_facts, chain_of_mission, error_location, error_message
        )
        
        if self.debug:
            print(f"[AnalysisLLM Debug] Brain分析提示词:\n{prompt}")
        
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=self.default_temperature
        )
        
        return response.strip()

    def analyze_nerves_failure(
        self,
        task: str,
        current_facts: Optional[Set[str]],
        chain_of_action: List[str],
        error_location: str,
        error_message: str
    ) -> str:
        """
        分析Nerves层失败原因并提供修复建议

        :param task: 当前任务
        :param current_facts: 当前环境事实集合（可选）
        :param chain_of_action: 动作链
        :param error_location: 错误位置
        :param error_message: 错误信息
        :return: 修复建议描述
        """
        prompt = self._build_nerves_analysis_prompt(
            task, current_facts, chain_of_action, error_location, error_message
        )
        
        if self.debug:
            print(f"[AnalysisLLM Debug] Nerves分析提示词:\n{prompt}")
        
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=self.default_temperature
        )
        
        return response.strip()

    def analyze_pddl_syntax_error(
        self,
        pddl_content: str,
        error_message: str,
        layer: str
    ) -> str:
        """
        分析PDDL语法错误并提供修复建议

        :param pddl_content: PDDL内容
        :param error_message: 错误信息
        :param layer: 错误发生的层
        :return: 修复建议描述
        """
        prompt = self._build_pddl_syntax_analysis_prompt(
            pddl_content, error_message, layer
        )
        
        if self.debug:
            print(f"[AnalysisLLM Debug] PDDL语法分析提示词:\n{prompt}")
        
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=self.default_temperature
        )
        
        return response.strip()

    def _build_brain_analysis_prompt(
        self,
        user_goal: str,
        current_facts: Optional[Set[str]],
        chain_of_mission: List[str],
        error_location: str,
        error_message: str
    ) -> str:
        """构建Brain层分析提示词"""
        prompt_lines = [
            "你是一个任务规划错误分析专家。请分析以下Brain层规划失败的原因，并提供具体的修复建议。",
            "",
            f"用户目标: \"{user_goal}\"",
            ""
        ]
        
        if current_facts:
            prompt_lines.append("当前环境事实:")
            for fact in sorted(current_facts):
                prompt_lines.append(f"  {fact}")
            prompt_lines.append("")
        
        prompt_lines.append("生成的任务链:")
        for i, task in enumerate(chain_of_mission):
            prompt_lines.append(f"  {i+1}. {task}")
        
        prompt_lines.extend([
            "",
            f"错误位置: {error_location}",
            f"错误信息: {error_message}",
            "",
            "请分析:",
            "1. 失败的根本原因是什么？",
            "2. 任务链中存在哪些问题？",
            "3. 如何修正任务链以实现用户目标？",
            "4. 具体的修复建议是什么？",
            "",
            "请提供清晰、具体的修复建议，帮助规划器重新生成正确的任务链。",
            "",
            "分析结果:"
        ])
        
        return "\n".join(prompt_lines)

    def _build_nerves_analysis_prompt(
        self,
        task: str,
        current_facts: Optional[Set[str]],
        chain_of_action: List[str],
        error_location: str,
        error_message: str
    ) -> str:
        """构建Nerves层分析提示词"""
        prompt_lines = [
            "你是一个动作规划错误分析专家。请分析以下Nerves层规划失败的原因，并提供具体的修复建议。",
            "",
            f"当前任务: {task}",
            ""
        ]
        
        if current_facts:
            prompt_lines.append("当前环境事实:")
            for fact in sorted(current_facts):
                prompt_lines.append(f"  {fact}")
            prompt_lines.append("")
        
        prompt_lines.append("生成的动作链:")
        for i, action in enumerate(chain_of_action):
            prompt_lines.append(f"  {i+1}. {action}")
        
        prompt_lines.extend([
            "",
            f"错误位置: {error_location}",
            f"错误信息: {error_message}",
            "",
            "请分析:",
            "1. 失败的根本原因是什么？",
            "2. 动作链中存在哪些问题？",
            "3. 是否缺少必要的前置条件？",
            "4. 是否使用了不可用的对象或动作？",
            "5. 如何修正动作链以完成当前任务？",
            "6. 具体的修复建议是什么？",
            "",
            "请提供清晰、具体的修复建议，帮助规划器重新生成正确的动作链。",
            "",
            "分析结果:"
        ])
        
        return "\n".join(prompt_lines)

    def _build_pddl_syntax_analysis_prompt(
        self,
        pddl_content: str,
        error_message: str,
        layer: str
    ) -> str:
        """构建PDDL语法分析提示词"""
        prompt_lines = [
            f"你是一个PDDL语法专家。请分析以下{layer}层PDDL语法错误，并提供具体的修复建议。",
            "",
            f"PDDL内容:",
            pddl_content,
            "",
            f"错误信息: {error_message}",
            "",
            "请分析:",
            "1. 语法错误的具体位置和类型",
            "2. PDDL格式规范要求",
            "3. 如何修正语法错误",
            "4. 修正后的正确PDDL格式",
            "",
            "请提供清晰、具体的修复建议，包括修正后的PDDL代码示例。",
            "",
            "分析结果:"
        ]
        
        return "\n".join(prompt_lines)

    def analyze_general_failure(
        self,
        context: Dict[str, Any],
        error_message: str,
        failure_type: str
    ) -> str:
        """
        分析通用失败原因（扩展方法）

        :param context: 上下文信息字典
        :param error_message: 错误信息
        :param failure_type: 失败类型
        :return: 修复建议描述
        """
        prompt_lines = [
            f"你是一个AI系统错误分析专家。请分析以下{failure_type}失败的原因，并提供具体的修复建议。",
            "",
            f"失败类型: {failure_type}",
            f"错误信息: {error_message}",
            "",
            "上下文信息:"
        ]
        
        for key, value in context.items():
            if isinstance(value, (list, set)):
                prompt_lines.append(f"{key}:")
                for item in value:
                    prompt_lines.append(f"  {item}")
            else:
                prompt_lines.append(f"{key}: {value}")
        
        prompt_lines.extend([
            "",
            "请分析失败原因并提供具体的修复建议:",
            "",
            "分析结果:"
        ])
        
        prompt = "\n".join(prompt_lines)
        
        if self.debug:
            print(f"[AnalysisLLM Debug] 通用分析提示词:\n{prompt}")
        
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=self.default_temperature
        )
        
        return response.strip()


# 工厂函数
def create_analysis_llm(
    llm: ILLM,
    config: Optional[Dict[str, Any]] = None
) -> AnalysisLLM:
    """创建AnalysisLLM实例"""
    return AnalysisLLM(llm, config)