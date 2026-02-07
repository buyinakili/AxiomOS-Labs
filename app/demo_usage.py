#!/usr/bin/env python3
"""
第五步重构功能使用演示
运行: python demo_usage.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from algorithm.cot_data_generator import create_cot_data_generator
from infrastructure.llm.deepseek_client import DeepSeekClient
from infrastructure.planner.lama_planner import LAMAPlanner


def demo_basic_usage():
    """演示基本使用"""
    print("=" * 60)
    print("🎬 第五步重构功能 - 基本使用演示")
    print("=" * 60)
    
    # 1. 初始化
    print("\n1️⃣ 初始化系统组件...")
    settings = Settings.load_from_env()
    llm = DeepSeekClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model
    )
    planner = LAMAPlanner(config=settings)
    cot_generator = create_cot_data_generator(llm, planner)
    print("   ✅ 系统初始化完成")
    
    # 2. 演示简单任务
    print("\n2️⃣ 演示简单任务处理")
    simple_tasks = [
        "扫描当前文件夹",
        "创建一个测试文件夹",
        "获取管理员权限",
    ]
    
    for task in simple_tasks:
        print(f"\n   📋 任务: {task}")
        result = cot_generator.generate(user_task=task)
        
        if result.get("success", False):
            tasks = result.get("brain_layer", {}).get("chain_of_mission", [])
            print(f"     ✅ 成功 - 生成 {len(tasks)} 个Brain任务")
            for i, t in enumerate(tasks, 1):
                print(f"       {i}. {t}")
        else:
            print(f"     ❌ 失败")
            errors = result.get("error_messages", [])
            if errors:
                print(f"       错误: {errors[-1]}")
    
    # 3. 演示复杂任务
    print("\n3️⃣ 演示复杂任务处理")
    complex_task = "先扫描workspace文件夹，然后创建backup文件夹，最后将重要文件移动到backup"
    print(f"\n   📋 复杂任务: {complex_task}")
    
    result = cot_generator.generate(user_task=complex_task)
    
    if result.get("success", False):
        print(f"     ✅ 处理成功")
        
        # 显示详细结果
        brain_layer = result.get("brain_layer", {})
        if brain_layer:
            tasks = brain_layer.get("chain_of_mission", [])
            print(f"       生成的Brain任务链:")
            for i, task in enumerate(tasks, 1):
                print(f"         {i}. {task}")
            
            # 显示可达性检查
            reachability = brain_layer.get("mission_reachability", [])
            if reachability:
                # 安全处理可达性数据
                try:
                    if isinstance(reachability[0], (list, tuple)) and len(reachability[0]) > 0:
                        reachable = sum(1 for r in reachability if r[0])
                    else:
                        reachable = sum(1 for r in reachability if isinstance(r, bool) and r)
                    print(f"       可达性: {reachable}/{len(reachability)} 个任务可达")
                except:
                    print(f"       可达性检查: {len(reachability)} 个检查结果")
    else:
        print(f"     ❌ 处理失败")
    
    print("\n" + "=" * 60)
    print("🎉 基本使用演示完成")
    print("=" * 60)


def demo_advanced_features():
    """演示高级功能"""
    print("\n\n" + "=" * 60)
    print("🚀 第五步重构功能 - 高级功能演示")
    print("=" * 60)
    
    # 初始化
    settings = Settings.load_from_env()
    llm = DeepSeekClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model
    )
    planner = LAMAPlanner(config=settings)
    
    # 使用自定义配置
    config = {
        "brian_false_limit": 5,
        "nerves_false_limit": 5,
        "debug": False
    }
    
    cot_generator = create_cot_data_generator(llm, planner, config)
    
    # 演示错误恢复
    print("\n1️⃣ 演示错误恢复机制")
    problematic_task = "执行一个不可能完成的任务"
    print(f"\n   📋 问题任务: {problematic_task}")
    
    try:
        result = cot_generator.generate(user_task=problematic_task)
        print(f"    结果: {'成功' if result.get('success', False) else '失败'}")
        
        # 显示错误信息
        error_messages = result.get("error_messages", [])
        if error_messages:
            print(f"    错误记录 ({len(error_messages)} 个):")
            for err in error_messages:
                print(f"      - {err}")
    except Exception as e:
        print(f"    💥 异常: {e}")
    
    # 演示路由决策
    print("\n2️⃣ 演示路由决策")
    tasks_with_routes = [
        ("简单命令: ls", "Route_To_Nerves"),
        ("复杂规划: 创建项目结构并备份", "Route_To_Brain"),
        ("需要逻辑推理的任务", "Route_To_Brain"),
    ]
    
    for task_desc, expected_route in tasks_with_routes:
        print(f"\n   📋 {task_desc}")
        result = cot_generator.generate(user_task=task_desc)
        actual_route = result.get("route", "未知")
        print(f"     预期路由: {expected_route}")
        print(f"     实际路由: {actual_route}")
        print(f"     匹配: {'✅' if actual_route == expected_route else '❌'}")
    
    print("\n" + "=" * 60)
    print("🎊 高级功能演示完成")
    print("=" * 60)


def demo_integration():
    """演示集成使用"""
    print("\n\n" + "=" * 60)
    print("🔗 第五步重构功能 - 集成演示")
    print("=" * 60)
    
    # 模拟生产环境使用
    print("\n🎯 模拟生产环境使用场景")
    
    class ProductionTaskHandler:
        def __init__(self):
            settings = Settings.load_from_env()
            llm = DeepSeekClient(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model
            )
            planner = LAMAPlanner(config=settings)
            self.cot_generator = create_cot_data_generator(llm, planner)
            self.execution_history = []
        
        def handle_user_request(self, user_task):
            """处理用户请求"""
            print(f"\n   📥 收到用户请求: {user_task}")
            
            # 使用重构功能生成CoT数据
            cot_data = self.cot_generator.generate(user_task=user_task)
            
            # 记录执行历史
            self.execution_history.append({
                "task": user_task,
                "timestamp": "2026-02-07T07:20:00Z",
                "success": cot_data.get("success", False),
                "brain_tasks": cot_data.get("brain_layer", {}).get("chain_of_mission", []),
                "route": cot_data.get("route", "未知")
            })
            
            # 模拟执行
            if cot_data.get("success", False):
                print(f"     ✅ 规划成功")
                brain_tasks = cot_data.get("brain_layer", {}).get("chain_of_mission", [])
                print(f"       生成 {len(brain_tasks)} 个Brain级任务")
                
                # 这里可以添加实际执行逻辑（第六步功能）
                return {
                    "status": "success",
                    "plan": brain_tasks,
                    "cot_data": cot_data
                }
            else:
                print(f"     ❌ 规划失败")
                errors = cot_data.get("error_messages", [])
                if errors:
                    print(f"       错误: {errors[-1]}")
                
                return {
                    "status": "failed",
                    "error": errors[-1] if errors else "未知错误"
                }
    
    # 创建处理器并测试
    handler = ProductionTaskHandler()
    
    test_scenarios = [
        "用户请求扫描项目文件夹",
        "用户需要创建备份系统",
        "用户要求整理文档结构",
    ]
    
    for scenario in test_scenarios:
        result = handler.handle_user_request(scenario)
        print(f"     处理结果: {result['status']}")
    
    # 显示执行历史
    print(f"\n   📊 执行历史统计:")
    print(f"     总请求数: {len(handler.execution_history)}")
    success_count = sum(1 for h in handler.execution_history if h["success"])
    print(f"     成功数: {success_count}")
    print(f"     成功率: {success_count/len(handler.execution_history)*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("🏁 集成演示完成")
    print("=" * 60)


def main():
    """主演示函数"""
    print("第五步重构功能使用演示")
    print("=" * 60)
    
    try:
        # 运行各个演示
        demo_basic_usage()
        demo_advanced_features()
        demo_integration()
        
        print("\n\n🎉 所有演示完成！")
        print("\n📚 更多使用方式:")
        print("  1. 查看使用指南: app/使用指南_第五步重构功能.md")
        print("  2. 使用命令行工具: python app/cot_cli.py \"你的任务\"")
        print("  3. 运行测试: python app/test_step5_real.py")
        print("  4. 查看源代码: algorithm/cot_data_generator.py")
        
    except Exception as e:
        print(f"\n💥 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()