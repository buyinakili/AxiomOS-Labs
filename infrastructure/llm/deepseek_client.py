"""DeepSeek LLM客户端实现"""
from openai import OpenAI
from typing import List, Dict, Any
from interface.llm import ILLM


class DeepSeekClient(ILLM):
    """DeepSeek LLM客户端实现"""

    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-chat"):
        """
        初始化DeepSeek客户端

        :param api_key: API密钥
        :param base_url: API基础URL
        :param model: 模型名称
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0,
        response_format: Dict[str, Any] = None
    ) -> str:
        """
        调用LLM进行对话

        :param messages: 消息列表
        :param temperature: 温度参数
        :param response_format: 响应格式
        :return: LLM响应内容
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
