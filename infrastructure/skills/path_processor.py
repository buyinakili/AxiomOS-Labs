#!/usr/bin/env python3
"""
路径处理器 - 解决技能基类中的硬编码路径处理问题

提供统一的路径处理逻辑，支持PDDL格式转换、安全路径构建和沙盒环境适配。
"""
import os
import re
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from config.settings import Settings

logger = logging.getLogger("AxiomLabs_path_processor")


@dataclass
class PathConfig:
    """路径配置"""
    base_path: str  # 基础路径
    pddl_dot_replacement: str = "_dot_"  # PDDL中点的替换字符串
    safe_path_separator: str = os.path.sep  # 路径分隔符
    enable_sandbox_mode: bool = False  # 是否启用沙盒模式
    sandbox_root: Optional[str] = None  # 沙盒根目录
    workspace_dir: str = "workspace"  # workspace目录名称


class PathProcessor:
    """路径处理器"""
    
    def __init__(self, config: Optional[PathConfig] = None):
        self.config = config or self._create_default_config()
        self._validate_config()
    
    def _create_default_config(self) -> PathConfig:
        """创建默认配置"""
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        
        # 检查是否为沙盒模式
        sandbox_storage_path = os.environ.get("SANDBOX_STORAGE_PATH")
        enable_sandbox = sandbox_storage_path is not None
        
        return PathConfig(
            base_path=sandbox_storage_path if enable_sandbox else os.getcwd(),
            pddl_dot_replacement="_dot_",
            enable_sandbox_mode=enable_sandbox,
            sandbox_root=sandbox_storage_path,
            workspace_dir="workspace"
        )
    
    def _validate_config(self):
        """验证配置"""
        if not os.path.exists(self.config.base_path):
            logger.warning(f"基础路径不存在: {self.config.base_path}")
            # 尝试创建目录
            try:
                os.makedirs(self.config.base_path, exist_ok=True)
                logger.info(f"已创建基础路径: {self.config.base_path}")
            except Exception as e:
                logger.error(f"创建基础路径失败: {e}")
    
    def to_pddl_name(self, filename: str) -> str:
        """
        将实际文件名转换为PDDL格式
        
        Args:
            filename: 实际文件名（可能包含点）
            
        Returns:
            PDDL格式的文件名（点替换为配置的字符串）
        """
        if not filename:
            return filename
        
        # 替换点
        result = filename.replace('.', self.config.pddl_dot_replacement)
        
        # 记录转换（调试用）
        if '.' in filename:
            logger.debug(f"to_pddl_name: {filename} -> {result}")
        
        return result
    
    def from_pddl_name(self, pddl_name: str) -> str:
        """
        将PDDL格式的文件名转换回实际文件名
        
        Args:
            pddl_name: PDDL格式的文件名
            
        Returns:
            实际文件名
        """
        if not pddl_name:
            return pddl_name
        
        # 替换回点
        result = pddl_name.replace(self.config.pddl_dot_replacement, '.')
        
        # 记录转换（调试用）
        if self.config.pddl_dot_replacement in pddl_name:
            logger.debug(f"from_pddl_name: {pddl_name} -> {result}")
        
        return result
    
    def safe_path(self, *parts: str) -> str:
        """
        安全构建路径
        
        Args:
            *parts: 路径组成部分
            
        Returns:
            绝对路径
        """
        # 处理PDDL格式的文件名
        safe_parts = []
        for part in parts:
            safe_parts.append(self.from_pddl_name(part))
        
        # 构建完整路径
        full_path = os.path.join(self.config.base_path, *safe_parts)
        
        # 规范化路径
        full_path = os.path.normpath(full_path)
        
        # 安全检查：确保路径在基础路径内（防止目录遍历攻击）
        if not self._is_path_safe(full_path):
            logger.warning(f"路径安全检查失败: {full_path} 不在基础路径 {self.config.base_path} 内")
            # 返回基础路径作为安全回退
            return self.config.base_path
        
        logger.debug(f"safe_path: 基础路径={self.config.base_path}, 部分={parts}, 完整路径={full_path}")
        return full_path
    
    def _is_path_safe(self, path: str) -> bool:
        """检查路径是否安全（在基础路径内）"""
        try:
            # 获取规范化的绝对路径
            abs_path = os.path.abspath(path)
            abs_base = os.path.abspath(self.config.base_path)
            
            # 检查路径是否以基础路径开头
            return abs_path.startswith(abs_base)
        except Exception:
            return False
    
    def get_relative_path(self, full_path: str) -> str:
        """
        获取相对于基础路径的相对路径
        
        Args:
            full_path: 完整路径
            
        Returns:
            相对路径
        """
        try:
            rel_path = os.path.relpath(full_path, self.config.base_path)
            # 如果是当前目录，返回空字符串
            if rel_path == ".":
                return ""
            return rel_path
        except ValueError:
            # 如果路径不在同一驱动器上，返回原路径
            return full_path
    
    def ensure_directory(self, *parts: str) -> str:
        """
        确保目录存在
        
        Args:
            *parts: 目录路径组成部分
            
        Returns:
            目录路径
        """
        dir_path = self.safe_path(*parts)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path
    
    def file_exists(self, *parts: str) -> bool:
        """检查文件是否存在"""
        file_path = self.safe_path(*parts)
        return os.path.exists(file_path)
    
    def is_file(self, *parts: str) -> bool:
        """检查是否为文件"""
        file_path = self.safe_path(*parts)
        return os.path.isfile(file_path)
    
    def is_directory(self, *parts: str) -> bool:
        """检查是否为目录"""
        dir_path = self.safe_path(*parts)
        return os.path.isdir(dir_path)
    
    def list_files(self, *parts: str) -> List[str]:
        """列出目录中的文件"""
        dir_path = self.safe_path(*parts)
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            return []
        
        try:
            return os.listdir(dir_path)
        except Exception as e:
            logger.error(f"列出目录失败 {dir_path}: {e}")
            return []
    
    def update_base_path(self, new_base_path: str):
        """更新基础路径"""
        old_base = self.config.base_path
        self.config.base_path = new_base_path
        
        # 验证新路径
        self._validate_config()
        
        logger.info(f"更新基础路径: {old_base} -> {new_base_path}")
    
    def enable_sandbox_mode(self, sandbox_root: str):
        """启用沙盒模式"""
        self.config.enable_sandbox_mode = True
        self.config.sandbox_root = sandbox_root
        self.update_base_path(sandbox_root)
        logger.info(f"启用沙盒模式，根目录: {sandbox_root}")
    
    def disable_sandbox_mode(self):
        """禁用沙盒模式"""
        self.config.enable_sandbox_mode = False
        self.config.sandbox_root = None
        self.update_base_path(os.getcwd())
        logger.info("禁用沙盒模式")
    
    def get_workspace_path(self) -> str:
        """获取workspace路径"""
        if self.config.enable_sandbox_mode and self.config.sandbox_root:
            # 沙盒模式下，基础路径就是沙盒根目录
            return self.config.base_path
        else:
            # 生产模式下，使用workspace目录
            return self.safe_path(self.config.workspace_dir)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "base_path": self.config.base_path,
            "pddl_dot_replacement": self.config.pddl_dot_replacement,
            "enable_sandbox_mode": self.config.enable_sandbox_mode,
            "sandbox_root": self.config.sandbox_root,
            "workspace_dir": self.config.workspace_dir,
            "workspace_path": self.get_workspace_path()
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# 默认路径处理器
_default_processor = None

