#!/usr/bin/env python3
"""
技能注册表 - 管理MCP技能的注册、发现和加载

解决MCP服务器中的硬编码技能导入问题，实现动态、可配置的技能管理。
"""
import os
import sys
import json
import logging
import importlib
import importlib.util
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger("AxiomLabs_skill_registry")


@dataclass
class SkillConfig:
    """技能配置"""
    name: str  # 技能名称
    module_path: str  # 模块路径（如 "infrastructure.mcp_skills.scan_skill"）
    class_name: str  # 类名（如 "ScanSkill"）
    description: str = ""  # 技能描述
    enabled: bool = True  # 是否启用
    priority: int = 100  # 优先级（数值越小优先级越高）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据


@dataclass
class RegistryConfig:
    """注册表配置"""
    skill_directories: List[str] = field(default_factory=list)  # 技能目录列表
    skill_patterns: List[str] = field(default_factory=lambda: ["*_skill.py"])  # 技能文件模式
    auto_discovery: bool = True  # 是否自动发现技能
    config_file: Optional[str] = None  # 配置文件路径
    fallback_to_hardcoded: bool = False  # 是否回退到硬编码列表


class ISkillLoader(ABC):
    """技能加载器接口"""
    
    @abstractmethod
    def load_skill(self, config: SkillConfig) -> Any:
        """加载技能实例"""
        pass
    
    @abstractmethod
    def discover_skills(self, directory: str, patterns: List[str]) -> List[SkillConfig]:
        """发现目录中的技能"""
        pass


class PythonSkillLoader(ISkillLoader):
    """Python技能加载器"""
    
    def load_skill(self, config: SkillConfig) -> Any:
        """加载技能实例"""
        try:
            # 动态导入模块
            module = importlib.import_module(config.module_path)
            # 获取技能类
            skill_class = getattr(module, config.class_name)
            # 实例化技能
            return skill_class()
        except ImportError as e:
            logger.error(f"导入模块失败 {config.module_path}: {e}")
            raise
        except AttributeError as e:
            logger.error(f"找不到技能类 {config.class_name} 在模块 {config.module_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"实例化技能失败 {config.name}: {e}")
            raise
    
    def discover_skills(self, directory: str, patterns: List[str]) -> List[SkillConfig]:
        """发现目录中的技能"""
        import glob
        from pathlib import Path
        
        skills = []
        
        if not os.path.exists(directory):
            logger.warning(f"技能目录不存在: {directory}")
            return skills
        
        # 扫描所有匹配模式的文件
        for pattern in patterns:
            for filepath in glob.glob(os.path.join(directory, pattern)):
                try:
                    skill_config = self._parse_skill_file(filepath, directory)
                    if skill_config:
                        skills.append(skill_config)
                except Exception as e:
                    logger.error(f"解析技能文件失败 {filepath}: {e}")
        
        return skills
    
    def _parse_skill_file(self, filepath: str, base_dir: str) -> Optional[SkillConfig]:
        """解析技能文件，提取技能配置"""
        try:
            # 获取相对路径和模块名
            rel_path = os.path.relpath(filepath, base_dir)
            module_name = rel_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            
            # 动态导入模块以检查技能类
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None:
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 查找MCPBaseSkill的子类
            from infrastructure.mcp_skills.mcp_base_skill import MCPBaseSkill
            
            skill_classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, MCPBaseSkill) and 
                    attr is not MCPBaseSkill):
                    skill_classes.append((attr_name, attr))
            
            if not skill_classes:
                return None
            
            # 使用第一个找到的技能类
            class_name, skill_class = skill_classes[0]
            
            # 创建技能实例以获取元数据
            skill_instance = skill_class()
            
            # 构建模块路径
            # 计算相对于项目根目录的模块路径
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            rel_to_root = os.path.relpath(filepath, project_root)
            module_path = rel_to_root.replace('/', '.').replace('\\', '.').replace('.py', '')
            
            return SkillConfig(
                name=skill_instance.name,
                module_path=module_path,
                class_name=class_name,
                description=skill_instance.description,
                enabled=True,
                priority=100,
                metadata={
                    "file_path": filepath,
                    "input_schema": skill_instance.input_schema
                }
            )
            
        except Exception as e:
            logger.error(f"解析技能文件失败 {filepath}: {e}")
            return None


