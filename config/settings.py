"""配置管理类"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from config.constants import Constants


@dataclass
class Settings:
    """AxiomLabs系统配置 - 简化版"""
    
    # ========== 核心路径配置 ==========
    project_root: str
    """项目根目录"""
    
    # ========== LLM配置 ==========
    llm_api_key: str
    """LLM API密钥"""
    llm_base_url: str = field(default_factory=lambda: Constants.DEFAULT_LLM_BASE_URL)
    """LLM基础URL"""
    llm_model: str = field(default_factory=lambda: Constants.DEFAULT_LLM_MODEL)
    """LLM模型"""
    llm_temperature: float = field(default_factory=lambda: Constants.DEFAULT_LLM_TEMPERATURE)
    """LLM温度"""
    llm_max_tokens: int = field(default_factory=lambda: Constants.DEFAULT_LLM_MAX_TOKENS)
    """LLM最大token数"""
    
    # ========== 算法配置 ==========
    max_iterations: int = field(default_factory=lambda: Constants.DEFAULT_MAX_ITERATIONS)
    """最大迭代次数"""
    max_evolution_retries: int = field(default_factory=lambda: Constants.DEFAULT_MAX_EVOLUTION_RETRIES)
    """最大进化重试次数"""
    planning_timeout: int = field(default_factory=lambda: Constants.DEFAULT_PLANNING_TIMEOUT)
    """规划超时时间（秒）"""
    evolution_max_retries: int = field(default_factory=lambda: Constants.DEFAULT_EVOLUTION_MAX_RETRIES)
    """进化算法最大重试次数"""
    evolution_max_pddl_retries: int = field(default_factory=lambda: Constants.DEFAULT_EVOLUTION_MAX_PDDL_RETRIES)
    """进化算法PDDL重试次数"""
    curriculum_max_retries: int = field(default_factory=lambda: Constants.DEFAULT_CURRICULUM_MAX_RETRIES)
    """课程算法最大重试次数"""
    
    # ========== MCP配置 ==========
    use_mcp: bool = False
    """是否使用MCP执行器"""
    mcp_server_command: str = field(default_factory=lambda: Constants.DEFAULT_MCP_SERVER_COMMAND)
    """MCP服务器命令"""
    mcp_server_args: str = field(default_factory=lambda: Constants.DEFAULT_MCP_SERVER_ARGS)
    """MCP服务器参数"""
    mcp_connection_timeout: float = field(default_factory=lambda: Constants.MCP_CONNECTION_TIMEOUT)
    """MCP连接超时"""
    mcp_tool_call_timeout: float = field(default_factory=lambda: Constants.MCP_TOOL_CALL_TIMEOUT)
    """MCP工具调用超时"""
    mcp_disconnect_timeout: float = field(default_factory=lambda: Constants.MCP_DISCONNECT_TIMEOUT)
    """MCP断开连接超时"""
    
    # ========== 领域配置 ==========
    domain_name: str = field(default_factory=lambda: Constants.DEFAULT_DOMAIN_NAME)
    """领域名称"""
    
    # ========== 执行器配置 ==========
    generated_skill_class_name: str = field(default_factory=lambda: Constants.GENERATED_SKILL_CLASS_NAME)
    """生成的技能类名"""
    
    # ========== PDDL配置 ==========
    pddl_ai_generated_comment: str = field(default_factory=lambda: Constants.PDDL_AI_GENERATED_COMMENT)
    """PDDL AI生成注释"""
    
    # ========== 计算属性（动态生成） ==========
    @property
    def pddl_configs_path(self) -> str:
        """PDDL配置路径"""
        return os.path.join(self.project_root, Constants.PDDL_CONFIGS_DIR_NAME)
    
    @property
    def storage_path(self) -> str:
        """存储路径"""
        return os.path.join(self.project_root, Constants.WORKSPACE_DIR_NAME)
    
    @property
    def sandbox_runs_path(self) -> str:
        """沙盒运行路径"""
        return os.path.join(self.project_root, Constants.SANDBOX_RUNS_DIR_NAME)
    
    @property
    def skills_path(self) -> str:
        """技能路径"""
        return os.path.join(self.project_root, Constants.SKILLS_RELATIVE_PATH)
    
    @property
    def temp_dir(self) -> str:
        """临时目录"""
        return os.path.join(self.project_root, Constants.TEMP_DIR_NAME)
    
    @property
    def downward_path(self) -> str:
        """Fast Downward路径"""
        return os.path.join(self.project_root, "downward", "fast-downward.py")
    
    @property
    def domain_file_name(self) -> str:
        """Domain文件名"""
        return Constants.DOMAIN_FILE_NAME
    
    @property
    def problem_file_name(self) -> str:
        """Problem文件名"""
        return Constants.PROBLEM_FILE_NAME
    
    @property
    def sandbox_storage_dir_name(self) -> str:
        """沙盒存储目录名"""
        return Constants.SANDBOX_STORAGE_DIR_NAME
    
    @property
    def sandbox_skills_dir_name(self) -> str:
        """沙盒技能目录名"""
        return Constants.SANDBOX_SKILLS_DIR_NAME
    
    @property
    def sandbox_domain_file_name(self) -> str:
        """沙盒Domain文件名"""
        return Constants.SANDBOX_DOMAIN_FILE_NAME
    
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
        
        # 从环境变量读取配置，使用常量作为默认值
        return cls(
            project_root=project_root,
            llm_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            llm_base_url=os.getenv("DEEPSEEK_BASE_URL", Constants.DEFAULT_LLM_BASE_URL),
            llm_model=os.getenv("DEEPSEEK_MODEL", Constants.DEFAULT_LLM_MODEL),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", str(Constants.DEFAULT_LLM_TEMPERATURE))),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", str(Constants.DEFAULT_LLM_MAX_TOKENS))),
            max_iterations=int(os.getenv("MAX_ITERATIONS", str(Constants.DEFAULT_MAX_ITERATIONS))),
            max_evolution_retries=int(os.getenv("MAX_EVOLUTION_RETRIES", str(Constants.DEFAULT_MAX_EVOLUTION_RETRIES))),
            planning_timeout=int(os.getenv("PLANNING_TIMEOUT", str(Constants.DEFAULT_PLANNING_TIMEOUT))),
            use_mcp=os.getenv("USE_MCP", "false").lower() == "true",
            mcp_server_command=os.getenv("MCP_SERVER_COMMAND", Constants.DEFAULT_MCP_SERVER_COMMAND),
            mcp_server_args=os.getenv("MCP_SERVER_ARGS", Constants.DEFAULT_MCP_SERVER_ARGS),
            mcp_connection_timeout=float(os.getenv("MCP_CONNECTION_TIMEOUT", str(Constants.MCP_CONNECTION_TIMEOUT))),
            mcp_tool_call_timeout=float(os.getenv("MCP_TOOL_CALL_TIMEOUT", str(Constants.MCP_TOOL_CALL_TIMEOUT))),
            mcp_disconnect_timeout=float(os.getenv("MCP_DISCONNECT_TIMEOUT", str(Constants.MCP_DISCONNECT_TIMEOUT))),
            domain_name=os.getenv("DOMAIN_NAME", Constants.DEFAULT_DOMAIN_NAME),
            evolution_max_retries=int(os.getenv("EVOLUTION_MAX_RETRIES", str(Constants.DEFAULT_EVOLUTION_MAX_RETRIES))),
            evolution_max_pddl_retries=int(os.getenv("EVOLUTION_MAX_PDDL_RETRIES", str(Constants.DEFAULT_EVOLUTION_MAX_PDDL_RETRIES))),
            curriculum_max_retries=int(os.getenv("CURRICULUM_MAX_RETRIES", str(Constants.DEFAULT_CURRICULUM_MAX_RETRIES))),
            generated_skill_class_name=os.getenv("GENERATED_SKILL_CLASS_NAME", Constants.GENERATED_SKILL_CLASS_NAME),
            pddl_ai_generated_comment=os.getenv("PDDL_AI_GENERATED_COMMENT", Constants.PDDL_AI_GENERATED_COMMENT)
        )
    
    def validate(self, critical_only: bool = False) -> bool:
        """
        验证配置是否有效
        
        :param critical_only: 是否只验证关键配置（快速检查）
        :return: 配置是否有效
        :raises: ValueError 如果配置无效
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
        
        # 如果不是仅检查关键配置，进行完整验证
        if not critical_only:
            # 验证数值范围
            if self.max_iterations <= 0:
                errors.append(f"❌ MAX_ITERATIONS必须大于0，当前值: {self.max_iterations}")
                
            if self.max_evolution_retries <= 0:
                errors.append(f"❌ MAX_EVOLUTION_RETRIES必须大于0，当前值: {self.max_evolution_retries}")
                
            if self.planning_timeout <= 0:
                errors.append(f"❌ PLANNING_TIMEOUT必须大于0，当前值: {self.planning_timeout}")
                
            if self.mcp_connection_timeout <= 0:
                errors.append(f"❌ MCP_CONNECTION_TIMEOUT必须大于0，当前值: {self.mcp_connection_timeout}")
                
            if self.mcp_tool_call_timeout <= 0:
                errors.append(f"❌ MCP_TOOL_CALL_TIMEOUT必须大于0，当前值: {self.mcp_tool_call_timeout}")
        
        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(errors)
            error_msg += "\n\n💡 快速修复建议:"
            error_msg += "\n1. 检查.env文件或环境变量"
            error_msg += "\n2. 运行 'python tools/check_environment.py' 检查环境"
            error_msg += "\n3. 参考 README.md 中的安装指南"
            raise ValueError(error_msg)
        
        return True
    
    def validate_critical(self) -> bool:
        """验证关键配置（向后兼容）"""
        return self.validate(critical_only=True)
    
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
