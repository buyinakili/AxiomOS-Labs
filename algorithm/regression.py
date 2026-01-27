"""回归测试算法 - 纯算法逻辑"""
import json
import os
import shutil
from typing import List, Dict
from interface.sandbox_manager import ISandboxManager
from interface.executor import IExecutor
from interface.translator import ITranslator
from interface.planner import IPlanner
from interface.storage import IStorage
from interface.llm import ILLM


class RegressionAlgorithm:
    """
    回归测试算法 - 负责验证新技能不破坏旧功能
    纯算法逻辑，只依赖接口
    """

    def __init__(self, registry_path: str):
        """
        初始化回归测试算法

        :param registry_path: 测试用例注册表路径
        """
        self.registry_path = registry_path

    def load_tests(self) -> List[Dict]:
        """加载所有回归测试用例"""
        if not os.path.exists(self.registry_path):
            return []

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_new_test(self, task_data: Dict):
        """将新学会的任务加入回归测试库"""
        tests = self.load_tests()

        new_entry = {
            "task_name": task_data.get("task_name", "Unknown_Action"),
            "goal": task_data["goal"],
            "setup_actions": task_data.get("setup_actions", [])
        }

        # 避免重复
        if any(t['goal'] == new_entry['goal'] for t in tests):
            print(f"[Regression] 测试用例已存在，跳过添加")
            return

        tests.append(new_entry)

        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(tests, f, indent=4, ensure_ascii=False)

        print(f"[Regression] 新任务已收录至回归库: {new_entry['goal']}")

    def run_regression_suite(
        self,
        candidate_domain_path: str,
        candidate_skill_path: str,
        sandbox_manager: ISandboxManager,
        llm: ILLM,
        storage: IStorage,
        translator_factory,
        planner_factory,
        executor_factory
    ) -> bool:
        """
        运行回归测试套件

        :param candidate_domain_path: 包含新Action的Domain PDDL路径
        :param candidate_skill_path: 新生成的Python技能脚本路径
        :param sandbox_manager: 沙盒管理器
        :param llm: LLM客户端
        :param storage: 存储接口
        :param translator_factory: 翻译器工厂函数
        :param planner_factory: 规划器工厂函数
        :param executor_factory: 执行器工厂函数
        :return: 是否全部通过
        """
        tests = self.load_tests()

        if not tests:
            print("[Regression] 测试库为空，跳过回归测试。")
            return True

        print(f"\n{'#'*20} 启动回归测试 (共 {len(tests)} 个用例) {'#'*20}")
        print("目的: 验证新加入的功能是否破坏了原有能力。")

        # 创建回归沙盒
        reg_sandbox_path = sandbox_manager.create_sandbox()

        # 将候选Domain覆盖到回归沙盒中
        sandbox_domain_path = sandbox_manager.get_pddl_path()
        shutil.copy(candidate_domain_path, sandbox_domain_path)

        all_passed = True

        for idx, test_case in enumerate(tests):
            print(f"\n[Regression Case {idx+1}/{len(tests)}] 测试目标: {test_case['goal']}")

            # 重置环境
            sandbox_manager.reset_jail_storage()

            # 创建执行器
            reg_executor = executor_factory()

            # 加载新技能
            if candidate_skill_path and os.path.exists(candidate_skill_path):
                reg_executor.register_skill_from_file(candidate_skill_path)

            # 设置base_path
            reg_executor.set_storage_path(sandbox_manager.get_storage_path())

            # 执行Setup Actions
            if 'setup_actions' in test_case:
                for action in test_case['setup_actions']:
                    verb = action[0]
                    args = action[1:] if len(action) > 1 else []
                    reg_executor.execute(f"{verb} {' '.join(args)}")

            # 创建内核
            reg_planner = planner_factory()
            reg_translator = translator_factory()

            from algorithm.kernel import AxiomLabsKernel
            kernel = AxiomLabsKernel(
                translator=reg_translator,
                planner=reg_planner,
                executor=reg_executor,
                storage=storage,
                max_iterations=5
            )

            # 重定向到沙盒Domain
            kernel.domain_path = sandbox_domain_path
            kernel.prob_path = f"{reg_sandbox_path}/regression_prob.pddl"
            kernel.memory_facts = set()

            try:
                # 扫描初始状态
                initial_scan = reg_executor.execute("scan root")
                if initial_scan.success:
                    kernel.memory_facts.update(initial_scan.add_facts)

                # 运行任务
                success = kernel.run(test_case['goal'])

                if success:
                    print(f"  -> [PASS] 测试用例通过。")
                else:
                    print(f"  -> [FAIL] 任务执行失败。")
                    all_passed = False
                    break

            except Exception as e:
                print(f"  -> [ERROR] 测试过程发生异常: {e}")
                all_passed = False
                break

        if all_passed:
            print(f"\n[Regression] 所有测试用例通过！新能力验证安全。")
        else:
            print(f"\n[Regression] 警告：新能力导致回归测试失败，拒绝合并。")

        return all_passed
