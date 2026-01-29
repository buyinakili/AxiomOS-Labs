"""依赖注入工厂 - 使用服务注册表解耦"""
from config.settings import Settings
from algorithm.kernel import AxiomLabsKernel
from app.service_registry import ServiceRegistry


class AxiomLabsFactory:
    """AxiomLabs系统工厂 - 使用服务注册表解耦具体实现"""

    @staticmethod
    def create_kernel(config: Settings) -> AxiomLabsKernel:
        """
        创建AxiomLabs内核

        :param config: 配置对象
        :return: AxiomLabsKernel实例
        """
        # 验证配置
        config.validate()

        # 创建服务注册表
        registry = ServiceRegistry.create_default_registry(config)

        # 从注册表获取服务
        translator = registry.get('translator')
        planner = registry.get('planner')
        executor = registry.get('executor')
        storage = registry.get('storage')

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
    def create_kernel_with_registry(registry: ServiceRegistry) -> AxiomLabsKernel:
        """
        使用自定义服务注册表创建内核

        :param registry: 服务注册表实例
        :return: AxiomLabsKernel实例
        """
        # 从注册表获取配置
        config = registry.get('config')
        config.validate()

        # 从注册表获取服务
        translator = registry.get('translator')
        planner = registry.get('planner')
        executor = registry.get('executor')
        storage = registry.get('storage')

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
        
        # 创建服务注册表
        registry = ServiceRegistry.create_default_registry(config)
        
        # 替换自定义实现
        from app.service_registry import (
            register_custom_llm, register_custom_planner,
            register_custom_executor, register_custom_storage
        )
        
        if llm_class is not None:
            register_custom_llm(registry, llm_class, **kwargs.get('llm_kwargs', {}))
            
        if planner_class is not None:
            register_custom_planner(registry, planner_class, **kwargs.get('planner_kwargs', {}))
            
        if executor_class is not None:
            register_custom_executor(registry, executor_class, **kwargs.get('executor_kwargs', {}))
            
        if storage_class is not None:
            register_custom_storage(registry, storage_class, **kwargs.get('storage_kwargs', {}))
        
        # 使用自定义注册表创建内核
        return AxiomLabsFactory.create_kernel_with_registry(registry)

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
