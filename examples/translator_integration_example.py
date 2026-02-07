#!/usr/bin/env python3
"""
Translator层集成示例

展示如何在CoT数据生成器中使用Brain/Nerves环境事实转换器。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.translator import (
    Nerves2BrainTranslator,
    Brain2NervesTranslator,
)


def demonstrate_translator_integration():
    """演示Translator层集成"""
    print("=" * 60)
    print("Translator层集成示例")
    print("=" * 60)
    
    # 创建转换器实例
    n2b_translator = Nerves2BrainTranslator()
    b2n_translator = Brain2NervesTranslator()
    
    # 示例1：Nerves层环境事实 -> Brain层逻辑谓词
    print("\n1. Nerves层到Brain层转换（降采样）")
    print("-" * 40)
    
    nerves_environment = {
        "(at file1 root)",
        "(at file2 root)",
        "(at file3 backup)",
        "(connected root backup)",
        "(has_admin_rights)",
        "(scanned root)",
        "(scanned backup)",
        "(is_created file1)",
        "(is_created file2)",
    }
    
    print("Nerves层环境事实（详细物理状态）:")
    for fact in sorted(nerves_environment):
        print(f"  {fact}")
    
    brain_environment = n2b_translator.translate(nerves_environment)
    
    print("\nBrain层环境事实（高层逻辑状态）:")
    for fact in sorted(brain_environment):
        print(f"  {fact}")
    
    # 示例2：Brain层逻辑谓词 -> Nerves层环境事实
    print("\n2. Brain层到Nerves层转换（具身化）")
    print("-" * 40)
    
    brain_plan = {
        "(located file1 root)",
        "(accessible root backup)",
        "(has_permission)",
        "(known root)",
    }
    
    print("Brain层逻辑谓词（抽象规划）:")
    for fact in sorted(brain_plan):
        print(f"  {fact}")
    
    nerves_plan = b2n_translator.translate(brain_plan)
    
    print("\nNerves层物理事实（具体执行）:")
    for fact in sorted(nerves_plan):
        print(f"  {fact}")
    
    # 示例3：带上下文的转换
    print("\n3. 带上下文的转换（错误语义升级）")
    print("-" * 40)
    
    nerves_facts_with_errors = {
        "(at file1 root)",
        "(has_admin_rights)",
    }
    
    context = {
        "errors": ["error_access_denied", "error_file_not_found"]
    }
    
    print("Nerves层事实（带错误上下文）:")
    for fact in sorted(nerves_facts_with_errors):
        print(f"  {fact}")
    print("错误上下文:", context["errors"])
    
    brain_facts_with_errors = n2b_translator.translate(
        nerves_facts_with_errors, 
        context
    )
    
    print("\nBrain层事实（错误语义升级）:")
    for fact in sorted(brain_facts_with_errors):
        print(f"  {fact}")
    
    # 示例4：在CoT数据生成流程中的集成
    print("\n4. 在CoT数据生成流程中的集成")
    print("-" * 40)
    
    # 模拟CoT数据生成流程
    user_task = "将root文件夹下的所有文件移动到backup文件夹"
    
    print(f"用户任务: {user_task}")
    print("\n模拟流程:")
    print("1. HypothalamusFilter判断任务路由")
    print("2. BrainLLM进行高层任务分解")
    print("3. TranslatorNerves2Brian转换环境事实")
    print("4. NervesLLM进行原子动作分解")
    print("5. TranslatorBrain2Nerves转换环境事实")
    print("6. 执行原子动作并记录数据")
    
    # 演示实际转换
    print("\n实际转换示例:")
    
    # 假设BrainLLM输出的任务链
    chain_of_mission = [
        "(scan root)",
        "(move file1 root backup)",
        "(move file2 root backup)",
    ]
    
    print(f"Brain层任务链: {chain_of_mission}")
    
    # 对于每个任务，需要转换环境事实
    for i, task in enumerate(chain_of_mission):
        print(f"\n任务 {i+1}: {task}")
        
        # 模拟当前环境状态
        if i == 0:
            current_nerves_env = nerves_environment
        else:
            # 模拟环境变化
            current_nerves_env = {
                "(at file2 root)",
                "(at file3 backup)",
                "(connected root backup)",
                "(has_admin_rights)",
                "(scanned root)",
                "(scanned backup)",
            }
        
        # 转换到Brain层环境
        current_brain_env = n2b_translator.translate(current_nerves_env)
        print(f"  Nerves环境 -> Brain环境: {len(current_brain_env)} 个事实")
        
        # 执行任务后，环境变化需要转换回Nerves层
        # 模拟任务执行后的Brain层环境
        updated_brain_env = current_brain_env.copy()
        if "move" in task:
            updated_brain_env.add("(located file1 backup)")
            updated_brain_env.discard("(located file1 root)")
        
        # 转换回Nerves层
        updated_nerves_env = b2n_translator.translate(updated_brain_env)
        print(f"  Brain环境 -> Nerves环境: {len(updated_nerves_env)} 个事实")
    
    print("\n" + "=" * 60)
    print("集成示例完成")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_translator_integration()