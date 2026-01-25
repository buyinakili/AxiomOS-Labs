"""训练模式依赖注入工厂"""
import os
import shutil
from config.settings import Settings

# 算法层
from algorithm.evolution import EvolutionAlgorithm
from algorithm.curriculum import CurriculumAlgorithm
from algorithm.regression import RegressionAlgorithm

# 工程层
from infrastructure.sandbox.sandbox_manager import SandboxManager
from infrastructure.pddl.pddl_modifier import PDDLModifier
from infrastructure.llm.deepseek_client import DeepSeekClient
from infrastructure.storage.file_storage import FileStorage
from infrastructure.planner.lama_planner import LAMAPlanner
from infrastructure.executor.action_executor import ActionExecutor
from infrastructure.translator.pddl_translator import PDDLTranslator
from infrastructure.domain.file_management_expert import FileManagementExpert

# 技能
from infrastructure.skills.filesystem_skills import (
    ScanSkill, MoveSkill, GetAdminSkill, CompressSkill
)


class TrainingFactory:
    """训练模式工厂 - 负责组装训练相关组件"""

    @staticmethod
    def create_training_components(config: Settings):
        """
        创建训练所需的所有组件

        :param config: 配置对象
        :return: 组件字典
        """
        config.validate()

        # 1. 创建LLM客户端
        llm = DeepSeekClient(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            model=config.llm_model
        )
        print(f"[Factory] LLM客户端已创建")

        # 2. 创建存储
        storage = FileStorage(
            project_root=config.project_root,
            storage_path=config.storage_path,
            tests_path=config.tests_path
        )
        print(f"[Factory] 存储已创建")

        # 3. 创建沙盒管理器
        sandbox_manager = SandboxManager(
            project_root=config.project_root,
            storage_path=config.storage_path,
            tests_path=config.tests_path
        )
        print(f"[Factory] 沙盒管理器已创建")

        # 4. 创建PDDL修改器
        pddl_modifier = PDDLModifier()
        print(f"[Factory] PDDL修改器已创建")

        # 5. 创建规划器
        planner = LAMAPlanner(
            downward_path=config.downward_path,
            temp_dir=config.temp_dir,
            timeout=config.planning_timeout
        )
        print(f"[Factory] 规划器已创建")

        # 6. 创建执行器工厂（用于创建新的执行器实例）
        def create_executor():
            executor = ActionExecutor(storage_path=config.storage_path)
            executor.register_skill(ScanSkill())
            executor.register_skill(MoveSkill())
            executor.register_skill(GetAdminSkill())
            executor.register_skill(CompressSkill())
            # 加载扩展技能
            TrainingFactory._load_extended_skills(executor, config.skills_path)
            return executor

        # 7. 创建翻译器工厂
        def create_translator():
            domain_experts = {
                "file_management": FileManagementExpert()
            }
            return PDDLTranslator(
                llm=llm,
                storage=storage,
                domain_experts=domain_experts
            )

        # 8. 创建规划器工厂
        def create_planner():
            return LAMAPlanner(
                downward_path=config.downward_path,
                temp_dir=config.temp_dir,
                timeout=config.planning_timeout
            )

        # 9. 创建进化算法
        executor_for_evolution = create_executor()
        evolution_algorithm = EvolutionAlgorithm(
            executor=executor_for_evolution,
            planner=planner,
            pddl_modifier=pddl_modifier,
            max_retries=config.max_evolution_retries
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
            registry_path=os.path.join(config.tests_path, "regression_registry.json")
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
        """加载扩展技能"""
        if not os.path.exists(skills_path):
            return

        for filename in os.listdir(skills_path):
            if filename.endswith("_skill.py") and filename != "base_skill.py":
                skill_file = os.path.join(skills_path, filename)
                executor.register_skill_from_file(skill_file)

    @staticmethod
    def promote_skill(skill_data: dict, config: Settings):
        """
        技能晋升逻辑：将沙盒验证成功的代码合并到主系统

        :param skill_data: 技能数据
        :param config: 配置对象
        """
        print(f"\n[Promoter] 正在晋升技能: {skill_data['action_name']} ...")

        # 1. 合并PDDL到tests/domain.pddl
        main_domain_path = os.path.join(config.tests_path, "domain.pddl")
        pddl_modifier = PDDLModifier()
        pddl_modifier.add_action(main_domain_path, skill_data['pddl_patch'])
        print(f"  - PDDL Action 已追加到主 Domain。")

        # 2. 移动Python文件到 infrastructure/skills/
        new_filename = f"{skill_data['action_name']}_skill.py"
        target_skill_path = os.path.join(config.skills_path, new_filename)

        shutil.copy(skill_data['skill_file_path'], target_skill_path)
        print(f"  - Python 脚本已部署到: {target_skill_path}")

        print("[Promoter] 晋升完成！重启系统后即可使用新能力。")
