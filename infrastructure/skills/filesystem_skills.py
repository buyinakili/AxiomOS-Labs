"""文件系统基础技能"""
import os
import shutil
from typing import List
from infrastructure.skills.base_skill import BaseSkill
from interface.executor import ExecutionResult


class ScanSkill(BaseSkill):
    """扫描文件夹技能"""

    @property
    def name(self):
        return "scan"

    def execute(self, args: List[str]) -> ExecutionResult:
        """
        扫描文件夹并返回PDDL事实

        :param args: [folder_name]
        :return: ExecutionResult
        """
        folder = args[0]
        target_path = self._safe_path(folder)

        if not os.path.exists(target_path):
            return ExecutionResult(False, f"目录 {folder} 不存在")

        files = os.listdir(target_path)

        # 生成PDDL事实
        found_facts = []
        for f in files:
            # 忽略系统文件
            if f.startswith("."):
                continue

            safe_name = self._to_pddl_name(f)

            if os.path.isfile(os.path.join(target_path, f)):
                found_facts.append(f"(at {safe_name} {folder})")
            elif os.path.isdir(os.path.join(target_path, f)):
                found_facts.append(f"(connected {folder} {safe_name})")
                found_facts.append(f"(connected {safe_name} {folder})")

        found_facts.append(f"(scanned {folder})")

        return ExecutionResult(
            success=True,
            message=f"扫描完成: {files}",
            add_facts=found_facts
        )


class MoveSkill(BaseSkill):
    """移动文件技能"""

    @property
    def name(self):
        return "move"

    def execute(self, args: List[str]) -> ExecutionResult:
        """
        移动文件

        :param args: [file_name, from_folder, to_folder]
        :return: ExecutionResult
        """
        file_sym, src_folder, dst_folder = args[0], args[1], args[2]

        src_path = self._safe_path(src_folder, file_sym)
        dst_path = self._safe_path(dst_folder, file_sym)

        try:
            shutil.move(src_path, dst_path)
            return ExecutionResult(
                success=True,
                message=f"已移动 {file_sym} 到 {dst_folder}",
                add_facts=[f"(at {file_sym} {dst_folder})"],
                del_facts=[f"(at {file_sym} {src_folder})"]
            )
        except Exception as e:
            return ExecutionResult(False, f"移动失败: {str(e)}")


class GetAdminSkill(BaseSkill):
    """获取管理员权限技能"""

    @property
    def name(self):
        return "get_admin"

    def execute(self, args: List[str]) -> ExecutionResult:
        """
        模拟获取管理员权限

        :param args: []
        :return: ExecutionResult
        """
        return ExecutionResult(
            success=True,
            message="已获取管理员权限",
            add_facts=["(has_admin_rights)"]
        )


class CompressSkill(BaseSkill):
    """压缩文件技能"""

    @property
    def name(self):
        return "compress"

    def execute(self, args: List[str]) -> ExecutionResult:
        """
        压缩文件

        :param args: [file_name, folder, archive_name]
        :return: ExecutionResult
        """
        file_sym, folder, archive_sym = args[0], args[1], args[2]

        # 简化模拟逻辑
        return ExecutionResult(
            success=True,
            message=f"已压缩 {file_sym} 为 {archive_sym}",
            add_facts=[
                f"(is_created {archive_sym})",
                f"(at {archive_sym} {folder})",
                f"(is_compressed {file_sym} {archive_sym})"
            ]
        )
