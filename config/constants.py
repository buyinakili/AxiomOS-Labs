"""
配置常量定义

此文件包含AIOS-PDDL系统的所有硬编码常量，用于集中管理配置值。
这些常量可以在Settings类中被环境变量覆盖。
"""

from typing import Dict, Any


class Constants:
    """系统常量定义"""
    
    # ========== 文件路径相关常量 ==========
    
    # 目录名称
    PDDL_CONFIGS_DIR_NAME = "pddl_configs"  # 原tests目录，存放PDDL配置文件和回归注册表
    WORKSPACE_DIR_NAME = "workspace"
    SANDBOX_RUNS_DIR_NAME = "sandbox_runs"
    SKILLS_DIR_NAME = "skills"
    TEMP_DIR_NAME = ".temp"
    SANDBOX_STORAGE_DIR_NAME = "storage_jail"
    SANDBOX_SKILLS_DIR_NAME = "skills"
    
    # 文件名称
    DOMAIN_FILE_NAME = "domain.pddl"
    PROBLEM_FILE_NAME = "problem.pddl"
    SANDBOX_DOMAIN_FILE_NAME = "domain_exp.pddl"
    
    # 相对路径（相对于infrastructure目录）
    SKILLS_RELATIVE_PATH = "infrastructure/skills"
    
    # ========== 领域相关常量 ==========
    
    # 默认领域名称
    DEFAULT_DOMAIN_NAME = "file_management"
    
    # 领域专家规则文件（可选，未来扩展）
    DOMAIN_RULES_FILE = "domain_rules.json"
    
    # ========== 算法参数常量 ==========
    
    # 内核算法参数
    DEFAULT_MAX_ITERATIONS = 5
    DEFAULT_MAX_EVOLUTION_RETRIES = 4
    DEFAULT_PLANNING_TIMEOUT = 30
    
    # 进化算法参数
    DEFAULT_EVOLUTION_MAX_RETRIES = 4
    DEFAULT_EVOLUTION_MAX_PDDL_RETRIES = 2
    
    # 课程算法参数
    DEFAULT_CURRICULUM_MAX_RETRIES = 3
    
    # ========== LLM配置常量 ==========
    
    # DeepSeek API配置
    DEFAULT_LLM_BASE_URL = "https://api.deepseek.com"
    DEFAULT_LLM_MODEL = "deepseek-chat"
    
    # LLM调用参数
    DEFAULT_LLM_TEMPERATURE = 0.0
    DEFAULT_LLM_MAX_TOKENS = 2000
    
    # ========== MCP配置常量 ==========
    
    # MCP服务器配置
    DEFAULT_MCP_SERVER_COMMAND = "python3"
    DEFAULT_MCP_SERVER_SCRIPT = "mcp_server_structured.py"
    DEFAULT_MCP_SERVER_ARGS = "mcp_server_structured.py"
    
    # MCP超时配置（秒）
    MCP_CONNECTION_TIMEOUT = 5.0
    MCP_SESSION_INIT_TIMEOUT = 5.0
    MCP_TOOL_LIST_TIMEOUT = 5.0
    MCP_TOOL_CALL_TIMEOUT = 5.0
    MCP_DISCONNECT_TIMEOUT = 2.0
    MCP_FORCE_DISCONNECT_TIMEOUT = 3.0
    
    # ========== PDDL相关常量 ==========
    
    # PDDL注释模板
    PDDL_AI_GENERATED_COMMENT = ";; --- AI Generated Action ---"
    
    # ========== 执行器相关常量 ==========
    
    # 技能类名
    GENERATED_SKILL_CLASS_NAME = "GeneratedSkill"
    
    # 基础技能列表（用于进化算法）
    BASE_SKILLS = ["scan", "move", "get_admin", "remove_file", "compress"]
    
    # 类型映射：谓词 -> 参数位置 -> 类型（用于文件管理领域）
    TYPE_MAPPING = {
        "at": {0: "file", 1: "folder"},
        "connected": {0: "folder", 1: "folder"},
        "scanned": {0: "folder"},
        "is_created": {0: "file"},
        "is_compressed": {0: "file", 1: "archive"},
    }
    
    # ========== 沙盒相关常量 ==========
    
    # 沙盒目录前缀
    SANDBOX_DIR_PREFIX = "run_"
    
    # ========== 错误消息模板 ==========
    
    # 通用错误消息
    ERROR_FILE_NOT_FOUND = "文件不存在: {path}"
    ERROR_DIRECTORY_NOT_FOUND = "目录不存在: {path}"
    ERROR_API_KEY_NOT_CONFIGURED = "API密钥未配置"
    
    # ========== 日志消息模板 ==========
    
    # 通用日志前缀
    LOG_PREFIX_SANDBOX = "[Sandbox]"
    LOG_PREFIX_MCP = "[MCP]"
    LOG_PREFIX_PDDL = "[PDDL]"
    LOG_PREFIX_EXECUTOR = "[Executor]"
    LOG_PREFIX_MODIFIER = "[Modifier]"
    LOG_PREFIX_EVOLUTION = "[Evolution]"
    
    # ========== 配置映射 ==========
    
    @classmethod
    def get_all_constants(cls) -> Dict[str, Any]:
        """获取所有常量"""
        constants = {}
        for key in dir(cls):
            if not key.startswith('_') and not callable(getattr(cls, key)):
                constants[key] = getattr(cls, key)
        return constants
    
    @classmethod
    def get_path_constants(cls) -> Dict[str, str]:
        """获取路径相关常量"""
        return {
            'PDDL_CONFIGS_DIR_NAME': cls.PDDL_CONFIGS_DIR_NAME,
            'WORKSPACE_DIR_NAME': cls.WORKSPACE_DIR_NAME,
            'SANDBOX_RUNS_DIR_NAME': cls.SANDBOX_RUNS_DIR_NAME,
            'SKILLS_DIR_NAME': cls.SKILLS_DIR_NAME,
            'TEMP_DIR_NAME': cls.TEMP_DIR_NAME,
            'DOMAIN_FILE_NAME': cls.DOMAIN_FILE_NAME,
            'PROBLEM_FILE_NAME': cls.PROBLEM_FILE_NAME,
            'SANDBOX_DOMAIN_FILE_NAME': cls.SANDBOX_DOMAIN_FILE_NAME,
        }
    
    @classmethod
    def get_timeout_constants(cls) -> Dict[str, float]:
        """获取超时相关常量"""
        return {
            'MCP_CONNECTION_TIMEOUT': cls.MCP_CONNECTION_TIMEOUT,
            'MCP_SESSION_INIT_TIMEOUT': cls.MCP_SESSION_INIT_TIMEOUT,
            'MCP_TOOL_LIST_TIMEOUT': cls.MCP_TOOL_LIST_TIMEOUT,
            'MCP_TOOL_CALL_TIMEOUT': cls.MCP_TOOL_CALL_TIMEOUT,
            'MCP_DISCONNECT_TIMEOUT': cls.MCP_DISCONNECT_TIMEOUT,
            'MCP_FORCE_DISCONNECT_TIMEOUT': cls.MCP_FORCE_DISCONNECT_TIMEOUT,
        }


# 导出常量实例
CONSTANTS = Constants()