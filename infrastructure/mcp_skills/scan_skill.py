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
        return "扫描文件夹并生成PDDL事实。\nPDDL作用: 生成(at ?file ?folder)和(connected ?folder ?subfolder)事实，标记文件夹为已扫描(scanned ?folder)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "要扫描的文件夹名称"}
            },
            "required": ["folder"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        folder = arguments["folder"]
        target_path = self._safe_path(folder)
        
        if not os.path.exists(target_path):
            return self.create_error_response(f"目录 {folder} 不存在")
        
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
            
            safe_name = self._to_pddl_name(f)
            full_path = os.path.join(target_path, f)
            if os.path.isfile(full_path):
                found_facts.append(f"(at {safe_name} {folder})")
            elif os.path.isdir(full_path):
                # 双向连接性
                found_facts.append(f"(connected {folder} {safe_name})")
                found_facts.append(f"(connected {safe_name} {folder})")
        
        found_facts.append(f"(scanned {folder})")
        
        # 构建PDDL delta字符串，用空格分隔多个事实
        pddl_delta = " ".join(found_facts)
        message = f"扫描文件夹 {folder} 完成，发现 {len(files)} 个项目"
        return self.create_success_response(message, pddl_delta)