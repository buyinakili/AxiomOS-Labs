"""纯工厂模式 - 直接创建系统组件"""
from config.settings import Settings
from algorithm.kernel import AxiomLabsKernel
from infrastructure.llm.deepseek_client import DeepSeekClient
from infrastructure.storage.file_storage import FileStorage
from infrastructure.planner.lama_planner import LAMAPlanner
from infrastructure.executor.mcp_executor import MCPActionExecutor
from infrastructure.domain.file_management_expert import FileManagementExpert
from infrastructure.translator.pddl_translator import PDDLTranslator
from infrastructure.pddl.pddl_modifier import PDDLModifier
from infrastructure.sandbox.sandbox_manager import SandboxManager


class AxiomLabsFactory:
    """AxiomLabs系统工厂 - 纯工厂模式实现"""
    
    @staticmethod
    def create_llm(config: Settings) -> DeepSeekClient:
        """创建LLM客户端"""
        return DeepSeekClient(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            model=config.llm_model
        )
    
    @staticmethod
    def create_storage(config: Settings) -> FileStorage:
        """创建文件存储"""
        return FileStorage(config=config)
    
    @staticmethod
    def create_planner(config: Settings) -> LAMAPlanner:
        """创建规划器"""
        return LAMAPlanner(config=config)
    
    @staticmethod
    def create_executor(config: Settings) -> MCPActionExecutor:
        """创建执行器"""
        server_args = config.mcp_server_args.strip().split() if config.mcp_server_args.strip() else ["infrastructure/mcp_server.py"]
        return MCPActionExecutor(
            storage_path=config.storage_path,
            server_command=config.mcp_server_command,
            server_args=server_args,
            config=config
        )
    
    @staticmethod
    def create_domain_expert(config: Settings) -> FileManagementExpert:
        """创建领域专家"""
        return FileManagementExpert(config=config)
    
    @staticmethod
    def create_pddl_modifier(config: Settings) -> PDDLModifier:
        """创建PDDL修改器"""
        return PDDLModifier(config=config)
    
    @staticmethod
    def create_sandbox_manager(config: Settings) -> SandboxManager:
        """创建沙盒管理器"""
        return SandboxManager(config=config)
    
    @staticmethod
    def create_translator(config: Settings, llm=None, storage=None, domain_expert=None) -> PDDLTranslator:
        """创建翻译器"""
        if llm is None:
            llm = AxiomLabsFactory.create_llm(config)
        if storage is None:
            storage = AxiomLabsFactory.create_storage(config)
        if domain_expert is None:
            domain_expert = AxiomLabsFactory.create_domain_expert(config)
        
        domain_experts = {
            config.domain_name: domain_expert
        }
        
        return PDDLTranslator(
            llm=llm,
            storage=storage,
            domain_experts=domain_experts,
            config=config
        )
    
    @staticmethod
    def create_kernel(config: Settings) -> AxiomLabsKernel:
        """
        创建AxiomLabs内核
        
        :param config: 配置对象
        :return: AxiomLabsKernel实例
        """
        # 验证配置
        config.validate()
        
        # 直接创建各个组件
        llm = AxiomLabsFactory.create_llm(config)
        storage = AxiomLabsFactory.create_storage(config)
        planner = AxiomLabsFactory.create_planner(config)
        executor = AxiomLabsFactory.create_executor(config)
        domain_expert = AxiomLabsFactory.create_domain_expert(config)
        translator = AxiomLabsFactory.create_translator(config, llm, storage, domain_expert)
        
        # 组装内核
        kernel = AxiomLabsKernel(
            translator=translator,
            planner=planner,
            executor=executor,
            storage=storage,
            config=config
        )
        
        # 简洁日志
        skill_count = len(executor.get_registered_skills())
        print(f"[Factory] 内核已创建 | LLM: {config.llm_model} | 执行器: MCP ({skill_count} 技能)")
        
        return kernel
    
    @staticmethod
    def create_custom_kernel(config: Settings, 
                            llm_class=None, 
                            planner_class=None, 
                            executor_class=None,
                            storage_class=None,
                            **kwargs) -> AxiomLabsKernel:
        """
        创建自定义内核，支持替换具体实现
        
        :param config: 配置对象
        :param llm_class: 自定义LLM实现类，如果为None则使用默认
        :param planner_class: 自定义规划器实现类，如果为None则使用默认
        :param executor_class: 自定义执行器实现类，如果为None则使用默认
        :param storage_class: 自定义存储实现类，如果为None则使用默认
        :param kwargs: 传递给自定义类的参数
        :return: AxiomLabsKernel实例
        """
        config.validate()
        
        # 创建自定义组件
        if llm_class is not None:
            llm = llm_class(**kwargs.get('llm_kwargs', {}))
        else:
            llm = AxiomLabsFactory.create_llm(config)
        
        if storage_class is not None:
            storage = storage_class(**kwargs.get('storage_kwargs', {}))
        else:
            storage = AxiomLabsFactory.create_storage(config)
        
        if planner_class is not None:
            planner = planner_class(**kwargs.get('planner_kwargs', {}))
        else:
            planner = AxiomLabsFactory.create_planner(config)
        
        if executor_class is not None:
            executor = executor_class(**kwargs.get('executor_kwargs', {}))
        else:
            executor = AxiomLabsFactory.create_executor(config)
        
        # 创建领域专家和翻译器
        domain_expert = AxiomLabsFactory.create_domain_expert(config)
        translator = AxiomLabsFactory.create_translator(config, llm, storage, domain_expert)
        
        # 组装内核
        kernel = AxiomLabsKernel(
            translator=translator,
            planner=planner,
            executor=executor,
            storage=storage,
            config=config
        )
        
        # 简洁日志
        skill_count = len(executor.get_registered_skills())
        custom_components = []
        if llm_class is not None:
            custom_components.append("LLM")
        if planner_class is not None:
            custom_components.append("规划器")
        if executor_class is not None:
            custom_components.append("执行器")
        if storage_class is not None:
            custom_components.append("存储")
        
        if custom_components:
            print(f"[Factory] 自定义内核已创建 | 自定义组件: {', '.join(custom_components)} | 技能: {skill_count}")
        else:
            print(f"[Factory] 内核已创建 | LLM: {config.llm_model} | 执行器: MCP ({skill_count} 技能)")
        
        return kernel
    
    @staticmethod
    def _load_extended_skills(executor, skills_path: str):
        """
        加载扩展技能
        
        :param executor: 执行器实例
        :param skills_path: 技能目录路径
        """
        import os
        
        if not os.path.exists(skills_path):
            return
        
        for filename in os.listdir(skills_path):
            if filename.endswith("_skill.py") and filename != "base_skill.py":
                skill_file = os.path.join(skills_path, filename)
                executor.register_skill_from_file(skill_file)
