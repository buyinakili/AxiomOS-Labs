import os
from modules.sandbox import SandboxManager
from modules.executor import ActionExecutor
from modules.evolution_manager import EvolutionManager

# 模拟一个 LLM 客户端占位符（实际测试中目前用不到，因为 EvolutionManager 里是 Mock 的）
class MockLLMClient:
    pass

def test_evolution_loop():
    print("=== 启动 AIOS 自动化进化测试 (v2) ===")
    
    # 1. 初始化基础设施
    sm = SandboxManager()
    sandbox_path = sm.create_sandbox()
    
    # 2. 初始化执行器 (自动指向沙盒路径)
    executor = ActionExecutor()
    # 这一步很关键：为了测试 remove，我们需要先在沙盒里“造”一个文件让它删
    # 因为 EvolutionManager 的模拟数据里写死了要删 to_be_deleted_dot_txt
    print("\n[预设] 正在沙盒中创建测试文件...")
    executor.skills["create_file"].base_path = sm.storage_path
    executor.execute_step("create_file", ["to_be_deleted_dot_txt", "root"])
    
    # 3. 初始化进化管理器
    # 此时 executor 还没加载 remove 技能，PDDL 也没修改
    ev_manager = EvolutionManager(executor, max_retries=2)
    
    # 4. 运行进化循环
    # 目标："删除文件" (触发内部的 Mock 数据)
    user_goal = "帮我删除 root 下的 txt 文件"
    success = ev_manager.run_evolution_loop(user_goal, sm, MockLLMClient())
    
    # 5. 最终验证
    if success:
        print("\n=== 测试结论: 进化闭环测试通过 ===")
        # 验证 PDDL 是否真的改了
        with open(sm.get_pddl_path(), 'r') as f:
            if "(:action remove_file" in f.read():
                print("Checking... Domain PDDL 已成功注入 Action。")
            else:
                print("Checking... [Error] PDDL 未发现注入痕迹。")
    else:
        print("\n=== 测试结论: 进化失败 ===")

if __name__ == "__main__":
    test_evolution_loop()
#python3 train_env_v1.py