"""CoT数据生成器常量定义"""

from typing import List


class Constants:
    """常量配置类"""
    
    # ========== 项目配置 ==========
    PROJECT_NAME: str = "CoT-Data-Generator"
    VERSION: str = "0.1.0"
    
    # ========== 路径配置 ==========
    PDDL_CONFIGS_DIR: str = "pddl_configs"
    WORKSPACE_DIR: str = "workspace"
    DATA_OUTPUT_DIR: str = "data_output"
    
    # ========== LLM配置 ==========
    DEFAULT_LLM_BASE_URL: str = "https://api.deepseek.com"
    DEFAULT_LLM_MODEL: str = "deepseek-chat"
    DEFAULT_LLM_TEMPERATURE: float = 0.1
    DEFAULT_LLM_MAX_TOKENS: int = 2000
    
    # ========== 算法配置 ==========
    DEFAULT_MAX_ITERATIONS: int = 3
    DEFAULT_MAX_EVOLUTION_RETRIES: int = 3
    DEFAULT_PLANNING_TIMEOUT: int = 60
    DEFAULT_EVOLUTION_MAX_RETRIES: int = 3
    DEFAULT_EVOLUTION_MAX_PDDL_RETRIES: int = 2
    DEFAULT_CURRICULUM_MAX_RETRIES: int = 2
    
    # ========== Brain/Nerves配置 ==========
    BRAIN_FALSE_LIMIT: int = 3
    NERVES_FALSE_LIMIT: int = 3
    
    # ========== 领域配置 ==========
    DEFAULT_DOMAIN_NAME: str = "file_management"
    
    # ========== 九大原子动作 ==========
    @staticmethod
    def get_nine_atomic_actions() -> List[str]:
        return [
            "scan", "move", "remove", "rename", "copy",
            "compress", "uncompress", "create_file", "create_folder"
        ]
    
    # ========== Nerves反射白名单 ==========
    @staticmethod
    def get_nerves_action_whitelist() -> List[str]:
        return [
            "move", "remove", "copy", "rename", "scan",
            "compress", "uncompress", "create_file", "create_folder"
        ]
    
    # ========== 逻辑复杂度关键词 ==========
    @staticmethod
    def get_logic_keywords() -> List[str]:
        return [
            "如果", "所有", "除了", "且", "或", "当...时",
            "if", "all", "except", "and", "or", "when"
        ]
    
    # ========== 模糊代词检测 ==========
    @staticmethod
    def get_vague_pronouns() -> List[str]:
        return [
            "那个", "一些", "相关", "*", "所有", "某些",
            "that", "some", "related", "all", "certain"
        ]
    
    # ========== 数据格式配置 ==========
    DATA_SCHEMA_VERSION: str = "1.0.0"
    MAX_DATA_POINTS_PER_FILE: int = 1000
    
    # ========== 翻译器配置 ==========
    @staticmethod
    def get_granularity_conversion_rules() -> dict:
        return {
            "size > 1GB": "is_large",
            "mod_time < 2025": "is_old",
            "error_access_denied": "not_has_permission"
        }