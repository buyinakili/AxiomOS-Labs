"""CoT数据生成器配置管理类"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from .constants import Constants


@dataclass
class Settings:
    """CoT数据生成器系统配置"""
    
    # ========== 核心路径配置 ==========
    project_root: str
    """项目根目录"""
    
    # ========== LLM配置 ==========
    llm_api_key: str = ""
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
    brain_false_limit: int = field(default_factory=lambda: Constants.BRAIN_FALSE_LIMIT)
    """Brain层失败限制"""
    nerves_false_limit: int = field(default_factory=lambda: Constants.NERVES_FALSE_LIMIT)
    """Nerves层失败限制"""
    planning_timeout: int = field(default_factory=lambda: Constants.DEFAULT_PLANNING_TIMEOUT)
    """规划超时时间（秒）"""
    
    # ========== 领域配置 ==========
    domain_name: str = field(default_factory=lambda: Constants.DEFAULT_DOMAIN_NAME)
    """领域名称"""
    
    # ========== 数据生成配置 ==========
    data_output_dir: str = field(default_factory=lambda: Constants.DATA_OUTPUT_DIR)
    """数据输出目录"""
    max_data_points_per_file: int = field(default_factory=lambda: Constants.MAX_DATA_POINTS_PER_FILE)
    """每个文件最大数据点数"""
    
    # ========== 计算属性（动态生成） ==========
    @property
    def pddl_configs_path(self) -> str:
        """PDDL配置路径"""
        return os.path.join(self.project_root, Constants.PDDL_CONFIGS_DIR)
    
    @property
    def workspace_path(self) -> str:
        """工作空间路径"""
        return os.path.join(self.project_root, Constants.WORKSPACE_DIR)
    
    @property
    def data_output_path(self) -> str:
        """数据输出路径"""
        return os.path.join(self.project_root, self.data_output_dir)
    
    # ========== 类方法 ==========
    @classmethod
    def load_from_env(cls, project_root: Optional[str] = None) -> 'Settings':
        """
        从环境变量加载配置
        
        :param project_root: 项目根目录，如果为None则使用当前文件所在目录的父目录
        :return: Settings实例
        """
        # 加载.env文件
        load_dotenv()
        
        # 确定项目根目录
        if project_root is None:
            # 使用当前文件的父目录的父目录（cot_generator/config -> cot_generator -> 项目根目录）
            import inspect
            current_file = inspect.getfile(cls)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(current_file))))
        
        # 从环境变量读取配置，使用默认值作为后备
        llm_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        return cls(
            project_root=project_root,
            llm_api_key=llm_api_key,
            llm_base_url=os.getenv("DEEPSEEK_BASE_URL", Constants.DEFAULT_LLM_BASE_URL),
            llm_model=os.getenv("DEEPSEEK_MODEL", Constants.DEFAULT_LLM_MODEL),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", str(Constants.DEFAULT_LLM_TEMPERATURE))),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", str(Constants.DEFAULT_LLM_MAX_TOKENS))),
            max_iterations=int(os.getenv("MAX_ITERATIONS", str(Constants.DEFAULT_MAX_ITERATIONS))),
            brain_false_limit=int(os.getenv("BRAIN_FALSE_LIMIT", str(Constants.BRAIN_FALSE_LIMIT))),
            nerves_false_limit=int(os.getenv("NERVES_FALSE_LIMIT", str(Constants.NERVES_FALSE_LIMIT))),
            planning_timeout=int(os.getenv("PLANNING_TIMEOUT", str(Constants.DEFAULT_PLANNING_TIMEOUT))),
            domain_name=os.getenv("DOMAIN_NAME", Constants.DEFAULT_DOMAIN_NAME),
            data_output_dir=os.getenv("DATA_OUTPUT_DIR", Constants.DATA_OUTPUT_DIR),
            max_data_points_per_file=int(os.getenv("MAX_DATA_POINTS_PER_FILE", str(Constants.MAX_DATA_POINTS_PER_FILE))),
        )
    
    def validate(self) -> bool:
        """
        验证配置是否有效
        
        :return: 是否有效
        """
        errors = []
        
        # 检查必要配置
        if not self.llm_api_key:
            errors.append("LLM API密钥未设置")
        
        # 检查路径是否存在
        if not os.path.exists(self.project_root):
            errors.append(f"项目根目录不存在: {self.project_root}")
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def validate_critical(self) -> bool:
        """
        验证关键配置（只检查会导致系统崩溃的配置）
        
        :return: 是否有效
        """
        # 只检查最关键的配置
        if not self.llm_api_key:
            print("❌ 关键配置缺失: LLM API密钥未设置")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_root": self.project_root,
            "llm_api_key": "***" if self.llm_api_key else "",
            "llm_base_url": self.llm_base_url,
            "llm_model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "max_iterations": self.max_iterations,
            "brain_false_limit": self.brain_false_limit,
            "nerves_false_limit": self.nerves_false_limit,
            "planning_timeout": self.planning_timeout,
            "domain_name": self.domain_name,
            "data_output_dir": self.data_output_dir,
            "max_data_points_per_file": self.max_data_points_per_file,
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        config_dict = self.to_dict()
        lines = ["CoT数据生成器配置:"]
        for key, value in config_dict.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)