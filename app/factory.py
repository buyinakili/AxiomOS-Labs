"""依赖注入工厂"""
from config.settings import Settings
from algorithm.kernel import AIOSKernel

# 接口
from interface.translator import ITranslator
from interface.planner import IPlanner
from interface.executor import IExecutor
from interface.storage import IStorage
from interface.llm import ILLM
from interface.domain_expert import IDomainExpert

# 实现
from infrastructure.llm.deepseek_client import DeepSeekClient
from infrastructure.storage.file_storage import FileStorage
from infrastructure.planner.lama_planner import LAMAPlanner
from infrastructure.executor.action_executor import ActionExecutor
from infrastructure.executor.mcp_executor import MCPActionExecutor
from infrastructure.translator.pddl_translator import PDDLTranslator
from infrastructure.domain.file_management_expert import FileManagementExpert

# 技能
from infrastructure.skills.filesystem_skills import (
    ScanSkill, MoveSkill, GetAdminSkill, CompressSkill
)


class AIOSFactory:
    """AIOS系统工厂 - 负责组装所有组件"""

    @staticmethod
    def create_kernel(config: Settings) -> AIOSKernel:
        """
        创建AIOS内核

        :param config: 配置对象
        :return: AIOSKernel实例
        """
        # 验证配置
        config.validate()

        # 1. 创建LLM客户端
        llm: ILLM = DeepSeekClient(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            model=config.llm_model
        )
        print(f"[Factory] LLM客户端已创建")

        # 2. 创建存储
        storage: IStorage = FileStorage(
            project_root=config.project_root,
            storage_path=config.storage_path,
            tests_path=config.tests_path
        )
        print(f"[Factory] 存储已创建")

        # 3. 创建规划器
        planner: IPlanner = LAMAPlanner(
            downward_path=config.downward_path,
            temp_dir=config.temp_dir,
            timeout=config.planning_timeout
        )
        print(f"[Factory] 规划器已创建")

        # 4. 创建执行器
        executor: IExecutor
        if config.use_mcp:
            # 使用 MCP 执行器
            server_args = config.mcp_server_args.strip().split() if config.mcp_server_args.strip() else ["mcp_server_structured.py"]
            print(f"[Factory] 使用 MCP 执行器 (服务器: {config.mcp_server_command} {' '.join(server_args)})")
            executor = MCPActionExecutor(
                storage_path=config.storage_path,
                server_command=config.mcp_server_command,
                server_args=server_args
            )
        else:
            # 使用本地技能执行器
            executor = ActionExecutor(
                storage_path=config.storage_path
            )

            # 注册基础技能
            executor.register_skill(ScanSkill())
            executor.register_skill(MoveSkill())
            executor.register_skill(GetAdminSkill())
            executor.register_skill(CompressSkill())

            # 动态加载扩展技能
            AIOSFactory._load_extended_skills(executor, config.skills_path)

        print(f"[Factory] 执行器已创建，注册了 {len(executor.get_registered_skills())} 个技能")

        # 5. 创建领域专家
        domain_experts = {
            "file_management": FileManagementExpert()
        }
        print(f"[Factory] 领域专家已注册")

        # 6. 创建翻译器
        translator: ITranslator = PDDLTranslator(
            llm=llm,
            storage=storage,
            domain_experts=domain_experts
        )
        print(f"[Factory] 翻译器已创建")

        # 7. 组装内核
        kernel = AIOSKernel(
            translator=translator,
            planner=planner,
            executor=executor,
            storage=storage,
            max_iterations=config.max_iterations
        )
        print(f"[Factory] 内核已创建\n")

        return kernel

    @staticmethod
    def _load_extended_skills(executor: IExecutor, skills_path: str):
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
