"""配置管理类"""
import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from config.constants import Constants


@dataclass
class Settings:
    """AxiomLabs系统配置"""
    # 项目路径
    project_root: str
    pddl_configs_path: str  # 原tests_path，存放PDDL配置文件和回归注册表
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
    llm_temperature: float
    llm_max_tokens: int

    # 运行配置
    max_iterations: int
    max_evolution_retries: int
    planning_timeout: int
    
    # MCP 配置
    use_mcp: bool
    mcp_server_command: str
    mcp_server_args: str  # 空格分隔的参数
    mcp_connection_timeout: float
    mcp_tool_call_timeout: float
    mcp_disconnect_timeout: float
    
    # 领域配置
    domain_name: str
    domain_file_name: str
    problem_file_name: str
    
    # 沙盒配置
    sandbox_storage_dir_name: str
    sandbox_skills_dir_name: str
    sandbox_domain_file_name: str
    
    # 算法配置
    evolution_max_retries: int
    evolution_max_pddl_retries: int
    curriculum_max_retries: int
    
    # 执行器配置
    generated_skill_class_name: str
    
    # PDDL配置
    pddl_ai_generated_comment: str

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

        # 从常量获取默认值
        constants = Constants()
        
        # 构建路径（使用常量中的目录名）
        pddl_configs_path = os.path.join(project_root, constants.PDDL_CONFIGS_DIR_NAME)
        storage_path = os.path.join(project_root, constants.WORKSPACE_DIR_NAME)
        sandbox_runs_path = os.path.join(project_root, constants.SANDBOX_RUNS_DIR_NAME)
        skills_path = os.path.join(project_root, constants.SKILLS_RELATIVE_PATH)
        temp_dir = os.path.join(project_root, constants.TEMP_DIR_NAME)

        # 确保必要目录存在
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(sandbox_runs_path, exist_ok=True)

        # 从环境变量读取配置，使用常量作为默认值
        return cls(
            project_root=project_root,
            pddl_configs_path=pddl_configs_path,
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
                constants.DEFAULT_LLM_BASE_URL
            ),
            llm_model=os.getenv("DEEPSEEK_MODEL", constants.DEFAULT_LLM_MODEL),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", str(constants.DEFAULT_LLM_TEMPERATURE))),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", str(constants.DEFAULT_LLM_MAX_TOKENS))),
            max_iterations=int(os.getenv("MAX_ITERATIONS", str(constants.DEFAULT_MAX_ITERATIONS))),
            max_evolution_retries=int(os.getenv("MAX_EVOLUTION_RETRIES", str(constants.DEFAULT_MAX_EVOLUTION_RETRIES))),
            planning_timeout=int(os.getenv("PLANNING_TIMEOUT", str(constants.DEFAULT_PLANNING_TIMEOUT))),
            use_mcp=os.getenv("USE_MCP", "false").lower() == "true",
            mcp_server_command=os.getenv("MCP_SERVER_COMMAND", constants.DEFAULT_MCP_SERVER_COMMAND),
            mcp_server_args=os.getenv("MCP_SERVER_ARGS", constants.DEFAULT_MCP_SERVER_ARGS),
            mcp_connection_timeout=float(os.getenv("MCP_CONNECTION_TIMEOUT", str(constants.MCP_CONNECTION_TIMEOUT))),
            mcp_tool_call_timeout=float(os.getenv("MCP_TOOL_CALL_TIMEOUT", str(constants.MCP_TOOL_CALL_TIMEOUT))),
            mcp_disconnect_timeout=float(os.getenv("MCP_DISCONNECT_TIMEOUT", str(constants.MCP_DISCONNECT_TIMEOUT))),
            domain_name=os.getenv("DOMAIN_NAME", constants.DEFAULT_DOMAIN_NAME),
            domain_file_name=os.getenv("DOMAIN_FILE_NAME", constants.DOMAIN_FILE_NAME),
            problem_file_name=os.getenv("PROBLEM_FILE_NAME", constants.PROBLEM_FILE_NAME),
            sandbox_storage_dir_name=os.getenv("SANDBOX_STORAGE_DIR_NAME", constants.SANDBOX_STORAGE_DIR_NAME),
            sandbox_skills_dir_name=os.getenv("SANDBOX_SKILLS_DIR_NAME", constants.SANDBOX_SKILLS_DIR_NAME),
            sandbox_domain_file_name=os.getenv("SANDBOX_DOMAIN_FILE_NAME", constants.SANDBOX_DOMAIN_FILE_NAME),
            evolution_max_retries=int(os.getenv("EVOLUTION_MAX_RETRIES", str(constants.DEFAULT_EVOLUTION_MAX_RETRIES))),
            evolution_max_pddl_retries=int(os.getenv("EVOLUTION_MAX_PDDL_RETRIES", str(constants.DEFAULT_EVOLUTION_MAX_PDDL_RETRIES))),
            curriculum_max_retries=int(os.getenv("CURRICULUM_MAX_RETRIES", str(constants.DEFAULT_CURRICULUM_MAX_RETRIES))),
            generated_skill_class_name=os.getenv("GENERATED_SKILL_CLASS_NAME", constants.GENERATED_SKILL_CLASS_NAME),
            pddl_ai_generated_comment=os.getenv("PDDL_AI_GENERATED_COMMENT", constants.PDDL_AI_GENERATED_COMMENT)
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

        if not os.path.exists(self.pddl_configs_path):
            raise ValueError(f"PDDL配置路径不存在: {self.pddl_configs_path}")

        # 检查API Key
        if not self.llm_api_key:
            raise ValueError("LLM API Key未配置")

        # 验证数值范围
        if self.max_iterations <= 0:
            raise ValueError(f"MAX_ITERATIONS必须大于0，当前值: {self.max_iterations}")
            
        if self.max_evolution_retries <= 0:
            raise ValueError(f"MAX_EVOLUTION_RETRIES必须大于0，当前值: {self.max_evolution_retries}")
            
        if self.planning_timeout <= 0:
            raise ValueError(f"PLANNING_TIMEOUT必须大于0，当前值: {self.planning_timeout}")
            
        if self.mcp_connection_timeout <= 0:
            raise ValueError(f"MCP_CONNECTION_TIMEOUT必须大于0，当前值: {self.mcp_connection_timeout}")
            
        if self.mcp_tool_call_timeout <= 0:
            raise ValueError(f"MCP_TOOL_CALL_TIMEOUT必须大于0，当前值: {self.mcp_tool_call_timeout}")

        return True
    
    def validate_critical(self) -> bool:
        """
        验证关键配置（快速检查，用于快速迭代期）
        
        只检查会导致系统崩溃的关键配置，不检查所有细节
        
        :return: 关键配置是否有效
        :raises: ValueError 如果关键配置无效
        """
        errors = []
        
        # 1. 检查项目根目录
        if not os.path.exists(self.project_root):
            errors.append(f"❌ 项目根目录不存在: {self.project_root}")
        
        # 2. 检查LLM API密钥（不能是默认值）
        if not self.llm_api_key or self.llm_api_key == "your-api-key":
            errors.append("❌ LLM API密钥未配置（请设置DEEPSEEK_API_KEY环境变量）")
        
        # 3. 检查Fast-Downward（核心依赖）
        if not os.path.exists(self.downward_path):
            errors.append(f"❌ Fast-Downward路径不存在: {self.downward_path}")
            errors.append(f"   请确保已安装Fast-Downward或设置正确的DOWNWARD_PATH")
        
        # 4. 检查pddl_configs目录（包含PDDL文件）
        if not os.path.exists(self.pddl_configs_path):
            errors.append(f"❌ PDDL配置目录不存在: {self.pddl_configs_path}")
        else:
            # 检查必要的PDDL文件
            domain_file = os.path.join(self.pddl_configs_path, self.domain_file_name)
            problem_file = os.path.join(self.pddl_configs_path, self.problem_file_name)
            
            if not os.path.exists(domain_file):
                errors.append(f"❌ Domain文件不存在: {domain_file}")
            if not os.path.exists(problem_file):
                errors.append(f"❌ Problem文件不存在: {problem_file}")
        
        # 5. 检查workspace目录（会被自动创建，但需要检查权限）
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            test_file = os.path.join(self.storage_path, ".test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            errors.append(f"❌ 存储目录无写入权限: {self.storage_path} ({e})")
        
        if errors:
            error_msg = "关键配置验证失败:\n" + "\n".join(errors)
            error_msg += "\n\n💡 快速修复建议:"
            error_msg += "\n1. 检查.env文件或环境变量"
            error_msg += "\n2. 运行 'python tools/check_environment.py' 检查环境"
            error_msg += "\n3. 参考 README.md 中的安装指南"
            raise ValueError(error_msg)
        
        return True
    
    def get_domain_file_path(self) -> str:
        """获取Domain文件完整路径"""
        return os.path.join(self.pddl_configs_path, self.domain_file_name)
    
    def get_problem_file_path(self) -> str:
        """获取Problem文件完整路径"""
        return os.path.join(self.pddl_configs_path, self.problem_file_name)
    
    def get_sandbox_domain_path(self, sandbox_dir: str) -> str:
        """获取沙盒中的Domain文件路径"""
        return os.path.join(sandbox_dir, self.sandbox_domain_file_name)
    
    def get_sandbox_storage_path(self, sandbox_dir: str) -> str:
        """获取沙盒中的存储路径"""
        return os.path.join(sandbox_dir, self.sandbox_storage_dir_name)
    
    def get_sandbox_skills_path(self, sandbox_dir: str) -> str:
        """获取沙盒中的技能路径"""
        return os.path.join(sandbox_dir, self.sandbox_skills_dir_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'project_root': self.project_root,
            'pddl_configs_path': self.pddl_configs_path,
            'storage_path': self.storage_path,
            'sandbox_runs_path': self.sandbox_runs_path,
            'skills_path': self.skills_path,
            'temp_dir': self.temp_dir,
            'downward_path': self.downward_path,
            'llm_api_key': '***' if self.llm_api_key else '',
            'llm_base_url': self.llm_base_url,
            'llm_model': self.llm_model,
            'llm_temperature': self.llm_temperature,
            'llm_max_tokens': self.llm_max_tokens,
            'max_iterations': self.max_iterations,
            'max_evolution_retries': self.max_evolution_retries,
            'planning_timeout': self.planning_timeout,
            'use_mcp': self.use_mcp,
            'mcp_server_command': self.mcp_server_command,
            'mcp_server_args': self.mcp_server_args,
            'mcp_connection_timeout': self.mcp_connection_timeout,
            'mcp_tool_call_timeout': self.mcp_tool_call_timeout,
            'mcp_disconnect_timeout': self.mcp_disconnect_timeout,
            'domain_name': self.domain_name,
            'domain_file_name': self.domain_file_name,
            'problem_file_name': self.problem_file_name,
            'sandbox_storage_dir_name': self.sandbox_storage_dir_name,
            'sandbox_skills_dir_name': self.sandbox_skills_dir_name,
            'sandbox_domain_file_name': self.sandbox_domain_file_name,
            'evolution_max_retries': self.evolution_max_retries,
            'evolution_max_pddl_retries': self.evolution_max_pddl_retries,
            'curriculum_max_retries': self.curriculum_max_retries,
            'generated_skill_class_name': self.generated_skill_class_name,
            'pddl_ai_generated_comment': self.pddl_ai_generated_comment
        }
    
    def __str__(self) -> str:
        """返回配置的字符串表示"""
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
