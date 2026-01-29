"""服务注册表 - 管理所有服务的创建和依赖关系"""
from typing import Dict, Any, Callable, Type, Optional
from interface.llm import ILLM
from interface.storage import IStorage
from interface.planner import IPlanner
from interface.executor import IExecutor
from interface.translator import ITranslator
from interface.domain_expert import IDomainExpert
from interface.pddl_modifier import IPDDLModifier
from interface.sandbox_manager import ISandboxManager
from config.settings import Settings


class ServiceRegistry:
    """服务注册表 - 管理所有服务的创建和依赖"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        
    def register_factory(self, service_name: str, factory: Callable):
        """注册服务工厂
        
        :param service_name: 服务名称
        :param factory: 工厂函数，返回服务实例
        """
        self._factories[service_name] = factory
        
    def register_singleton(self, service_name: str, instance: Any):
        """注册单例服务
        
        :param service_name: 服务名称
        :param instance: 服务实例
        """
        self._singletons[service_name] = instance
        
    def get(self, service_name: str, **kwargs) -> Any:
        """获取服务实例
        
        :param service_name: 服务名称
        :param kwargs: 传递给工厂函数的参数
        :return: 服务实例
        """
        # 首先检查单例
        if service_name in self._singletons:
            return self._singletons[service_name]
            
        # 然后检查工厂
        if service_name in self._factories:
            factory = self._factories[service_name]
            return factory(**kwargs)
            
        raise KeyError(f"服务未注册: {service_name}")
        
    def has(self, service_name: str) -> bool:
        """检查服务是否已注册
        
        :param service_name: 服务名称
        :return: 是否已注册
        """
        return service_name in self._singletons or service_name in self._factories
        
    def clear(self):
        """清空所有注册的服务"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        
    @staticmethod
    def create_default_registry(config: Settings) -> 'ServiceRegistry':
        """创建默认的服务注册表
        
        :param config: 配置对象
        :return: 服务注册表实例
        """
        registry = ServiceRegistry()
        
        # 注册配置
        registry.register_singleton('config', config)
        
        # 注册LLM工厂
        def create_llm():
            from infrastructure.llm.deepseek_client import DeepSeekClient
            return DeepSeekClient(
                api_key=config.llm_api_key,
                base_url=config.llm_base_url,
                model=config.llm_model
            )
        registry.register_factory('llm', create_llm)
        
        # 注册存储工厂
        def create_storage():
            from infrastructure.storage.file_storage import FileStorage
            return FileStorage(config=config)
        registry.register_factory('storage', create_storage)
        
        # 注册规划器工厂
        def create_planner():
            from infrastructure.planner.lama_planner import LAMAPlanner
            return LAMAPlanner(config=config)
        registry.register_factory('planner', create_planner)
        
        # 注册执行器工厂
        def create_executor():
            from infrastructure.executor.mcp_executor import MCPActionExecutor
            server_args = config.mcp_server_args.strip().split() if config.mcp_server_args.strip() else ["mcp_server_structured.py"]
            return MCPActionExecutor(
                storage_path=config.storage_path,
                server_command=config.mcp_server_command,
                server_args=server_args
            )
        registry.register_factory('executor', create_executor)
        
        # 注册领域专家工厂
        def create_domain_expert():
            from infrastructure.domain.file_management_expert import FileManagementExpert
            return FileManagementExpert(config=config)
        registry.register_factory('domain_expert.file_management', create_domain_expert)
        
        # 注册翻译器工厂
        def create_translator():
            from infrastructure.translator.pddl_translator import PDDLTranslator
            domain_experts = {
                "file_management": registry.get('domain_expert.file_management')
            }
            return PDDLTranslator(
                llm=registry.get('llm'),
                storage=registry.get('storage'),
                domain_experts=domain_experts,
                config=config
            )
        registry.register_factory('translator', create_translator)
        
        # 注册PDDL修改器工厂
        def create_pddl_modifier():
            from infrastructure.pddl.pddl_modifier import PDDLModifier
            return PDDLModifier(config=config)
        registry.register_factory('pddl_modifier', create_pddl_modifier)
        
        # 注册沙盒管理器工厂
        def create_sandbox_manager():
            from infrastructure.sandbox.sandbox_manager import SandboxManager
            return SandboxManager(config=config)
        registry.register_factory('sandbox_manager', create_sandbox_manager)
        
        return registry


# 工具函数：支持自定义实现注册
def register_custom_llm(registry: ServiceRegistry, llm_class, **kwargs):
    """注册自定义LLM实现
    
    :param registry: 服务注册表
    :param llm_class: LLM实现类
    :param kwargs: 传递给构造函数的参数
    """
    def create_custom_llm():
        return llm_class(**kwargs)
    registry.register_factory('llm', create_custom_llm)


def register_custom_planner(registry: ServiceRegistry, planner_class, **kwargs):
    """注册自定义规划器实现
    
    :param registry: 服务注册表
    :param planner_class: 规划器实现类
    :param kwargs: 传递给构造函数的参数
    """
    def create_custom_planner():
        return planner_class(**kwargs)
    registry.register_factory('planner', create_custom_planner)


def register_custom_executor(registry: ServiceRegistry, executor_class, **kwargs):
    """注册自定义执行器实现
    
    :param registry: 服务注册表
    :param executor_class: 执行器实现类
    :param kwargs: 传递给构造函数的参数
    """
    def create_custom_executor():
        return executor_class(**kwargs)
    registry.register_factory('executor', create_custom_executor)


def register_custom_storage(registry: ServiceRegistry, storage_class, **kwargs):
    """注册自定义存储实现
    
    :param registry: 服务注册表
    :param storage_class: 存储实现类
    :param kwargs: 传递给构造函数的参数
    """
    def create_custom_storage():
        return storage_class(**kwargs)
    registry.register_factory('storage', create_custom_storage)


# 测试支持
def create_test_registry(config: Optional[Settings] = None):
    """创建测试用的服务注册表
    
    :param config: 可选的配置对象，如果为None则创建默认配置
    :return: 服务注册表实例
    """
    from unittest.mock import Mock
    
    if config is None:
        from config.settings import Settings
        config = Settings.load_from_env()
    
    registry = ServiceRegistry()
    registry.register_singleton('config', config)
    
    # 注册mock服务
    registry.register_singleton('llm', Mock(spec=ILLM))
    registry.register_singleton('planner', Mock(spec=IPlanner))
    registry.register_singleton('executor', Mock(spec=IExecutor))
    registry.register_singleton('storage', Mock(spec=IStorage))
    registry.register_singleton('translator', Mock(spec=ITranslator))
    registry.register_singleton('domain_expert.file_management', Mock(spec=IDomainExpert))
    registry.register_singleton('pddl_modifier', Mock(spec=IPDDLModifier))
    registry.register_singleton('sandbox_manager', Mock(spec=ISandboxManager))
    
    return registry