"""AxiomLabs自主学习模式入口"""
import sys
import os
import argparse

# 添加项目根路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from app.training_factory import TrainingFactory


def parse_arguments():
    """解析命令行参数"""
    # 检查环境变量中的默认轮次
    env_rounds = os.getenv("TRAINING_ROUNDS")
    default_auto_rounds = 3  # 自动模式默认3轮
    if env_rounds and env_rounds.isdigit():
        default_auto_rounds = int(env_rounds)
    
    parser = argparse.ArgumentParser(
        description='AxiomLabs自主学习模式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                     # 自动模式，学习3次（或TRAINING_ROUNDS环境变量）
  %(prog)s --task "删除文件"     # 指定任务模式，学习"删除文件"任务（默认1轮）
  %(prog)s --task "移动文件" --rounds 5  # 指定任务模式，重试5次
  %(prog)s --auto --rounds 10  # 自动模式，学习10次
        """
    )
    
    # 模式选择
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--auto', '-a',
        action='store_true',
        default=True,
        help='自动模式：LLM自动出题（默认）'
    )
    mode_group.add_argument(
        '--task', '-t',
        type=str,
        help='指定任务模式：学习指定的任务（默认1轮）'
    )
    
    # 其他参数
    parser.add_argument(
        '--rounds', '-r',
        type=int,
        default=None,  # 设置为None，后面根据模式决定默认值
        help='训练轮次/重试次数（自动模式默认：3，指定任务模式默认：1，可从TRAINING_ROUNDS环境变量设置自动模式默认值）'
    )
    
    # 如果提供了未解析的参数，可能是任务描述（向后兼容）
    parser.add_argument(
        'extra_args',
        nargs='*',
        help=argparse.SUPPRESS
    )
    
    args = parser.parse_args()
    
    # 处理默认轮次逻辑
    if args.rounds is None:
        # 用户没有指定--rounds参数
        if args.task:
            # 指定任务模式：默认1轮
            args.rounds = 1
        else:
            # 自动模式：使用环境变量或默认3轮
            args.rounds = default_auto_rounds
    # 如果用户指定了--rounds，就使用用户指定的值
    
    return args


def run_training_round(components, config, task_data, round_num, total_rounds):
    """运行一轮训练"""
    print(f"\n{'='*30} 第 {round_num}/{total_rounds} 轮训练 {'='*30}\n")

    # 创建新的执行器（使用已设置的环境变量）
    base_executor = components['create_executor']()
    base_executor.clear_execution_history()

    # 2. 使用已创建的沙盒（不再重复创建）
    sandbox_path = components['sandbox_manager'].get_sandbox_path()
    print(f"[Trainer] 使用已创建的沙盒: {sandbox_path}\n")

    # 3. 运行进化
    print("[Trainer] 启动进化循环...")
    result = components['evolution_algorithm'].evolve(
        user_goal=task_data['goal'],
        sandbox_manager=components['sandbox_manager'],
        task_data=task_data,
        llm=components['llm'],
        translator=components['create_translator'](),
        storage=components['storage']
    )

    # 4. 审计
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
            result['error'] = f"Action '{target_action}' 未被调用"

    # 5. 回归测试
    if result['success']:
        print(f"\n[Trainer] 任务 '{task_data['goal']}' 训练成功！")
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
            print(f"\n✓ 第 {round_num}/{total_rounds} 轮训练成功完成\n")
            return True
        else:
            print(f"\n[Trainer] 回归测试失败！拒绝晋升。")
            print(f"\n✗ 第 {round_num}/{total_rounds} 轮训练失败\n")
            return False
    else:
        print(f"\n[Trainer] 任务 '{task_data['goal']}' 训练失败。")
        print(f"\n✗ 第 {round_num}/{total_rounds} 轮训练失败\n")
        return False


def main():
    """自主学习模式主函数"""
    args = parse_arguments()
    
    # 处理向后兼容：如果extra_args有内容且没有--task参数，则将其作为任务
    if args.extra_args and not args.task:
        args.task = " ".join(args.extra_args)
        args.auto = False
    
    # 确定模式
    if args.task:
        mode = "指定任务"
        mode_desc = f"指定任务模式：学习 '{args.task}'"
    else:
        mode = "自动"
        mode_desc = "自动模式：LLM自动出题"
    
    print("="*80)
    print("AxiomLabs - 自演化智能操作系统")
    print("自主学习模式")
    print("="*80 + "\n")
    print(f"[模式] {mode_desc}")
    print(f"[轮次] 计划训练 {args.rounds} 轮\n")
    print("="*80 + "\n")

    # 1. 加载配置
    config = Settings.load_from_env()
    print(f"[Main] 配置加载完成\n")

    # 2. 创建训练组件
    components = TrainingFactory.create_training_components(config)
    
    success_count = 0
    
    for round_num in range(1, args.rounds + 1):
        # 1. 先创建沙盒环境
        print(f"\n[Trainer] 正在为第 {round_num}/{args.rounds} 轮创建沙盒环境...")
        sandbox = components['sandbox_manager'].create_sandbox()
        
        # 2. 设置环境变量，确保MCP服务器能正确识别沙盒路径
        sandbox_storage_path = components['sandbox_manager'].get_storage_path()
        sandbox_skills_dir = os.path.join(components['sandbox_manager'].get_sandbox_path(), "skills")
        
        os.environ['SANDBOX_STORAGE_PATH'] = sandbox_storage_path
        os.environ['SANDBOX_MCP_SKILLS_DIR'] = sandbox_skills_dir
        
        print(f"[Trainer] 环境变量已设置:")
        print(f"  - SANDBOX_STORAGE_PATH: {sandbox_storage_path}")
        print(f"  - SANDBOX_MCP_SKILLS_DIR: {sandbox_skills_dir}")
        
        # 3. 创建执行器（使用正确的环境变量）
        base_executor = components['create_executor']()
        base_executor.clear_execution_history()
        
        # 4. 获取任务数据
        if args.task:
            # 指定任务模式
            print(f"[Trainer] 正在根据用户目标生成具体任务...")
            task_data = components['curriculum_algorithm'].propose_specific_task(
                task_goal=args.task,
                executor=base_executor
            )
        else:
            # 自动模式
            print("[Trainer] 正在请求 LLM 出题...")
            task_data = components['curriculum_algorithm'].propose_next_task(base_executor)
        
        if not task_data:
            print("[Trainer] 无法生成任务，跳过本轮。")
            continue
        
        print(f"[Trainer] 任务生成成功: {task_data['goal']}")
        print(f"[Trainer] 理由: {task_data['rationale']}\n")
        
        # 5. 运行训练轮次（传入已创建的沙盒信息）
        if run_training_round(components, config, task_data, round_num, args.rounds):
            success_count += 1

    print("\n" + "="*80)
    print(f"[System] 自主学习模式已完成")
    print(f"  成功轮次: {success_count}/{args.rounds}")
    print("="*80)


if __name__ == "__main__":
    main()
#python3 app/auto_trainer.py
#python3 app/auto_trainer.py --task "将root下的txt文件重命名为new.txt"