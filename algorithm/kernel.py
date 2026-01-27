"""AxiomLabs核心内核算法"""
import re
from typing import Set
from interface.translator import ITranslator
from interface.planner import IPlanner
from interface.executor import IExecutor
from interface.storage import IStorage


class AxiomLabsKernel:
    """
    AxiomLabs核心内核 - 纯算法逻辑，只依赖接口
    """

    def __init__(
        self,
        translator: ITranslator,
        planner: IPlanner,
        executor: IExecutor,
        storage: IStorage,
        max_iterations: int = 5,
        sandbox_mode: bool = False,
        domain_path: str = None
    ):
        """
        初始化内核

        :param translator: 翻译器接口
        :param planner: 规划器接口
        :param executor: 执行器接口
        :param storage: 存储接口
        :param max_iterations: 最大迭代次数
        :param sandbox_mode: 是否沙盒模式（读取domain_exp.pddl）
        :param domain_path: 自定义domain文件路径（覆盖默认）
        """
        self.translator = translator
        self.planner = planner
        self.executor = executor
        self.storage = storage
        self.max_iterations = max_iterations
        self.memory_facts: Set[str] = set()
        self.current_domain: str = None
        self.sandbox_mode = sandbox_mode
        self.domain_path = domain_path

    def run(self, user_goal: str) -> bool:
        """
        执行任务

        :param user_goal: 用户目标描述
        :return: 是否成功
        """
        # 1. 路由领域
        if not self.current_domain:
            self.current_domain = self.translator.route_domain(user_goal)
            print(f"[Kernel] 领域路由成功: [{self.current_domain}]")

        # 2. 迭代执行
        for i in range(self.max_iterations):
            print(f"\n{'='*10} 迭代 {i+1}/{self.max_iterations} {'='*10}")

            # 3. 生成PDDL Problem
            execution_history = self.executor.get_execution_history()
            problem_pddl = self.translator.translate(
                user_goal,
                self.memory_facts,
                self.current_domain,
                execution_history
            )

            # 检查是否已完成
            if "GOAL_FINISHED_ALREADY" in problem_pddl:
                print(f"[Kernel] 任务完成：目标已达成")
                return True

            # 预检：检查目标是否已在事实库中
            goal_predicates = self._extract_goal_predicates(problem_pddl)
            if goal_predicates and self._check_goals_achieved(goal_predicates):
                print(f"[Kernel] 任务完成：目标谓词已在事实库中")
                return True

            # 4. 保存Problem并执行规划
            self.storage.write_problem(problem_pddl)
            
            # 读取domain内容
            if self.sandbox_mode and self.domain_path:
                # 沙盒模式：从指定路径读取domain_exp.pddl
                import os
                if os.path.exists(self.domain_path):
                    with open(self.domain_path, "r", encoding="utf-8") as f:
                        domain_content = f.read()
                else:
                    # 回退到默认domain
                    domain_content = self.storage.read_domain(self.current_domain)
            else:
                # 正常模式：从storage读取domain.pddl
                domain_content = self.storage.read_domain(self.current_domain)

            plan_result = self.planner.plan(domain_content, problem_pddl)

            if not plan_result.success:
                print(f"[Kernel] 规划失败: {plan_result.error}")
                self.memory_facts.add(f"; Logic Feedback: {plan_result.error}")
                continue

            # 检查规划是否为空
            if not plan_result.actions:
                print(f"[Kernel] 规划器报告：当前状态已满足目标")
                return True

            # 5. 显示规划逻辑链条
            print(f"\n[Kernel] 规划成功！生成 {len(plan_result.actions)} 个步骤的逻辑链条：")
            print("-" * 60)
            for idx, (action_str, step_num) in enumerate(plan_result.actions, 1):
                print(f"  步骤 {step_num} ({idx}/{len(plan_result.actions)}): {action_str}")
            print("-" * 60)
            print(f"[Kernel] 开始执行规划链条...\n")

            # 6. 执行规划链
            chain_success = True

            for action_str, step_num in plan_result.actions:
                result = self.executor.execute(action_str)

                if result.success:
                    print(f"[Kernel] 步骤 {step_num} 成功: {result.message}")

                    # 更新事实库
                    if result.del_facts:
                        for df in result.del_facts:
                            self.memory_facts.discard(df)
                            print(f"[Kernel] 删除事实: {df}")

                    if result.add_facts:
                        self.memory_facts.update(result.add_facts)
                else:
                    print(f"[Kernel] 步骤 {step_num} 失败: {result.message}")
                    self.memory_facts.add(f"; Error: {result.message}")
                    chain_success = False
                    break

            if chain_success:
                print(f"[Kernel] 执行链完成，进入下一轮验证...")
                continue

        print(f"[Kernel] 达到最大迭代次数，任务未完成")
        return False

    def _extract_goal_predicates(self, problem_pddl: str) -> list:
        """
        从PDDL Problem中提取目标谓词

        :param problem_pddl: Problem PDDL内容
        :return: 谓词列表
        """
        goal_match = re.search(r'\(:goal\s+\(and\s+(.*?)\s*\)\s*\)', problem_pddl, re.DOTALL)
        if not goal_match:
            goal_match = re.search(r'\(:goal\s+(.*?)\s*\)', problem_pddl, re.DOTALL)

        if goal_match:
            goal_content = goal_match.group(1).strip()
            predicates = re.findall(r'\(.*?\)', goal_content)
            return [p.strip() for p in predicates]

        return []

    def _check_goals_achieved(self, goal_predicates: list) -> bool:
        """
        检查目标谓词是否已在事实库中

        :param goal_predicates: 目标谓词列表
        :return: 是否全部达成
        """
        for gp in goal_predicates:
            if gp not in self.memory_facts:
                return False
        return True

    def reset(self):
        """重置内核状态"""
        self.memory_facts.clear()
        self.current_domain = None
