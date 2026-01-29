"""AxiomLabs核心内核算法"""
import re
from typing import Set, Dict, Optional
from interface.translator import ITranslator
from interface.planner import IPlanner
from interface.executor import IExecutor
from interface.storage import IStorage
from config.settings import Settings
from config.constants import CONSTANTS


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
        max_iterations: int = None,
        sandbox_mode: bool = False,
        domain_path: str = None,
        config: Optional[Settings] = None
    ):
        """
        初始化内核

        :param translator: 翻译器接口
        :param planner: 规划器接口
        :param executor: 执行器接口
        :param storage: 存储接口
        :param max_iterations: 最大迭代次数，如果为None则使用配置中的值
        :param sandbox_mode: 是否沙盒模式（读取domain_exp.pddl）
        :param domain_path: 自定义domain文件路径（覆盖默认）
        :param config: 配置对象，如果为None则使用默认配置
        """
        self.translator = translator
        self.planner = planner
        self.executor = executor
        self.storage = storage
        self.config = config or Settings.load_from_env()
        # 使用配置中的值作为默认值
        self.max_iterations = max_iterations if max_iterations is not None else self.config.max_iterations
        self.memory_facts: Set[str] = set()
        self.objects: Dict[str, str] = {}  # 对象名 -> 类型
        self.base_init_facts: Set[str] = None  # 第一轮LLM生成的init基础事实
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
                execution_history,
                iteration=i,
                objects=self.objects if i > 0 else None,
                base_init_facts=self.base_init_facts if i > 0 else None
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

            # 如果是第一轮，从problem中提取objects并存储
            if i == 0:
                self._update_objects_from_problem(problem_pddl)

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
                        # 根据新增事实更新objects
                        self._update_objects_from_facts(result.add_facts, result.del_facts)
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

    def _update_objects_from_problem(self, problem_pddl: str):
        """
        从PDDL Problem中提取objects并更新self.objects
        同时提取第一轮的init事实作为base_init_facts
        """
        # 正则匹配objects部分
        objects_match = re.search(r'\(:objects\s+(.*?)\s*\)', problem_pddl, re.DOTALL)
        if not objects_match:
            return
        objects_text = objects_match.group(1).strip()
        # 按行分割
        lines = objects_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            # 格式: "obj1 obj2 ... - type"
            if ' - ' in line:
                objs_part, typ = line.rsplit(' - ', 1)
                objs = objs_part.split()
                for obj in objs:
                    self.objects[obj] = typ.strip()
        print(f"[Kernel] 从第一轮problem中提取objects: {self.objects}")
        
        # 提取init部分作为基础事实
        init_match = re.search(r'\(:init\s+(.*?)\s*\)\s*\(:goal', problem_pddl, re.DOTALL)
        if not init_match:
            # 尝试另一种模式：init后面直接是goal
            init_match = re.search(r'\(:init\s+(.*?)\s*\)\s*\(:goal', problem_pddl, re.DOTALL)
        if not init_match:
            # 最后尝试：init到文件末尾
            init_match = re.search(r'\(:init\s+(.*?)\s*\)\s*\)', problem_pddl, re.DOTALL)
        
        if init_match:
            init_text = init_match.group(1).strip()
            # 分割init事实 - 使用更复杂的正则匹配嵌套括号
            init_facts = set()
            
            # 方法：手动解析括号
            stack = []
            current_fact = []
            in_fact = False
            
            for char in init_text:
                if char == '(':
                    if not in_fact:
                        in_fact = True
                    stack.append(char)
                    current_fact.append(char)
                elif char == ')':
                    if stack:
                        stack.pop()
                        current_fact.append(char)
                        if not stack:  # 匹配到最外层的右括号
                            fact_str = ''.join(current_fact).strip()
                            if fact_str and not fact_str.startswith(';'):
                                init_facts.add(fact_str)
                            current_fact = []
                            in_fact = False
                    else:
                        # 不匹配的右括号，忽略
                        pass
                elif in_fact:
                    current_fact.append(char)
                # 忽略空格和换行
            
            # 清理：移除空事实和注释
            init_facts = {f for f in init_facts if f and not f.startswith(';')}
            
            self.base_init_facts = init_facts
            print(f"[Kernel] 从第一轮problem中提取{len(init_facts)}个基础init事实")

    def _update_objects_from_facts(self, add_facts: Set[str], del_facts: Set[str]):
        """
        根据新增/删除的事实更新objects
        目前仅支持file_management领域
        """
        # 使用常量中的类型映射
        type_mapping = CONSTANTS.TYPE_MAPPING
        # 处理新增事实
        for fact in add_facts:
            if fact.startswith("(not"):
                continue
            content = fact.strip("()")
            parts = content.split()
            if not parts:
                continue
            predicate = parts[0]
            if predicate not in type_mapping:
                continue
            mapping = type_mapping[predicate]
            for pos, obj in enumerate(parts[1:]):
                if pos in mapping:
                    obj_name = obj.strip("()")
                    if not obj_name:
                        continue
                    typ = mapping[pos]
                    self.objects[obj_name] = typ
        # 处理删除事实：如果某个对象在所有事实中都不再出现，则删除？暂时保留，因为可能在其他事实中引用。
        # 我们不做删除，因为对象可能在其他事实中仍然存在。
        # 但我们可以扫描所有memory_facts来清理？暂时跳过。

    def reset(self):
        """重置内核状态"""
        self.memory_facts.clear()
        self.objects.clear()
        self.current_domain = None
