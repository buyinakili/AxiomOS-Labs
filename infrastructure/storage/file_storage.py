"""文件存储实现"""
import os
from interface.storage import IStorage


class FileStorage(IStorage):
    """基于文件系统的存储实现"""

    def __init__(self, project_root: str, storage_path: str, tests_path: str):
        """
        初始化文件存储

        :param project_root: 项目根路径
        :param storage_path: 物理存储路径
        :param tests_path: 测试文件路径
        """
        self.project_root = project_root
        self.storage_path = storage_path
        self.tests_path = tests_path
        self.domain_cache = {}  # 缓存Domain内容

    def read_domain(self, domain_name: str = "file_management") -> str:
        """
        读取Domain PDDL内容

        :param domain_name: 领域名称
        :return: Domain PDDL内容
        """
        # 缓存检查
        if domain_name in self.domain_cache:
            return self.domain_cache[domain_name]

        # 读取文件
        domain_path = os.path.join(self.tests_path, "domain.pddl")
        with open(domain_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 缓存
        self.domain_cache[domain_name] = content
        return content

    def write_domain(self, domain_name: str, content: str):
        """
        写入Domain PDDL内容

        :param domain_name: 领域名称
        :param content: Domain PDDL内容
        """
        domain_path = os.path.join(self.tests_path, "domain.pddl")
        with open(domain_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 更新缓存
        self.domain_cache[domain_name] = content

    def read_problem(self) -> str:
        """
        读取Problem PDDL内容

        :return: Problem PDDL内容
        """
        problem_path = os.path.join(self.tests_path, "generated_problem.pddl")
        if not os.path.exists(problem_path):
            return ""

        with open(problem_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_problem(self, content: str):
        """
        写入Problem PDDL内容

        :param content: Problem PDDL内容
        """
        problem_path = os.path.join(self.tests_path, "generated_problem.pddl")
        with open(problem_path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_storage_path(self) -> str:
        """
        获取物理存储路径

        :return: 存储路径
        """
        return self.storage_path

    def invalidate_cache(self):
        """清空Domain缓存"""
        self.domain_cache.clear()