def get_default_processor() -> PathProcessor:
    """获取默认路径处理器"""
    global _default_processor
    if _default_processor is None:
        _default_processor = PathProcessor()
    return _default_processor


def to_pddl_name(filename: str) -> str:
    """将实际文件名转换为PDDL格式（快捷方式）"""
    return get_default_processor().to_pddl_name(filename)


def from_pddl_name(pddl_name: str) -> str:
    """将PDDL格式的文件名转换回实际文件名（快捷方式）"""
    return get_default_processor().from_pddl_name(pddl_name)


def safe_path(*parts: str) -> str:
    """安全构建路径（快捷方式）"""
    return get_default_processor().safe_path(*parts)


# 测试函数
def test_path_processor():
    """测试路径处理器"""
    print("测试路径处理器...")
    
    # 创建路径处理器
    processor = PathProcessor()
    
    print("配置信息:")
    print(processor)
    
    # 测试文件名转换
    print("\n测试文件名转换:")
    test_filenames = [
        "file.txt",
        "document.pdf",
        "image.jpg",
        "script.py",
        "data.json",
        "file_with_multiple.dots.in.name.tar.gz"
    ]
    
    for filename in test_filenames:
        pddl_name = processor.to_pddl_name(filename)
        original = processor.from_pddl_name(pddl_name)
        print(f"  {filename} -> {pddl_name} -> {original} (匹配: {filename == original})")
    
    # 测试路径构建
    print("\n测试路径构建:")
    test_paths = [
        ("folder", "file.txt"),
        ("docs", "subfolder", "document.pdf"),
        ("", "root_file.txt"),  # 空部分
    ]
    
    for parts in test_paths:
        safe = processor.safe_path(*parts)
        print(f"  {parts} -> {safe}")
    
    # 测试相对路径
    print("\n测试相对路径:")
    full_path = processor.safe_path("folder", "subfolder", "file.txt")
    rel_path = processor.get_relative_path(full_path)
    print(f"  完整路径: {full_path}")
    print(f"  相对路径: {rel_path}")
    
    # 测试目录操作
    print("\n测试目录操作:")
    test_dir = processor.ensure_directory("test_dir", "subdir")
    print(f"  确保目录存在: {test_dir}")
    print(f"  目录是否存在: {os.path.exists(test_dir)}")
    
    # 清理测试目录
    import shutil
    if os.path.exists("test_dir"):
        shutil.rmtree("test_dir")
        print("  已清理测试目录")
    
    print("路径处理器测试完成！")


if __name__ == "__main__":
    test_path_processor()