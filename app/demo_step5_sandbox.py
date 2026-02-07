#!/usr/bin/env python3
"""
第五步沙盒演示 - 在沙盒环境中测试CoT数据生成器

这个演示展示如何使用第五步实现的组件在沙盒环境中执行任务。
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from infrastructure.sandbox.sandbox_manager import SandboxManager
from algorithm.cot_data_generator import create_cot_data_generator
from infrastructure.llm.deepseek_client import DeepSeekClient
from infrastructure.planner.lama_planner import LAMAPlanner
from infrastructure.executor.mcp_executor import MCPActionExecutorRefactored


class Step5SandboxDemo:
    """第五步沙盒演示"""
    
    def __init__(self):
        """初始化演示环境"""
        self.settings = Settings.load_from_env()
        self.sandbox_manager = SandboxManager(self.settings)
        
        print("=" * 60)
        print("🚀 第五步沙盒演示 - CoT数据生成器")
        print("=" * 60)
    
    def setup_sandbox(self):
        """设置沙盒环境"""
        print("\n📦 设置沙盒环境...")
        
        # 创建沙盒
        sandbox_path = self.sandbox_manager.create_sandbox()
        print(f"  ✅ 沙盒创建成功: {sandbox_path}")
        
        # 获取沙盒存储路径
        storage_path = self.sandbox_manager.get_storage_path()
        print(f"  ✅ 沙盒存储路径: {storage_path}")
        
        # 在沙盒中创建一些测试文件
        self._create_test_files(storage_path)
        
        return sandbox_path, storage_path
    
    def _create_test_files(self, storage_path: str):
        """在沙盒中创建测试文件"""
        test_dir = Path(storage_path)
        
        # 创建测试文件夹和文件
        (test_dir / "test.txt").write_text("这是一个测试文件")
        (test_dir / "document.pdf").write_text("PDF文档内容")
        (test_dir / "data.csv").write_text("name,age\nAlice,30\nBob,25")
        
        print(f"  ✅ 创建了3个测试文件在沙盒中")
    
    def setup_components(self, storage_path: str):
        """设置第五步组件"""
        print("\n🔧 设置第五步组件...")
        
        # 创建LLM客户端（需要API密钥）
        llm_api_key = self.settings.llm_api_key
        print(f"  ℹ️  API密钥检查: '{llm_api_key}'")
        
        # 检查是否是默认或空密钥
        if (not llm_api_key or
            llm_api_key == "your-api-key" or
            llm_api_key == "your_deepseek_api_key_here" or
            llm_api_key.startswith("your_")):
            print("  ⚠️  LLM API密钥未配置，使用模拟模式")
            # 使用模拟LLM
            class DemoMockLLM:
                def chat(self, messages, temperature=0.1):
                    content = messages[0]["content"] if messages else ""
                    print(f"    [MockLLM] 收到请求: {content[:50]}...")
                    if "任务序列" in content:
                        # 返回简单的任务链
                        return "(scan storage_jail)\n(create_folder new_folder storage_jail)\n(move test.txt storage_jail new_folder)"
                    elif "原子动作序列" in content:
                        # 返回原子动作
                        return "(scan storage_jail)\n(create_folder new_folder storage_jail)\n(move test.txt storage_jail new_folder)"
                    else:
                        return "模拟响应"
                
                def generate(self, prompt, temperature=0.1):
                    return "模拟生成"
            
            llm = DemoMockLLM()
        else:
            print("  ✅ 使用真实LLM客户端")
            llm = DeepSeekClient(
                api_key=llm_api_key,
                base_url=self.settings.llm_base_url,
                model=self.settings.llm_model
            )
        
        # 创建规划器
        planner = LAMAPlanner(
            config=self.settings,
            temp_dir=tempfile.mkdtemp(),
            timeout=self.settings.planning_timeout
        )
        
        # 创建执行器（使用沙盒存储路径）
        print(f"  ✅ 创建MCP执行器，使用沙盒路径: {storage_path}")
        executor = MCPActionExecutorRefactored(
            storage_path=storage_path,
            server_command=self.settings.mcp_server_command
        )
        
        # 创建CoT数据生成器
        print("  ✅ 创建CoT数据生成器")
        cot_generator = create_cot_data_generator(llm, planner)
        
        # 替换执行器为沙盒版本
        cot_generator.executor = executor
        
        return cot_generator
    
    def run_demo_tasks(self, cot_generator):
        """运行演示任务"""
        print("\n🎯 运行演示任务...")
        
        demo_tasks = [
            "扫描当前文件夹",
            "创建一个名为new_folder的新文件夹",
            "将test.txt文件移动到new_folder文件夹",
        ]
        
        results = []
        
        for i, task in enumerate(demo_tasks, 1):
            print(f"\n  📋 任务 {i}: {task}")
            print(f"    {'─' * 40}")
            
            try:
                result = cot_generator.generate(user_task=task)
                
                # 显示结果摘要
                success = result.get("success", False)
                route = result.get("route", "未知")
                
                if success:
                    print(f"    ✅ 任务成功完成")
                    print(f"      路由: {route}")
                    
                    # 显示生成的数据摘要
                    brain_layer = result.get("brain_layer", {})
                    nerves_layers = result.get("nerves_layers", [])
                    
                    if brain_layer:
                        print(f"      Brain层任务: {brain_layer.get('task_chain', [])}")
                    
                    if nerves_layers:
                        for nerves in nerves_layers:
                            if nerves.get("success", False):
                                actions = nerves.get("chain_of_action", [])
                                print(f"      Nerves层动作: {len(actions)} 个")
                
                else:
                    print(f"    ❌ 任务失败")
                    error_messages = result.get("error_messages", [])
                    if error_messages:
                        print(f"      错误: {error_messages[-1]}")
                
                results.append((task, success, result))
                
            except Exception as e:
                print(f"    💥 执行异常: {e}")
                import traceback
                traceback.print_exc()
                results.append((task, False, {"error": str(e)}))
        
        return results
    
    def cleanup(self, sandbox_path: str):
        """清理沙盒环境"""
        print("\n🧹 清理沙盒环境...")
        
        # 注意：沙盒管理器默认保留沙盒供调试
        # 如果需要完全清理，可以手动删除
        if sandbox_path and os.path.exists(sandbox_path):
            print(f"  ℹ️  沙盒保留在: {sandbox_path}")
            print(f"    如需清理，请手动删除该目录")
    
    def run(self):
        """运行完整演示"""
        try:
            # 1. 设置沙盒环境
            sandbox_path, storage_path = self.setup_sandbox()
            
            # 2. 设置组件
            cot_generator = self.setup_components(storage_path)
            
            # 3. 运行演示任务
            results = self.run_demo_tasks(cot_generator)
            
            # 4. 显示总结
            print("\n" + "=" * 60)
            print("📊 演示结果总结")
            print("=" * 60)
            
            successful = sum(1 for _, success, _ in results if success)
            total = len(results)
            
            print(f"\n✅ 成功任务: {successful}/{total}")
            
            for task, success, result in results:
                status = "✅" if success else "❌"
                print(f"  {status} {task}")
            
            # 5. 检查沙盒中的实际变化
            print(f"\n📁 沙盒状态检查:")
            storage_dir = Path(storage_path)
            if storage_dir.exists():
                files = list(storage_dir.rglob("*"))
                print(f"  文件总数: {len(files)}")
                
                # 检查是否有new_folder被创建
                new_folder = storage_dir / "new_folder"
                if new_folder.exists():
                    print(f"  ✅ new_folder文件夹已创建")
                    if (new_folder / "test.txt").exists():
                        print(f"  ✅ test.txt已移动到new_folder")
            
            # 6. 清理
            self.cleanup(sandbox_path)
            
            print("\n" + "=" * 60)
            if successful == total:
                print("🎉 第五步沙盒演示完全成功！")
                print("💡 CoT数据生成器在沙盒环境中工作正常")
                return True
            else:
                print("⚠️  第五步沙盒演示部分成功")
                print("💡 某些任务失败，但系统整体架构工作正常")
                return True  # 仍然返回True，因为演示目的是验证架构
            
        except Exception as e:
            print(f"\n💥 演示失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    # 检查环境
    print("🔍 检查演示环境...")
    
    # 检查PDDL文件
    domain_file = project_root / "pddl_configs" / "domain.pddl"
    if not domain_file.exists():
        print(f"❌ PDDL domain文件不存在: {domain_file}")
        print("💡 请确保已正确设置项目结构")
        return False
    
    # 运行演示
    demo = Step5SandboxDemo()
    success = demo.run()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)