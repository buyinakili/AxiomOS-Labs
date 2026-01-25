"""回归测试管理器接口定义"""
from abc import ABC, abstractmethod
from typing import Dict


class IRegressionManager(ABC):
    """回归测试管理器接口 - 负责回归测试"""

    @abstractmethod
    def run_regression_suite(
        self,
        candidate_domain_path: str,
        candidate_skill_path: str
    ) -> bool:
        """
        运行回归测试套件

        :param candidate_domain_path: 包含新Action的Domain PDDL路径
        :param candidate_skill_path: 新生成的Python技能脚本路径
        :return: 是否全部通过
        """
        pass

    @abstractmethod
    def save_new_test(self, task_data: Dict):
        """
        将新学会的任务加入回归测试库

        :param task_data: 任务数据，包含 goal, setup_actions 等
        """
        pass

    @abstractmethod
    def load_tests(self) -> list:
        """
        加载所有回归测试用例

        :return: 测试用例列表
        """
        pass