class SkillRegistry:
    """技能注册表"""
    
    def __init__(self, config: Optional[RegistryConfig] = None):
        self.config = config or RegistryConfig()
        self.loader = PythonSkillLoader()
        self.skills: Dict[str, SkillConfig] = {}  # 技能名称 -> 配置
        self.instances: Dict[str, Any] = {}  # 技能名称 -> 实例
        
        # 初始化
        self._initialize()
    
    def _initialize(self):
        """初始化注册表"""
        # 1. 从配置文件加载（如果存在）
        if self.config.config_file and os.path.exists(self.config.config_file):
            self._load_from_config_file()
        
        # 2. 自动发现技能
        if self.config.auto_discovery:
            self._discover_skills()
        
        # 3. 回退到硬编码列表（如果需要）
        if not self.skills and self.config.fallback_to_hardcoded:
            self._load_hardcoded_skills()
        
        logger.info(f"技能注册表初始化完成，共 {len(self.skills)} 个技能")
    
    def _load_from_config_file(self):
        """从配置文件加载技能"""
        try:
            with open(self.config.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            for skill_data in config_data.get("skills", []):
                config = SkillConfig(**skill_data)
                if config.enabled:
                    self.skills[config.name] = config
                    
            logger.info(f"从配置文件加载了 {len(config_data.get('skills', []))} 个技能配置")
        except Exception as e:
            logger.error(f"加载配置文件失败 {self.config.config_file}: {e}")
    
    def _discover_skills(self):
        """自动发现技能"""
        for directory in self.config.skill_directories:
            if not os.path.exists(directory):
                # 尝试相对于项目根目录解析
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                abs_dir = os.path.join(project_root, directory)
                if os.path.exists(abs_dir):
                    directory = abs_dir
                else:
                    logger.warning(f"技能目录不存在: {directory}")
                    continue
            
            logger.info(f"扫描技能目录: {directory}")
            discovered = self.loader.discover_skills(directory, self.config.skill_patterns)
            
            for config in discovered:
                if config.name not in self.skills:
                    self.skills[config.name] = config
                    logger.info(f"发现技能: {config.name}")
                else:
                    logger.debug(f"跳过重复技能: {config.name}")
    
    def _load_hardcoded_skills(self):
        """加载硬编码技能列表（向后兼容）"""
        logger.warning("使用硬编码技能列表（向后兼容）")
        
        hardcoded_skills = [
            SkillConfig(
                name="scan",
                module_path="infrastructure.mcp_skills.scan_skill",
                class_name="ScanSkill",
                description="扫描文件夹并生成PDDL事实",
                enabled=True,
                priority=100
            ),
            SkillConfig(
                name="move",
                module_path="infrastructure.mcp_skills.move_skill",
                class_name="MoveSkill",
                description="移动文件到另一个文件夹",
                enabled=True,
                priority=100
            ),
            SkillConfig(
                name="get_admin",
                module_path="infrastructure.mcp_skills.get_admin_skill",
                class_name="GetAdminSkill",
                description="获取管理员权限",
                enabled=True,
                priority=100
            ),
            SkillConfig(
                name="compress",
                module_path="infrastructure.mcp_skills.compress_skill",
                class_name="CompressSkill",
                description="压缩文件",
                enabled=True,
                priority=100
            ),
            SkillConfig(
                name="remove_file",
                module_path="infrastructure.mcp_skills.remove_file_skill",
                class_name="RemoveFileSkill",
                description="删除文件",
                enabled=True,
                priority=100
            )
        ]
        
        for config in hardcoded_skills:
            if config.name not in self.skills:
                self.skills[config.name] = config
    
    def register_skill(self, config: SkillConfig):
        """注册技能"""
        self.skills[config.name] = config
        logger.info(f"注册技能: {config.name}")
    
    def get_skill(self, name: str) -> Optional[Any]:
        """获取技能实例（懒加载）"""
        if name not in self.skills:
            return None
        
        # 懒加载：如果还没有实例化，则创建实例
        if name not in self.instances:
            try:
                config = self.skills[name]
                instance = self.loader.load_skill(config)
                self.instances[name] = instance
                logger.debug(f"实例化技能: {name}")
            except Exception as e:
                logger.error(f"实例化技能失败 {name}: {e}")
                return None
        
        return self.instances[name]
    
    def get_all_skills(self) -> List[Any]:
        """获取所有技能实例"""
        instances = []
        for name in self.skills:
            instance = self.get_skill(name)
            if instance:
                instances.append(instance)
        return instances
    
    def get_skill_names(self) -> List[str]:
        """获取所有技能名称"""
        return list(self.skills.keys())
    
    def has_skill(self, name: str) -> bool:
        """检查技能是否存在"""
        return name in self.skills
    
    def clear(self):
        """清空注册表"""
        self.skills.clear()
        self.instances.clear()
        logger.info("技能注册表已清空")
    
    def save_config(self, filepath: str):
        """保存配置到文件"""
        try:
            config_data = {
                "skill_directories": self.config.skill_directories,
                "skill_patterns": self.config.skill_patterns,
                "auto_discovery": self.config.auto_discovery,
                "skills": []
            }
            
            for config in self.skills.values():
                skill_dict = {
                    "name": config.name,
                    "module_path": config.module_path,
                    "class_name": config.class_name,
                    "description": config.description,
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "metadata": config.metadata
                }
                config_data["skills"].append(skill_dict)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存配置失败 {filepath}: {e}")


# 默认注册表实例
_default_registry = None

def get_default_registry() -> SkillRegistry:
    """获取默认技能注册表"""
    global _default_registry
    if _default_registry is None:
        # 默认配置
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config = RegistryConfig(
            skill_directories=[
                os.path.join(project_root, "infrastructure", "mcp_skills"),
                os.path.join(project_root, "workspace", "skills")  # 沙盒技能目录
            ],
            skill_patterns=["*_skill.py", "generated_skill_*.py"],
            auto_discovery=True,
            fallback_to_hardcoded=True
        )
        _default_registry = SkillRegistry(config)
    return _default_registry


# 工具函数
def register_skill_from_file(filepath: str) -> bool:
    """从文件注册技能"""
    try:
        registry = get_default_registry()
        loader = PythonSkillLoader()
        
        # 确定基础目录
        base_dir = os.path.dirname(filepath)
        if "mcp_skills" in base_dir:
            base_dir = os.path.dirname(base_dir)  # 上一级目录
        
        config = loader._parse_skill_file(filepath, base_dir)
        if config:
            registry.register_skill(config)
            return True
    except Exception as e:
        logger.error(f"从文件注册技能失败 {filepath}: {e}")
    return False


def get_skill_instance(name: str) -> Optional[Any]:
    """获取技能实例（快捷方式）"""
    return get_default_registry().get_skill(name)


def get_all_skill_instances() -> List[Any]:
    """获取所有技能实例（快捷方式）"""
    return get_default_registry().get_all_skills()


# 测试函数
def test_skill_registry():
    """测试技能注册表"""
    print("测试技能注册表...")
    
    # 创建测试配置
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config = RegistryConfig(
        skill_directories=[
            os.path.join(project_root, "infrastructure", "mcp_skills")
        ],
        auto_discovery=True,
        fallback_to_hardcoded=False
    )
    
    # 创建注册表
    registry = SkillRegistry(config)
    
    # 测试获取技能
    skill_names = registry.get_skill_names()
    print(f"发现的技能: {skill_names}")
    
    # 测试获取实例
    for name in skill_names:
        skill = registry.get_skill(name)
        if skill:
            print(f"  - {name}: {type(skill).__name__}")
        else:
            print(f"  - {name}: 加载失败")
    
    print("技能注册表测试完成！")
    return registry


if __name__ == "__main__":
    test_skill_registry()