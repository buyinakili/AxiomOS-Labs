"""AxiomLabs指定学习模式入口"""
import sys
import os

# 添加项目根路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from app.training_factory import TrainingFactory


def main():
    """指定学习模式主函数"""
    print("="*80)
    print("AxiomLabs - 自演化智能操作系统")
    print("指定学习模式（用户指定任务）")
    print("="*80 + "\n")

    # 1. 获取用户指定的任务
    if len(sys.argv) > 1:
        task_goal = " ".join(sys.argv[1:])
    else:
        task_goal = input("请输入要学习的任务（如'学习重命名文件'）: ")

    if not task_goal:
        print("[Error] 未指定任务目标")
        return

    print(f"\n[Main] 用户指定学习目标: {task_goal}\n")

    # 2. 加载配置
    config = Settings.load_from_env()
    print(f"[Main] 配置加载完成\n")

    # 3. 创建训练组件
    components = TrainingFactory.create_training_components(config)

    # 4. 创建执行器
    base_executor = components['create_executor']()

    # 5. 生成指定任务
    print("[Trainer] 正在根据用户目标生成具体任务...")
    task_data = components['curriculum_algorithm'].propose_specific_task(
        task_goal=task_goal,
        executor=base_executor
    )

    if not task_data:
        print("[Trainer] 无法生成任务")
        return

    print(f"[Trainer] 任务生成成功: {task_data['goal']}")
    print(f"[Trainer] 理由: {task_data['rationale']}\n")

    # 6. 创建干净沙盒
    sandbox = components['sandbox_manager'].create_sandbox()
    print(f"[Trainer] 沙盒已创建: {sandbox}\n")

    # 7. 运行进化
    print("[Trainer] 启动进化循环...")
    result = components['evolution_algorithm'].evolve(
        user_goal=task_data['goal'],
        sandbox_manager=components['sandbox_manager'],
        task_data=task_data,
        llm=components['llm'],
        translator=components['create_translator'](),
        storage=components['storage']
    )

    # 8. 审计
    if result['success']:
        target_action = result.get('action_name', '').lower()
        actual_history = components['evolution_algorithm'].executor.get_execution_history()
        history = [h.lower() for h in actual_history]

        print(f"\n[Trainer] 正在审计执行路径...")
        print(f"  目标技能: {target_action}")
        print(f"  实际调用: {history}")

        if target_action and target_action not in history:
            print(f"[Trainer] \033[91m审计拦截：虚假进化！\033[0m")
            result['success'] = False

    # 9. 回归测试
    if result['success']:
        print(f"\n[Trainer] 任务训练成功！")
        print(f"[Trainer] 正在启动回归测试...")

        candidate_domain = components['sandbox_manager'].get_pddl_path()
        candidate_skill = result['skill_file_path']

        is_safe = components['regression_algorithm'].run_regression_suite(
            candidate_domain_path=candidate_domain,
            candidate_skill_path=candidate_skill,
            sandbox_manager=components['sandbox_manager'],
            llm=components['llm'],
            storage=components['storage'],
            translator_factory=components['create_translator'],
            planner_factory=components['create_planner'],
            executor_factory=components['create_executor']
        )

        if is_safe:
            print(f"\n[Trainer] 回归测试通过！批准晋升。")
            TrainingFactory.promote_skill(result, config)
            components['regression_algorithm'].save_new_test(task_data)

            print("\n" + "="*80)
            print("✓ 学习成功！新技能已添加到系统")
            print("="*80)
        else:
            print(f"\n[Trainer] 回归测试失败！拒绝晋升。")
            print("\n" + "="*80)
            print("✗ 学习失败（回归测试未通过）")
            print("="*80)
    else:
        print(f"\n[Trainer] 任务训练失败")
        print("\n" + "="*80)
        print("✗ 学习失败")
        print("="*80)


if __name__ == "__main__":
    main()
