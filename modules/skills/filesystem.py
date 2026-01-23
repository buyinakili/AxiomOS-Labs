# modules/skills/filesystem.py
import os
import shutil
from typing import List  # <--- 新增这一行以修复 List 报未定义的错误
from .base import BaseSkill, SkillResult

class ScanSkill(BaseSkill):
    @property
    def name(self):
        return "scan"

    def execute(self, args: List[str]) -> SkillResult:
        # args[0]: folder_name
        folder = args[0]
        target_path = self._safe_path(folder)

        if not os.path.exists(target_path):
            return SkillResult(False, f"目录 {folder} 不存在")
        
        files = os.listdir(target_path)
        
        # 优化：自动生成 PDDL facts
        found_facts = []
        for f in files:
            # 忽略系统文件
            if f.startswith("."): continue
            safe_name = f.replace(".", "_dot_")
            # 假设扫描到的都是文件，如果是文件夹需要额外逻辑判断
            if os.path.isfile(os.path.join(target_path, f)):
                found_facts.append(f"(at {safe_name} {folder})")
            elif os.path.isdir(os.path.join(target_path, f)):
                # 必须明确区分文件夹，否则 Translator 会混淆文件和路径
                found_facts.append(f"(connected {folder} {safe_name})") 
                found_facts.append(f"(connected {safe_name} {folder})")
            
        found_facts.append(f"(scanned {folder})")

        return SkillResult(
            is_success=True, 
            message=f"扫描完成: {files}",
            add_facts=found_facts
        )

class MoveSkill(BaseSkill):
    @property
    def name(self):
        return "move"

    def execute(self, args: List[str]) -> SkillResult:
        # args: [file_name, from_folder, to_folder]
        # 注意：这里我们假设已经有权限，或者可以在这里再次检查
        file_sym, src_folder, dst_folder = args[0], args[1], args[2]
        
        src_path = self._safe_path(src_folder, file_sym)
        dst_path = self._safe_path(dst_folder, file_sym)

        try:
            shutil.move(src_path, dst_path)
            return SkillResult(
                is_success=True,
                message=f"Moved {file_sym} to {dst_folder}",
                add_facts=[f"(at {file_sym} {dst_folder})"],
                del_facts=[f"(at {file_sym} {src_folder})"]
            )
        except Exception as e:
            return SkillResult(False, f"Move Error: {str(e)}")



class GetAdminSkill(BaseSkill):
    @property
    def name(self): return "get_admin"
    def execute(self, args: List[str]) -> SkillResult:
        # 模拟提权逻辑
        return SkillResult(True, "Admin rights granted", [f"(has_admin_rights)"])

class CompressSkill(BaseSkill):
    @property
    def name(self): return "compress"
    def execute(self, args: List[str]) -> SkillResult:
        file_sym, folder, archive_sym = args[0], args[1], args[2]
        # 简化模拟逻辑
        return SkillResult(True, f"Compressed {file_sym} into {archive_sym}", 
                          add_facts=[f"(is_created {archive_sym})", f"(at {archive_sym} {folder})", f"(is_compressed {file_sym} {archive_sym})"])