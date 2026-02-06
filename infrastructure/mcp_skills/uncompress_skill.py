#!/usr/bin/env python3
"""
解压文件技能
"""
import os
import zipfile
import tarfile
from typing import Dict, Any, List
from .mcp_base_skill import MCPBaseSkill


class UncompressSkill(MCPBaseSkill):
    """解压文件技能"""
    
    @property
    def name(self) -> str:
        return "uncompress"
    
    @property
    def description(self) -> str:
        return "解压压缩文件。\nPDDL作用: 添加解压文件事实(at ?file ?folder)，删除压缩关系事实(is_compressed ?file ?archive)"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "archive": {"type": "string", "description": "压缩文件名（PDDL格式）"},
                "folder": {"type": "string", "description": "压缩文件所在文件夹名称"},
                "file": {"type": "string", "description": "要解压出的文件名（PDDL格式）"}
            },
            "required": ["archive", "folder", "file"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        archive = arguments["archive"]
        folder = arguments["folder"]
        file = arguments["file"]
        
        # 构建完整文件路径
        archive_path = self._safe_path(folder, archive)
        
        # 检查压缩文件是否存在
        if not os.path.exists(archive_path):
            return self.create_error_response(f"压缩文件 {archive} 在文件夹 {folder} 中不存在")
        
        # 确定压缩文件类型并解压
        try:
            extracted_files = []
            
            if archive.endswith('.zip'):
                # 解压ZIP文件
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    # 如果指定了具体文件，只解压该文件
                    if file != "*":
                        # 在ZIP中查找文件
                        zip_files = zip_ref.namelist()
                        if file not in zip_files:
                            return self.create_error_response(f"文件 {file} 不在压缩包 {archive} 中")
                        
                        # 解压指定文件
                        zip_ref.extract(file, self._safe_path(folder))
                        extracted_files = [file]
                    else:
                        # 解压所有文件
                        zip_ref.extractall(self._safe_path(folder))
                        extracted_files = zip_files
                        
            elif archive.endswith('.tar.gz') or archive.endswith('.tgz'):
                # 解压tar.gz文件
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    if file != "*":
                        # 查找文件
                        tar_files = tar_ref.getnames()
                        if file not in tar_files:
                            return self.create_error_response(f"文件 {file} 不在压缩包 {archive} 中")
                        
                        # 解压指定文件
                        tar_ref.extract(file, self._safe_path(folder))
                        extracted_files = [file]
                    else:
                        # 解压所有文件
                        tar_ref.extractall(self._safe_path(folder))
                        extracted_files = tar_files
                        
            elif archive.endswith('.tar'):
                # 解压tar文件
                with tarfile.open(archive_path, 'r') as tar_ref:
                    if file != "*":
                        # 查找文件
                        tar_files = tar_ref.getnames()
                        if file not in tar_files:
                            return self.create_error_response(f"文件 {file} 不在压缩包 {archive} 中")
                        
                        # 解压指定文件
                        tar_ref.extract(file, self._safe_path(folder))
                        extracted_files = [file]
                    else:
                        # 解压所有文件
                        tar_ref.extractall(self._safe_path(folder))
                        extracted_files = tar_files
            else:
                return self.create_error_response(f"不支持的压缩格式: {archive}")
            
            # 生成PDDL事实
            # 注意：PDDL中的文件名需要转换（. -> _dot_）
            pddl_archive = archive.replace('.', '_dot_')
            pddl_file = file.replace('.', '_dot_')
            
            if file == "*":
                # 解压所有文件的情况
                pddl_delta = f"-(is_compressed ?any_file {pddl_archive})"  # 简化表示
                message = f"解压压缩文件 {archive} 在文件夹 {folder}，解压出 {len(extracted_files)} 个文件"
            else:
                # 解压特定文件的情况
                pddl_delta = f"+(at {pddl_file} {folder}) -(is_compressed {pddl_file} {pddl_archive})"
                message = f"解压文件 {file} 从压缩包 {archive} 在文件夹 {folder}"
            
            return self.create_success_response(message, pddl_delta)
            
        except Exception as e:
            return self.create_error_response(f"解压失败: {str(e)}")