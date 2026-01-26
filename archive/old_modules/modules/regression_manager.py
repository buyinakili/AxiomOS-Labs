import json
import os
import shutil
from main_demo import AIOSKernel
from modules.translator import PDDLTranslator
from modules.planner import LAMAPlanner
from modules.executor import ActionExecutor
from modules.sandbox import SandboxManager

class RegressionManager:
    def __init__(self, llm_client, registry_path="tests/regression_registry.json"):
        self.client = llm_client
        self.registry_path = registry_path
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def load_tests(self):
        if not os.path.exists(self.registry_path):
            return []
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_new_test(self, task_data):
        """
        将新学会的任务加入回归测试库
        task_data: dict, 包含 goal, setup_actions 等
        """
        tests = self.load_tests()
        new_entry = {
            "task_name": task_data.get("task_name", "Unknown_Action"),
            "goal": task_data["goal"],
            # 这里的 setup_actions 是由 CurriculumManager 生成的
            # 它包含了创建文件、创建目录等准备动作
            "setup_actions": task_data.get("setup_actions", []) 
        }
    
        # 避免重复
        if any(t['goal'] == new_entry['goal'] for t in tests):
            return

        tests.append(new_entry)
        
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(tests, f, indent=4, ensure_ascii=False)
        print(f"[Regression] 新任务已收录至回归库: {new_entry['goal']}")

    def run_regression_suite(self, candidate_domain_path, candidate_skill_path):
        """
        运行回归测试套件
        :param candidate_domain_path: 包含新 Action 的 domain PDDL 路径
        :param candidate_skill_path: 新生成的 Python Skill 脚本路径
        :return: bool (全部通过返回 True)
        """
        tests = self.load_tests()
        if not tests:
            print("[Regression] 测试库为空，跳过回归测试。")
            return True

        print(f"\n{'#'*20} 启动回归测试 (共 {len(tests)} 个用例) {'#'*20}")
        print("目的: 验证新加入的功能是否破坏了原有能力。")

        # 1. 临时创建一个全新的回归沙盒，避免污染
        reg_sm = SandboxManager()
        reg_sandbox_path = reg_sm.create_sandbox()
        
        # 2. 将 候选Domain 覆盖到回归沙盒中
        sandbox_domain_path = os.path.join(reg_sandbox_path, "domain_exp.pddl")
        shutil.copy(candidate_domain_path, sandbox_domain_path)

        # 3. 准备执行器并加载 新技能
        # 注意：这里需要在每个 case 运行前重新初始化吗？
        # 建议每次测试重置环境，但 Executor 可以复用，只需确保新技能被注册
        
        all_passed = True

        for idx, test_case in enumerate(tests):
            print(f"\n[Regression Case {idx+1}/{len(tests)}] 测试目标: {test_case['goal']}")
            
            # --- A. 环境重置 ---
            # 彻底重置：先删除旧沙盒存储，再重新从真实 storage 镜像一份
            if os.path.exists(reg_sm.storage_path):
                shutil.rmtree(reg_sm.storage_path)
            
            # 重新执行镜像逻辑，确保 root, backup 等基础文件夹和初始文件存在
            src_storage = os.path.join(self.project_root, "workspace")
            if os.path.exists(src_storage):
                shutil.copytree(src_storage, reg_sm.storage_path)
            else:
                os.makedirs(os.path.join(reg_sm.storage_path, "root"), exist_ok=True)
            
            # --- B. 构造执行器 ---
            reg_executor = ActionExecutor()
            # 这里的 executor 默认加载了 base skills
            # 必须手动加载本次进化的新 skill
            if candidate_skill_path and os.path.exists(candidate_skill_path):
                reg_executor.register_dynamic_skill(candidate_skill_path)
            
            # 将所有 skill 指向回归沙盒的路径
            for skill in reg_executor.skills.values():
                skill.base_path = reg_sm.storage_path

            # --- C. 执行 Setup Actions ---
            if 'setup_actions' in test_case:
                for action in test_case['setup_actions']:
                    verb, *args = action
                    reg_executor.execute_step(verb, args)
            
            from config import DOWNWARD_PATH
            # --- D. 运行 Kernel ---
            reg_planner = LAMAPlanner(DOWNWARD_PATH)
            reg_translator = PDDLTranslator(self.client)
            
            kernel = AIOSKernel(reg_translator, reg_planner, reg_executor)
            kernel.domain_path = sandbox_domain_path # 强制使用带补丁的 Domain
            kernel.prob_path = os.path.join(reg_sandbox_path, "regression_prob.pddl")
            # 必须清除 kernel 记忆，防止上下文污染
            kernel.memory_facts = set()
            
            try:
                # 扫描初始状态
                initial_scan = reg_executor.execute_step("scan", ["root"])
                if initial_scan.is_success:
                     kernel.memory_facts.update(initial_scan.add_facts)

                success = kernel.run(test_case['goal'])
                
                if success:
                    print(f"  -> [PASS] 测试用例通过。")
                else:
                    print(f"  -> [FAIL] 任务执行失败。")
                    all_passed = False
                    break # 只要有一个失败，就判定回归失败，防止破坏系统
            except Exception as e:
                print(f"  -> [ERROR] 测试过程发生异常: {e}")
                all_passed = False
                break
        
        # 清理回归沙盒
        # shutil.rmtree(reg_sandbox_path) 
        
        if all_passed:
            print(f"\n[Regression] 所有测试用例通过！新能力验证安全。")
        else:
            print(f"\n[Regression] 警告：新能力导致回归测试失败，拒绝合并。")
            
        return all_passed
    