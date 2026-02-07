#!/usr/bin/env python3
"""
命令行工具 - CoT数据生成器
用法: python cot_cli.py "扫描文件夹"
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from algorithm.cot_data_generator import create_cot_data_generator
from infrastructure.llm.deepseek_client import DeepSeekClient
from infrastructure.planner.lama_planner import LAMAPlanner


def init_system():
    """初始化系统组件"""
    print("🔄 初始化系统组件...")
    
    # 加载配置
    settings = Settings.load_from_env()
    print("  ✅ 配置加载完成")
    
    # 创建LLM客户端
    llm = DeepSeekClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model
    )
    print("  ✅ LLM客户端创建成功")
    
    # 创建规划器
    planner = LAMAPlanner(config=settings)
    print("  ✅ 规划器创建成功")
    
    # 创建CoT数据生成器
    cot_generator = create_cot_data_generator(llm, planner)
    print("  ✅ CoT数据生成器创建成功")
    
    return cot_generator


def process_task(cot_generator, user_task, verbose=False):
    """处理单个任务"""
    print(f"\n🎯 处理任务: {user_task}")
    print("-" * 40)
    
    try:
        result = cot_generator.generate(user_task=user_task)
        
        if result.get("success", False):
            print("✅ 任务处理成功")
            
            # 显示Brain任务链
            brain_tasks = result.get("brain_layer", {}).get("chain_of_mission", [])
            if brain_tasks:
                print(f"\n🧠 生成的Brain任务链 ({len(brain_tasks)} 个):")
                for i, task in enumerate(brain_tasks, 1):
                    print(f"  {i}. {task}")
            
            # 显示路由信息
            route = result.get("route", "未知")
            print(f"\n🛣️  路由决策: {route}")
            
            # 详细模式显示更多信息
            if verbose:
                print("\n📋 详细信息:")
                print(f"  开始环境: {result.get('brain_layer', {}).get('start_env', [])}")
                
                reachability = result.get("brain_layer", {}).get("mission_reachability", [])
                if reachability:
                    reachable = sum(1 for r in reachability if r[0])
                    print(f"  可达性检查: {reachable}/{len(reachability)} 个任务可达")
                
                nerves_layers = result.get("nerves_layers", [])
                if nerves_layers:
                    print(f"  Nerves层: {len(nerves_layers)} 个任务分解")
                    
        else:
            print("❌ 任务处理失败")
            errors = result.get("error_messages", [])
            if errors:
                print(f"\n⚠️ 错误信息:")
                for err in errors[-3:]:  # 显示最后3个错误
                    print(f"  - {err}")
        
        return result
        
    except Exception as e:
        print(f"💥 系统错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def batch_process(cot_generator, tasks_file, output_file=None):
    """批量处理任务"""
    print(f"\n📊 批量处理任务")
    print("=" * 40)
    
    # 读取任务文件
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ 文件不存在: {tasks_file}")
        return
    
    print(f"  读取到 {len(tasks)} 个任务")
    
    results = []
    success_count = 0
    
    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] 处理: {task[:50]}...")
        
        result = process_task(cot_generator, task, verbose=False)
        if result:
            results.append({
                "task": task,
                "success": result.get("success", False),
                "brain_tasks": result.get("brain_layer", {}).get("chain_of_mission", []),
                "route": result.get("route", "未知")
            })
            
            if result.get("success", False):
                success_count += 1
        
        # 进度显示
        print(f"  进度: {success_count}/{i} 成功 ({success_count/i*100:.1f}%)")
    
    # 输出统计
    print(f"\n📈 批量处理完成:")
    print(f"  总任务数: {len(tasks)}")
    print(f"  成功数: {success_count}")
    print(f"  成功率: {success_count/len(tasks)*100:.1f}%")
    
    # 保存结果
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"  结果已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
    
    return results


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description='CoT数据生成器命令行工具')
    parser.add_argument('task', nargs='?', help='要处理的任务描述')
    parser.add_argument('--batch', help='批量处理任务文件')
    parser.add_argument('--output', help='输出文件路径（JSON格式）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出模式')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    
    args = parser.parse_args()
    
    # 检查参数
    if not args.task and not args.batch:
        parser.print_help()
        print("\n示例:")
        print("  单个任务: python cot_cli.py \"扫描当前文件夹\"")
        print("  详细模式: python cot_cli.py \"创建test文件夹\" --verbose")
        print("  JSON输出: python cot_cli.py \"移动文件\" --json")
        print("  批量处理: python cot_cli.py --batch tasks.txt --output results.json")
        sys.exit(1)
    
    # 初始化系统
    cot_generator = init_system()
    
    if args.batch:
        # 批量处理模式
        batch_process(cot_generator, args.batch, args.output)
        
    else:
        # 单个任务模式
        result = process_task(cot_generator, args.task, args.verbose)
        
        if result and args.json:
            print("\n📋 JSON格式输出:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 40)
    print("🏁 处理完成")
    print("=" * 40)


if __name__ == "__main__":
    main()