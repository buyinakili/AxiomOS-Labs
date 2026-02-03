"""AxiomLabs生产模式入口"""
import sys
import os

# 添加项目根路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from app.factory import AxiomLabsFactory


def print_usage():
    """打印用法"""
    print("用法: python main_demo.py [目标描述] [选项]")
    print()
    print("选项:")
    print("  --debug-prompt    显示发送给LLM的提示词（调试用）")
    print("  --help            显示此帮助信息")
    print()
    print("示例:")
    print("  python main_demo.py \"将root下的txt文件移动到backup文件夹下\"")
    print("  python main_demo.py --debug-prompt")
    print("  python main_demo.py \"扫描root文件夹\" --debug-prompt")


def main():
    """主函数"""
    # 解析命令行参数
    args = sys.argv[1:]
    debug_prompt = False
    user_goal = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--debug-prompt":
            debug_prompt = True
            i += 1
        elif arg == "--help":
            print_usage()
            return
        elif arg.startswith("--"):
            print(f"未知选项: {arg}")
            print_usage()
            sys.exit(1)
        else:
            # 非选项参数视为目标描述
            if user_goal is None:
                user_goal = arg
                # 如果目标描述包含空格，将剩余部分合并
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    remaining = args[i + 1:]
                    user_goal = " ".join([arg] + remaining)
                    break
            i += 1

    # 设置调试环境变量
    if debug_prompt:
        os.environ["AXIOMLABS_DEBUG_PROMPT"] = "1"
        print("[Main] 调试模式已启用：将显示发送给LLM的提示词")
    else:
        # 确保环境变量未设置（避免之前运行的影响）
        os.environ.pop("AXIOMLABS_DEBUG_PROMPT", None)

    print("="*80)
    print("AxiomLabs - 自演化智能操作系统")
    print("生产模式")
    print("="*80 + "\n")

    # 1. 加载配置
    config = Settings.load_from_env()
    print(f"[Main] 配置加载完成")
    print(f"  - 项目路径: {config.project_root}")
    print(f"  - 存储路径: {config.storage_path}")
    print(f"  - LLM模型: {config.llm_model}\n")

    # 2. 创建系统
    kernel = AxiomLabsFactory.create_kernel(config)

    # 3. 运行任务
    if user_goal is None:
        # 默认任务
        user_goal = "将root下的txt文件移动到backup文件夹下，然后把backup下的good.txt删除"

    print(f"[Main] 开始执行任务: {user_goal}\n")
    print("="*80 + "\n")

    success = kernel.run(user_goal)

    print("\n" + "="*80)
    if success:
        print("[Main] ✓ 任务完成")
    else:
        print("[Main] ✗ 任务失败")
    print("="*80)


if __name__ == "__main__":
    main()
#python3 app/main_demo.py