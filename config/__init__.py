"""配置模块 - 提供向后兼容的配置变量导出"""
import os
from config.settings import Settings

# 加载配置
_settings = Settings.load_from_env()

# 向后兼容：导出旧的配置变量名
DEEPSEEK_API_KEY = _settings.llm_api_key
DEEPSEEK_BASE_URL = _settings.llm_base_url
DEEPSEEK_MODEL = _settings.llm_model
DOWNWARD_PATH = _settings.downward_path
PROJECT_ROOT = _settings.project_root

# 同时导出 Settings 类，供新代码使用
__all__ = [
    'Settings',
    'DEEPSEEK_API_KEY',
    'DEEPSEEK_BASE_URL',
    'DEEPSEEK_MODEL',
    'DOWNWARD_PATH',
    'PROJECT_ROOT'
]
