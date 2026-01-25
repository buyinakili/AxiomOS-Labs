"""LLM接口定义"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ILLM(ABC):
    """LLM接口 - 抽象大语言模型调用"""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0,
        response_format: Dict[str, Any] = None
    ) -> str:
        """
        调用LLM进行对话

        :param messages: 消息列表 [{"role": "user", "content": "..."}]
        :param temperature: 温度参数
        :param response_format: 响应格式（如 {'type': 'json_object'}）
        :return: LLM响应内容
        """
        pass
