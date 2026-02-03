"""训练模式依赖注入工厂 - 使用服务注册表解耦"""
import os
import shutil
from config.settings import Settings
from app.service_registry import ServiceRegistry

# 算法层
from algorithm.evolution import EvolutionAlgorithm
from algorithm.curriculum import CurriculumAlgorithm
from algorithm.regression import RegressionAlgorithm


class TrainingFactory:
    """训练模式工厂 - 使用服务注册表解耦具体实现"""

    @staticmethod
    def create_training_components(config: Settings):
        """
        创建训练所需的所有组件

        :param config: 配置对象
        :return: 组件字典
        """
        config.validate()

        # 创建服务注册表
        registry = ServiceRegistry.create_default_registry(config)

        # 从注册表获取核心服务
        llm = registry.get('llm')
        storage = registry.get('storage')
        sandbox_manager = registry.get('sandbox_manager')
        pddl_modifier = registry.get('pddl_modifier')
        planner = registry.get('planner')

        print(f"[Factory] 核心服务已创建")

        # 6. 创建执行器工厂（用于创建新的执行器实例）
        def create_executor():
            # 使用MCP执行器，与主工厂保持一致
            server_args = config.mcp_server_args.strip().split() if config.mcp_server_args.strip() else ["mcp_server_structured.py"]
            from infrastructure.executor.mcp_executor import MCPActionExecutor
            executor = MCPActionExecutor(
                storage_path=config.storage_path,
                server_command=config.mcp_server_command,
                server_args=server_args,
                config=config
            )
            # MCP执行器会自动从MCP服务器加载技能，无需手动注册
            return executor

        # 7. 创建翻译器工厂
        def create_translator():
            domain_experts = {
                config.domain_name: registry.get('domain_expert.file_management')
            }
            from infrastructure.translator.pddl_translator import PDDLTranslator
            return PDDLTranslator(
                llm=llm,
                storage=storage,
                domain_experts=domain_experts,
                config=config
            )

        # 8. 创建规划器工厂
        def create_planner():
            from infrastructure.planner.lama_planner import LAMAPlanner
            return LAMAPlanner(config=config)

        # 9. 创建进化算法
        executor_for_evolution = create_executor()
        evolution_algorithm = EvolutionAlgorithm(
            executor=executor_for_evolution,
            planner=planner,
            pddl_modifier=pddl_modifier,
            max_retries=config.max_evolution_retries,
            config=config
        )
        print(f"[Factory] 进化算法已创建")

        # 10. 创建课程算法
        curriculum_algorithm = CurriculumAlgorithm(
            llm=llm,
            storage=storage
        )
        print(f"[Factory] 课程算法已创建")

        # 11. 创建回归测试算法
        regression_algorithm = RegressionAlgorithm(
            registry_path=os.path.join(config.pddl_configs_path, "regression_registry.json")
        )
        print(f"[Factory] 回归测试算法已创建")

        print()

        return {
            "llm": llm,
            "storage": storage,
            "sandbox_manager": sandbox_manager,
            "pddl_modifier": pddl_modifier,
            "planner": planner,
            "evolution_algorithm": evolution_algorithm,
            "curriculum_algorithm": curriculum_algorithm,
            "regression_algorithm": regression_algorithm,
            "create_executor": create_executor,
            "create_translator": create_translator,
            "create_planner": create_planner,
            "config": config
        }

    @staticmethod
    def create_training_components_with_registry(registry: ServiceRegistry):
        """
        使用自定义服务注册表创建训练组件

        :param registry: 服务注册表实例
        :return: 组件字典
        """
        # 从注册表获取配置
        config = registry.get('config')
        config.validate()

        # 从注册表获取核心服务
        llm = registry.get('llm')
        storage = registry.get('storage')
        sandbox_manager = registry.get('sandbox_manager')
        pddl_modifier = registry.get('pddl_modifier')
        planner = registry.get('planner')

        print(f"[Factory] 核心服务已创建")

        # 创建执行器工厂
        def create_executor():
            # 使用MCP执行器，与主工厂保持一致
            server_args = config.mcp_server_args.strip().split() if config.mcp_server_args.strip() else ["mcp_server_structured.py"]
            from infrastructure.executor.mcp_executor import MCPActionExecutor
            executor = MCPActionExecutor(
                storage_path=config.storage_path,
                server_command=config.mcp_server_command,
                server_args=server_args,
                config=config
            )
            return executor

        # 创建翻译器工厂
        def create_translator():
            domain_experts = {
                config.domain_name: registry.get('domain_expert.file_management')
            }
            from infrastructure.translator.pddl_translator import PDDLTranslator
            return PDDLTranslator(
                llm=llm,
                storage=storage,
                domain_experts=domain_experts,
                config=config
            )

        # 创建规划器工厂
        def create_planner():
            from infrastructure.planner.lama_planner import LAMAPlanner
            return LAMAPlanner(config=config)

        # 创建进化算法
        executor_for_evolution = create_executor()
        evolution_algorithm = EvolutionAlgorithm(
            executor=executor_for_evolution,
            planner=planner,
            pddl_modifier=pddl_modifier,
            max_retries=config.max_evolution_retries,
            config=config
        )
        print(f"[Factory] 进化算法已创建")

        # 创建课程算法
        curriculum_algorithm = CurriculumAlgorithm(
            llm=llm,
            storage=storage
        )
        print(f"[Factory] 课程算法已创建")

        # 创建回归测试算法
        regression_algorithm = RegressionAlgorithm(
            registry_path=os.path.join(config.pddl_configs_path, "regression_registry.json")
        )
        print(f"[Factory] 回归测试算法已创建")

        print()

        return {
            "llm": llm,
            "storage": storage,
            "sandbox_manager": sandbox_manager,
            "pddl_modifier": pddl_modifier,
            "planner": planner,
            "evolution_algorithm": evolution_algorithm,
            "curriculum_algorithm": curriculum_algorithm,
            "regression_algorithm": regression_algorithm,
            "create_executor": create_executor,
            "create_translator": create_translator,
            "create_planner": create_planner,
            "config": config
        }

    @staticmethod
    def _load_extended_skills(executor, skills_path: str):
        """加载扩展技能（MCP执行器自动从服务器加载，此方法保留为空）"""
        # MCP执行器会自动从MCP服务器加载技能，无需手动加载
        pass

    @staticmethod
    def promote_skill(skill_data: dict, config: Settings):
        """
        技能晋升逻辑：将沙盒验证成功的代码合并到主系统

        :param skill_data: 技能数据
        :param config: 配置对象
        """
        print(f"\n[Promoter] 正在晋升技能: {skill_data['action_name']} ...")

        # 1. 合并PDDL到pddl_configs/domain.pddl
        main_domain_path = os.path.join(config.pddl_configs_path, "domain.pddl")
        
        # 使用服务注册表创建PDDL修改器
        registry = ServiceRegistry.create_default_registry(config)
        pddl_modifier = registry.get('pddl_modifier')
        
        pddl_modifier.add_action(main_domain_path, skill_data['pddl_patch'])
        print(f"  - PDDL Action 已追加到主 Domain。")

        # 2. 移动Python文件到 infrastructure/mcp_skills/ (MCP技能目录)
        new_filename = f"{skill_data['action_name']}_skill.py"
        # 使用MCP技能目录而不是本地技能目录
        mcp_skills_path = os.path.join(config.project_root, "infrastructure", "mcp_skills")
        os.makedirs(mcp_skills_path, exist_ok=True)
        target_skill_path = os.path.join(mcp_skills_path, new_filename)

        # 验证技能文件格式（确保是MCP格式）
        with open(skill_data['skill_file_path'], 'r', encoding='utf-8') as f:
            content = f.read()
            if 'MCPBaseSkill' not in content:
                print(f"  - 警告：技能文件可能不是MCP格式，但将继续复制")
            if 'BaseSkill' in content and 'MCPBaseSkill' not in content:
                print(f"  - 严重警告：技能文件使用旧版BaseSkill，可能无法被MCP服务器加载")

        shutil.copy(skill_data['skill_file_path'], target_skill_path)
        print(f"  - Python 脚本已部署到MCP技能目录: {target_skill_path}")
        print("  - 注意：需要重启MCP服务器才能加载新技能")

        print("[Promoter] 晋升完成！重启MCP服务器后即可使用新能力。")
