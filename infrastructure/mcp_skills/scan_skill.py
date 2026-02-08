#!/usr/bin/env python3
"""
扫描文件夹技能
"""
import os
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class ScanSkill(MCPBaseSkill):
    """扫描文件夹并生成PDDL事实"""
    
    @property
    def name(self) -> str:
        return "scan"
    
    @property
    def description(self) -> str:
        return "扫描文件夹并生成PDDL事实。\nPDDL作用: 生成(at ?file ?folder)和(is_created ?folder)事实，标记文件夹为已扫描(scanned ?folder)\n注意：使用物理路径作为参数，如 'storage_jail/root' 或 'run_20260208_173552/storage_jail/root'"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "要扫描的文件夹物理路径（如 'storage_jail/root'）"}
            },
            "required": ["folder"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        folder_path = arguments["folder"]
        
        # 特殊处理 "." 路径：将其转换为适当的相对路径
        # 在沙盒模式下，当前目录是 sandbox_runs/run_.../storage_jail
        # 我们希望返回以 storage_jail 为起始的路径
        normalized_folder_path = folder_path
        if folder_path == ".":
            # 获取当前工作目录
            current_dir = os.getcwd()
            # 检查是否在 sandbox_runs 目录下
            if "sandbox_runs" in current_dir:
                # 提取 sandbox_runs 之后的部分
                parts = current_dir.split("sandbox_runs/")
                if len(parts) > 1:
                    # parts[1] 应该是 run_.../storage_jail
                    # 我们只需要 storage_jail 部分
                    subparts = parts[1].split("/")
                    if len(subparts) >= 2:
                        # run_.../storage_jail -> 我们只需要 storage_jail
                        normalized_folder_path = subparts[-1]  # 最后一部分是 storage_jail
                    else:
                        normalized_folder_path = parts[1]
                else:
                    # 如果无法提取，使用当前目录名
                    normalized_folder_path = os.path.basename(current_dir)
            else:
                # 不在沙盒模式下，使用当前目录名
                normalized_folder_path = os.path.basename(current_dir)
            print(f"[ScanSkill] 将 '.' 转换为 '{normalized_folder_path}'")
        
        # 编码文件夹路径用于PDDL事实
        encoded_folder = self._encode_path(normalized_folder_path)
        
        # 使用安全路径方法获取实际路径（使用原始 folder_path）
        target_path = self._safe_path(folder_path)
        
        if not os.path.exists(target_path):
            return self.create_error_response(f"目录 {folder_path} 不存在")
        
        try:
            files = os.listdir(target_path)
        except Exception as e:
            return self.create_error_response(f"无法扫描目录: {str(e)}")
        
        # 生成PDDL事实
        found_facts = []
        for f in files:
            # 忽略系统文件
            if f.startswith("."):
                continue
            
            # 构建子项的完整路径（使用 normalized_folder_path 而不是 folder_path）
            item_relative_path = os.path.join(normalized_folder_path, f)
            encoded_item = self._encode_path(item_relative_path)
            
            full_path = os.path.join(target_path, f)
            if os.path.isfile(full_path):
                found_facts.append(f"(at {encoded_item} {encoded_folder})")
            elif os.path.isdir(full_path):
                # 不再生成connected事实，因为connected谓词已被删除
                # 只生成is_created事实来表示文件夹存在
                found_facts.append(f"(is_created {encoded_item})")
        
        found_facts.append(f"(scanned {encoded_folder})")
        
        # 构建PDDL delta字符串，用空格分隔多个事实
        pddl_delta = " ".join(found_facts)
        
        # 将 storage_jail_slash_ 前缀替换为 _dot__slash_，让LLM只看到 _dot_ 相关对象名
        # 根据用户设计：父文件夹是 storage_jail，LLM 应该看到 _dot_ 作为当前目录
        import re
        cwd = os.getcwd()
        cwd_basename = os.path.basename(cwd)
        
        # 如果当前目录是 storage_jail，则进行替换
        if cwd_basename == "storage_jail":
            # 将 storage_jail_slash_ 替换为 _dot__slash_
            pattern = re.compile(r"storage_jail_slash_")
            pddl_delta = pattern.sub("_dot__slash_", pddl_delta)
            # 同时处理 scanned 事实中的 storage_jail 替换为 _dot_
            scanned_pattern = re.compile(r"\bstorage_jail\b")
            pddl_delta = scanned_pattern.sub("_dot_", pddl_delta)
        # 如果当前目录是以 run_ 开头的目录（旧逻辑，保留兼容性）
        elif cwd_basename.startswith("run_"):
            # 将 run_..._..._slash_ 替换为 _dot__slash_
            pattern = re.compile(rf"{re.escape(cwd_basename)}_slash_")
            pddl_delta = pattern.sub("_dot__slash_", pddl_delta)
            # 同时处理 scanned 事实中的 run_..._... 替换为 _dot_
            scanned_pattern = re.compile(rf"\b{re.escape(cwd_basename)}\b")
            pddl_delta = scanned_pattern.sub("_dot_", pddl_delta)
        
        message = f"扫描文件夹 {folder_path} 完成，发现 {len(files)} 个项目"
        return self.create_success_response(message, pddl_delta)