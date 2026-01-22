import os
import shutil
import tempfile
import time
from pathlib import Path

class SandboxManager:
    def __init__(self, base_project_dir=None):
        # 获取当前项目的根目录
        self.project_root = base_project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.current_sandbox_path = None
        self.storage_path = None

    def create_sandbox(self):
        """
        创建沙盒：复制必要的配置和数据，但不复制整个项目源码（保持轻量）
        """
        # 1. 在项目目录下创建一个可观察的 sandbox_runs 文件夹
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        sandbox_dir = os.path.join(self.project_root, "sandbox_runs", f"run_{timestamp}")
        os.makedirs(sandbox_dir, exist_ok=True)
        
        print(f"[Sandbox] 正在初始化临时环境: {sandbox_dir}")

        # 2. 复制 PDDL 定义 (Domain)
        # 假设原文件在 tests/domain.pddl
        src_domain = os.path.join(self.project_root, "tests", "domain.pddl")
        dst_domain = os.path.join(sandbox_dir, "domain_exp.pddl")
        if os.path.exists(src_domain):
            shutil.copy(src_domain, dst_domain)
            print(f"[Sandbox] 已镜像 Domain PDDL")

        # 3. 创建沙盒专用的存储空间 (Storage)
        # 这样 AI 删减文件只会在这个目录下发生
        src_storage = os.path.join(self.project_root, "storage")
        dst_storage = os.path.join(sandbox_dir, "storage_jail")
        if os.path.exists(src_storage):
            shutil.copytree(src_storage, dst_storage)
            print(f"[Sandbox] 已镜像物理文件系统 (Jail)")
        else:
            os.makedirs(dst_storage, exist_ok=True)

        # 4. 创建动态技能存放目录
        os.makedirs(os.path.join(sandbox_dir, "skills"), exist_ok=True)

        self.current_sandbox_path = sandbox_dir
        self.storage_path = dst_storage
        return sandbox_dir

    def get_pddl_path(self):
        return os.path.join(self.current_sandbox_path, "domain_exp.pddl")

    def clean_up(self):
        """调试阶段建议先不调用此方法，以便观察"""
        if self.current_sandbox_path and os.path.exists(self.current_sandbox_path):
            # shutil.rmtree(self.current_sandbox_path)
            print(f"[Sandbox] 沙盒 {self.current_sandbox_path} 已保留供调试检查")