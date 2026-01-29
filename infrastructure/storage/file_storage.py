"""文件存储实现"""
import os
from typing import Optional
from interface.storage import IStorage
from config.settings import Settings


class FileStorage(IStorage):
    """基于文件系统的存储实现"""

    def __init__(self, config: Optional[Settings] = None):
        """
        初始化文件存储

        :param config: 系统配置，如果为None则使用默认配置
        """
        self.config = config or Settings.load_from_env()
        self.project_root = self.config.project_root
        self.storage_path = self.config.storage_path
        self.pddl_configs_path = self.config.pddl_configs_path
        self.domain_cache = {}  # 缓存Domain内容

    def read_domain(self, domain_name: str = None) -> str:
        """
        读取Domain PDDL内容

        :param domain_name: 领域名称，如果为None则使用配置中的默认领域名称
        :return: Domain PDDL内容
        """
        # 使用配置中的默认领域名称
        if domain_name is None:
            domain_name = self.config.domain_name
            
        # 缓存检查
        if domain_name in self.domain_cache:
            return self.domain_cache[domain_name]

        # 读取文件
        domain_path = self.config.get_domain_file_path()
        if not os.path.exists(domain_path):
            raise FileNotFoundError(f"Domain文件不存在: {domain_path}")

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
        domain_path = self.config.get_domain_file_path()
        with open(domain_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 更新缓存
        self.domain_cache[domain_name] = content

    def read_problem(self) -> str:
        """
        读取Problem PDDL内容

        :return: Problem PDDL内容
        """
        problem_path = self.config.get_problem_file_path()
        if not os.path.exists(problem_path):
            return ""

        with open(problem_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_problem(self, content: str):
        """
        写入Problem PDDL内容

        :param content: Problem PDDL内容
        """
        problem_path = self.config.get_problem_file_path()
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
        
    def get_domain_file_path(self) -> str:
        """获取Domain文件路径"""
        return self.config.get_domain_file_path()
        
    def get_problem_file_path(self) -> str:
        """获取Problem文件路径"""
        return self.config.get_problem_file_path()
