"""AIOS生产模式入口"""
import sys
import os

# 添加项目根路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from app.factory import AIOSFactory


def main():
    """主函数"""
    print("="*80)
    print("AIOS - 自演化智能操作系统")
    print("生产模式")
    print("="*80 + "\n")

    # 1. 加载配置
    config = Settings.load_from_env()
    print(f"[Main] 配置加载完成")
    print(f"  - 项目路径: {config.project_root}")
    print(f"  - 存储路径: {config.storage_path}")
    print(f"  - LLM模型: {config.llm_model}\n")

    # 2. 创建系统
    kernel = AIOSFactory.create_kernel(config)

    # 3. 运行任务
    # 可以从命令行参数获取目标，或使用默认目标
    if len(sys.argv) > 1:
        user_goal = " ".join(sys.argv[1:])
    else:
        # 默认任务
        user_goal = "将root下的txt文件重命名为new.txt"

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