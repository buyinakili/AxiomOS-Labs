"""配置管理类"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Settings:
    """AxiomLabs系统配置"""
    # 项目路径
    project_root: str
    tests_path: str
    storage_path: str
    sandbox_runs_path: str
    skills_path: str
    temp_dir: str

    # Fast Downward配置
    downward_path: str

    # LLM配置
    llm_api_key: str
    llm_base_url: str
    llm_model: str

    # 运行配置
    max_iterations: int
    max_evolution_retries: int
    planning_timeout: int
    
    # MCP 配置
    use_mcp: bool
    mcp_server_command: str
    mcp_server_args: str  # 空格分隔的参数

    @classmethod
    def load_from_env(cls, project_root: Optional[str] = None) -> 'Settings':
        """
        从环境变量加载配置

        :param project_root: 项目根路径，如果为None则自动检测
        :return: Settings实例
        """
        # 加载.env文件
        load_dotenv()

        # 确定项目根路径
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 构建路径
        tests_path = os.path.join(project_root, "tests")
        storage_path = os.path.join(project_root, "workspace")
        sandbox_runs_path = os.path.join(project_root, "sandbox_runs")
        skills_path = os.path.join(project_root, "infrastructure", "skills")
        temp_dir = os.path.join(project_root, ".temp")

        # 确保必要目录存在
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(sandbox_runs_path, exist_ok=True)

        return cls(
            project_root=project_root,
            tests_path=tests_path,
            storage_path=storage_path,
            sandbox_runs_path=sandbox_runs_path,
            skills_path=skills_path,
            temp_dir=temp_dir,
            downward_path=os.getenv(
                "DOWNWARD_PATH",
                os.path.join(project_root, "downward", "fast-downward.py")
            ),
            llm_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            llm_base_url=os.getenv(
                "DEEPSEEK_BASE_URL",
                "https://api.deepseek.com"
            ),
            llm_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            max_iterations=int(os.getenv("MAX_ITERATIONS", "5")),
            max_evolution_retries=int(os.getenv("MAX_EVOLUTION_RETRIES", "4")),
            planning_timeout=int(os.getenv("PLANNING_TIMEOUT", "30")),
            use_mcp=os.getenv("USE_MCP", "false").lower() == "true",
            mcp_server_command=os.getenv("MCP_SERVER_COMMAND", "python3"),
            mcp_server_args=os.getenv("MCP_SERVER_ARGS", "mcp_server_structured.py")
        )

    def validate(self) -> bool:
        """
        验证配置是否有效

        :return: 配置是否有效
        """
        # 检查必要路径
        if not os.path.exists(self.downward_path):
            raise ValueError(f"Fast Downward路径不存在: {self.downward_path}")

        if not os.path.exists(self.storage_path):
            raise ValueError(f"存储路径不存在: {self.storage_path}")

        if not os.path.exists(self.tests_path):
            raise ValueError(f"测试路径不存在: {self.tests_path}")

        # 检查API Key
        if not self.llm_api_key:
            raise ValueError("LLM API Key未配置")

        return True
