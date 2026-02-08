#!/usr/bin/env python3
"""
技能参数映射器 - 解决MCP执行器中的硬编码参数映射问题

将动作字符串参数映射到MCP工具的参数字典，支持动态配置和扩展。
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("AxiomLabs_parameter_mapper")


@dataclass
class ParameterMapping:
    """参数映射配置"""
    tool_name: str  # 工具名称
    param_schema: Dict[str, Any]  # 参数模式（JSON Schema）
    mapping_rules: List[Dict[str, Any]] = field(default_factory=list)  # 映射规则
    positional_mapping: bool = True  # 是否使用位置参数映射
    custom_mapper: Optional[str] = None  # 自定义映射函数名称


@dataclass
class MappingRule:
    """映射规则"""
    param_name: str  # 目标参数名
    source_type: str  # 来源类型：positional, named, constant, derived
    source_value: Any  # 来源值
    required: bool = True  # 是否必需
    default_value: Any = None  # 默认值


class ParameterMapper:
    """参数映射器"""
    
    def __init__(self):
        self.mappings: Dict[str, ParameterMapping] = {}
        self._initialize_default_mappings()
    
    def _initialize_default_mappings(self):
        """初始化默认映射"""
        # scan 工具映射
        self.register_mapping(
            ParameterMapping(
                tool_name="scan",
                param_schema={
                    "type": "object",
                    "properties": {
                        "folder": {"type": "string", "description": "要扫描的文件夹"}
                    },
                    "required": ["folder"]
                },
                mapping_rules=[
                    {"param_name": "folder", "source_type": "positional", "source_value": 0}
                ]
            )
        )
        
        # move 工具映射
        self.register_mapping(
            ParameterMapping(
                tool_name="move",
                param_schema={
                    "type": "object",
                    "properties": {
                        "file_name": {"type": "string", "description": "文件名"},
                        "from_folder": {"type": "string", "description": "源文件夹"},
                        "to_folder": {"type": "string", "description": "目标文件夹"}
                    },
                    "required": ["file_name", "from_folder", "to_folder"]
                },
                mapping_rules=[
                    {"param_name": "file_name", "source_type": "positional", "source_value": 0},
                    {"param_name": "from_folder", "source_type": "positional", "source_value": 1},
                    {"param_name": "to_folder", "source_type": "positional", "source_value": 2}
                ]
            )
        )
        
        # compress 工具映射
        self.register_mapping(
            ParameterMapping(
                tool_name="compress",
                param_schema={
                    "type": "object",
                    "properties": {
                        "file_name": {"type": "string", "description": "文件名"},
                        "folder": {"type": "string", "description": "文件夹"},
                        "archive_name": {"type": "string", "description": "压缩包名称"}
                    },
                    "required": ["file_name", "folder", "archive_name"]
                },
                mapping_rules=[
                    {"param_name": "file_name", "source_type": "positional", "source_value": 0},
                    {"param_name": "folder", "source_type": "positional", "source_value": 1},
                    {"param_name": "archive_name", "source_type": "positional", "source_value": 2}
                ]
            )
        )
        
        # remove_file 工具映射
        self.register_mapping(
            ParameterMapping(
                tool_name="remove_file",
                param_schema={
                    "type": "object",
                    "properties": {
                        "file_name": {"type": "string", "description": "文件名"},
                        "folder_name": {"type": "string", "description": "文件夹名"}
                    },
                    "required": ["file_name", "folder_name"]
                },
                mapping_rules=[
                    {"param_name": "file_name", "source_type": "positional", "source_value": 0},
                    {"param_name": "folder_name", "source_type": "positional", "source_value": 1}
                ]
            )
        )
        
        # create_folder 工具映射
        self.register_mapping(
            ParameterMapping(
                tool_name="create_folder",
                param_schema={
                    "type": "object",
                    "properties": {
                        "folder": {"type": "string", "description": "新文件夹名称"},
                        "parent": {"type": "string", "description": "父文件夹名称"}
                    },
                    "required": ["folder", "parent"]
                },
                mapping_rules=[
                    {"param_name": "folder", "source_type": "positional", "source_value": 0},
                    {"param_name": "parent", "source_type": "positional", "source_value": 1}
                ]
            )
        )
        
        # get_admin 工具映射（无参数）
        self.register_mapping(
            ParameterMapping(
                tool_name="get_admin",
                param_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                mapping_rules=[]
            )
        )
        
        # rename_file 工具映射
        self.register_mapping(
            ParameterMapping(
                tool_name="rename_file",
                param_schema={
                    "type": "object",
                    "properties": {
                        "old_file": {"type": "string", "description": "原文件名"},
                        "new_file": {"type": "string", "description": "新文件名"},
                        "folder": {"type": "string", "description": "文件夹"}
                    },
                    "required": ["old_file", "new_file", "folder"]
                },
                mapping_rules=[
                    {"param_name": "old_file", "source_type": "positional", "source_value": 0},
                    {"param_name": "new_file", "source_type": "positional", "source_value": 1},
                    {"param_name": "folder", "source_type": "positional", "source_value": 2}
                ]
            )
        )
    
    def register_mapping(self, mapping: ParameterMapping):
        """注册参数映射"""
        self.mappings[mapping.tool_name] = mapping
        logger.debug(f"注册参数映射: {mapping.tool_name}")
    
    def has_mapping(self, tool_name: str) -> bool:
        """检查是否有映射配置"""
        return tool_name in self.mappings
    
    def get_mapping(self, tool_name: str) -> Optional[ParameterMapping]:
        """获取映射配置"""
        return self.mappings.get(tool_name)
    
    def map_parameters(self, tool_name: str, args: List[str]) -> Dict[str, Any]:
        """
        映射参数
        
        Args:
            tool_name: 工具名称
            args: 位置参数列表
            
        Returns:
            参数字典
        """
        # 获取映射配置
        mapping = self.get_mapping(tool_name)
        if mapping is None:
            # 如果没有映射配置，使用通用映射
            return self._generic_mapping(tool_name, args)
        
        # 应用映射规则
        arguments = {}
        
        for rule_data in mapping.mapping_rules:
            rule = MappingRule(**rule_data)
            
            try:
                if rule.source_type == "positional":
                    # 位置参数映射
                    if rule.source_value < len(args):
                        arguments[rule.param_name] = args[rule.source_value]
                    elif rule.required:
                        raise ValueError(f"缺少必需参数 {rule.param_name} (位置 {rule.source_value})")
                    else:
                        arguments[rule.param_name] = rule.default_value
                
                elif rule.source_type == "named":
                    # 命名参数映射（格式：--param value）
                    # 这里简化处理，实际可能需要更复杂的解析
                    pass
                
                elif rule.source_type == "constant":
                    # 常量值
                    arguments[rule.param_name] = rule.source_value
                
                elif rule.source_type == "derived":
                    # 派生值（需要自定义处理）
                    pass
                    
            except (IndexError, ValueError) as e:
                if rule.required:
                    raise ValueError(f"参数映射失败 {rule.param_name}: {e}")
                else:
                    arguments[rule.param_name] = rule.default_value
        
        return arguments
    
    def _generic_mapping(self, tool_name: str, args: List[str]) -> Dict[str, Any]:
        """通用参数映射（向后兼容）"""
        arguments = {}
        
        # 将位置参数映射为 arg0, arg1, ...
        for i, arg in enumerate(args):
            arguments[f"arg{i}"] = arg
        
        logger.debug(f"使用通用参数映射: {tool_name} -> {arguments}")
        return arguments
    
    def validate_parameters(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证参数
        
        Args:
            tool_name: 工具名称
            arguments: 参数字典
            
        Returns:
            (是否有效, 错误信息)
        """
        mapping = self.get_mapping(tool_name)
        if mapping is None:
            # 如果没有映射配置，总是返回有效
            return True, ""
        
        # 检查必需参数
        for rule_data in mapping.mapping_rules:
            rule = MappingRule(**rule_data)
            if rule.required and rule.param_name not in arguments:
                return False, f"缺少必需参数: {rule.param_name}"
        
        # 检查参数类型（简化版本）
        # 实际应该使用JSON Schema验证
        
        return True, ""
    
    def load_mappings_from_file(self, filepath: str):
        """从文件加载映射配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for mapping_data in data.get("mappings", []):
                mapping = ParameterMapping(**mapping_data)
                self.register_mapping(mapping)
            
            logger.info(f"从文件加载了 {len(data.get('mappings', []))} 个映射配置: {filepath}")
        except Exception as e:
            logger.error(f"加载映射配置文件失败 {filepath}: {e}")
    
    def save_mappings_to_file(self, filepath: str):
        """保存映射配置到文件"""
        try:
            data = {"mappings": []}
            
            for mapping in self.mappings.values():
                mapping_dict = {
                    "tool_name": mapping.tool_name,
                    "param_schema": mapping.param_schema,
                    "mapping_rules": mapping.mapping_rules,
                    "positional_mapping": mapping.positional_mapping
                }
                if mapping.custom_mapper:
                    mapping_dict["custom_mapper"] = mapping.custom_mapper
                data["mappings"].append(mapping_dict)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"映射配置已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存映射配置失败 {filepath}: {e}")


# 默认参数映射器
_default_mapper = None

def get_default_mapper() -> ParameterMapper:
    """获取默认参数映射器"""
    global _default_mapper
    if _default_mapper is None:
        _default_mapper = ParameterMapper()
    return _default_mapper


def _translate_dot_to_storage_jail(arg: str) -> str:
    """
    将 _dot_ 相关的参数转换为物理路径参数
    
    规则：
    1. 如果参数是 "_dot_"，返回 "."（表示当前目录）
    2. 如果参数以 "_dot__slash_" 开头，将其替换为 "./"（表示当前目录下的子项）
    3. 否则返回原参数
    """
    if arg == "_dot_":
        return "."
    elif arg.startswith("_dot__slash_"):
        # _dot__slash_root -> ./root
        return "./" + arg[len("_dot__slash_"):]
    else:
        return arg

def map_action_to_arguments(action_str: str) -> Tuple[str, Dict[str, Any]]:
    """
    将动作字符串映射到工具名称和参数字典
    
    Args:
        action_str: 动作字符串（如 "move file_a folder_x folder_y" 或 "(scan workspace)"）
        
    Returns:
        (工具名称, 参数字典)
    """
    # 处理PDDL格式的动作（如 "(scan workspace)"）
    action_str = action_str.strip()
    
    # 如果以括号开头和结尾，移除它们
    if action_str.startswith("(") and action_str.endswith(")"):
        action_str = action_str[1:-1].strip()
    
    # 解析动作字符串
    parts = action_str.split()
    if not parts:
        raise ValueError("动作字符串为空")
    
    tool_name = parts[0].lower()
    args = parts[1:]
    
    # 转换参数：将 _dot_ 相关参数转换为 storage_jail 相关参数
    translated_args = [_translate_dot_to_storage_jail(arg) for arg in args]
    
    # 获取参数映射器
    mapper = get_default_mapper()
    
    # 映射参数
    arguments = mapper.map_parameters(tool_name, translated_args)
    
    return tool_name, arguments


# 测试函数
def test_parameter_mapper():
    """测试参数映射器"""
    print("测试参数映射器...")
    
    mapper = ParameterMapper()
    
    # 测试 scan 工具
    tool_name, args = "scan", ["workspace"]
    arguments = mapper.map_parameters(tool_name, args)
    print(f"{tool_name} {args} -> {arguments}")
    
    # 测试 move 工具
    tool_name, args = "move", ["file_a", "folder_x", "folder_y"]
    arguments = mapper.map_parameters(tool_name, args)
    print(f"{tool_name} {args} -> {arguments}")
    
    # 测试 compress 工具
    tool_name, args = "compress", ["file.txt", "docs", "archive.zip"]
    arguments = mapper.map_parameters(tool_name, args)
    print(f"{tool_name} {args} -> {arguments}")
    
    # 测试 remove_file 工具
    tool_name, args = "remove_file", ["old.txt", "temp"]
    arguments = mapper.map_parameters(tool_name, args)
    print(f"{tool_name} {args} -> {arguments}")
    
    # 测试 get_admin 工具
    tool_name, args = "get_admin", []
    arguments = mapper.map_parameters(tool_name, args)
    print(f"{tool_name} {args} -> {arguments}")
    
    # 测试未知工具
    tool_name, args = "unknown_tool", ["arg1", "arg2", "arg3"]
    arguments = mapper.map_parameters(tool_name, args)
    print(f"{tool_name} {args} -> {arguments}")
    
    # 测试 map_action_to_arguments 函数
    print("\n测试 map_action_to_arguments 函数:")
    test_actions = [
        "scan workspace",
        "move file_a folder_x folder_y",
        "compress file.txt docs archive.zip",
        "remove_file old.txt temp",
        "get_admin",
        "unknown_tool arg1 arg2 arg3"
    ]
    
    for action in test_actions:
        try:
            tool_name, arguments = map_action_to_arguments(action)
            print(f"  {action} -> {tool_name}: {arguments}")
        except Exception as e:
            print(f"  {action} -> 错误: {e}")
    
    print("参数映射器测试完成！")


if __name__ == "__main__":
    test_parameter_mapper()