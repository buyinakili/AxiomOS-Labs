import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 工具路径配置
# 默认为空，由用户在 .env 或环境变量中指定
DOWNWARD_PATH = os.getenv("DOWNWARD_PATH", "fast-downward.py")

# 路径常量
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STORAGE_PATH = os.path.join(PROJECT_ROOT, "storage")
TESTS_PATH = os.path.join(PROJECT_ROOT, "tests")
DOMAIN_PDDL_PATH = os.path.join(TESTS_PATH, "domain.pddl")