"""沙盒管理器实现"""
import os
import shutil
import time
from interface.sandbox_manager import ISandboxManager


class SandboxManager(ISandboxManager):
    """沙盒管理器实现"""

    def __init__(self, project_root: str, storage_path: str, tests_path: str):
        """
        初始化沙盒管理器

        :param project_root: 项目根路径
        :param storage_path: 主系统storage路径
        :param tests_path: 测试文件路径
        """
        self.project_root = project_root
        self.main_storage_path = storage_path
        self.tests_path = tests_path
        self.current_sandbox_path = None
        self.storage_path = None

    def create_sandbox(self) -> str:
        """创建一个新的沙盒环境"""
        # 1. 创建沙盒目录
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        sandbox_dir = os.path.join(self.project_root, "sandbox_runs", f"run_{timestamp}")
        os.makedirs(sandbox_dir, exist_ok=True)

        print(f"[Sandbox] 正在初始化临时环境: {sandbox_dir}")

        # 2. 复制PDDL定义
        src_domain = os.path.join(self.tests_path, "domain.pddl")
        dst_domain = os.path.join(sandbox_dir, "domain_exp.pddl")

        if os.path.exists(src_domain):
            shutil.copy(src_domain, dst_domain)
            print(f"[Sandbox] 已镜像 Domain PDDL")

        # 3. 创建沙盒专用存储空间
        dst_storage = os.path.join(sandbox_dir, "storage_jail")

        if os.path.exists(self.main_storage_path):
            shutil.copytree(self.main_storage_path, dst_storage)
            print(f"[Sandbox] 已镜像物理文件系统 (Jail)")
        else:
            os.makedirs(dst_storage, exist_ok=True)

        # 4. 创建动态技能存放目录
        os.makedirs(os.path.join(sandbox_dir, "skills"), exist_ok=True)

        self.current_sandbox_path = sandbox_dir
        self.storage_path = dst_storage

        return sandbox_dir

    def reset_jail_storage(self):
        """回滚专用：彻底重新同步镜像"""
        if os.path.exists(self.storage_path):
            shutil.rmtree(self.storage_path)

        # 重新镜像
        if os.path.exists(self.main_storage_path):
            shutil.copytree(self.main_storage_path, self.storage_path)
        else:
            os.makedirs(self.storage_path, exist_ok=True)

        print("[Sandbox] 存储已重置")

    def get_pddl_path(self) -> str:
        """获取沙盒中的PDDL Domain文件路径"""
        return os.path.join(self.current_sandbox_path, "domain_exp.pddl")

    def get_storage_path(self) -> str:
        """获取沙盒的物理存储路径"""
        return self.storage_path

    def get_sandbox_path(self) -> str:
        """获取当前沙盒的根路径"""
        return self.current_sandbox_path

    def clean_up(self):
        """清理沙盒"""
        if self.current_sandbox_path and os.path.exists(self.current_sandbox_path):
            print(f"[Sandbox] 沙盒 {self.current_sandbox_path} 已保留供调试检查")
