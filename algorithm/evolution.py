"""进化算法 - 纯算法逻辑"""
import traceback
from typing import Dict
from interface.executor import IExecutor
from interface.planner import IPlanner
from interface.sandbox_manager import ISandboxManager
from interface.pddl_modifier import IPDDLModifier
from interface.llm import ILLM
from interface.storage import IStorage
from interface.translator import ITranslator


class EvolutionAlgorithm:
    """
    进化算法 - 负责在沙盒中尝试学习新技能
    纯算法逻辑，只依赖接口
    """

    def __init__(
        self,
        executor: IExecutor,
        planner: IPlanner,
        pddl_modifier: IPDDLModifier,
        max_retries: int = 4
    ):
        """
        初始化进化算法

        :param executor: 执行器接口
        :param planner: 规划器接口
        :param pddl_modifier: PDDL修改器接口
        :param max_retries: 最大重试次数
        """
        self.executor = executor
        self.planner = planner
        self.pddl_modifier = pddl_modifier
        self.max_retries = max_retries
        self.history_errors = []

    def evolve(
        self,
        user_goal: str,
        sandbox_manager: ISandboxManager,
        task_data: Dict,
        llm: ILLM,
        translator: ITranslator,
        storage: IStorage
    ) -> Dict:
        """
        运行进化循环

        :param user_goal: 用户目标
        :param sandbox_manager: 沙盒管理器
        :param task_data: 任务数据
        :param llm: LLM客户端
        :param translator: 翻译器
        :param storage: 存储接口
        :return: 进化结果
        """
        print(f"\n[Evolution] 启动进化任务: {user_goal}")
        current_error_context = "这是第一次尝试，请根据任务创建缺失的 PDDL Action 和 Python 技能。"

        for attempt in range(1, self.max_retries + 1):
            print(f"\n{'-'*20} 尝试次数: {attempt}/{self.max_retries} {'-'*20}")

            # 重置环境（第2次及以后）
            if attempt > 1:
                print("[Evolution] 正在重置物理沙盒并重新同步...")
                sandbox_manager.reset_jail_storage()

                # 清空执行历史（重置环境后）
                self.executor.clear_execution_history()

                # 重置所有技能的base_path
                self.executor.set_storage_path(sandbox_manager.get_storage_path())

                # 执行setup动作（只允许基础技能）
                base_skills = ["scan", "move", "get_admin", "remove_file", "compress"]
                for action in task_data.get('setup_actions', []):
                    if action[0] in base_skills:
                        self.executor.execute(" ".join(action))

                # 注意：这里不清空历史，让翻译器能看到setup动作（特别是scan）
                # 审计时会通过history_before_validation来区分setup动作和验证动作
                print("[Evolution] 沙盒环境重置完毕。")

            try:
                # 0. 备份当前Domain状态用于回滚
                domain_path = sandbox_manager.get_pddl_path()
                with open(domain_path, 'r', encoding='utf-8') as f:
                    domain_backup = f.read()

                # 1. 调用LLM获取补丁
                print("[Evolution] 正在咨询 LLM 如何进化...")
                evolution_data = self._ask_llm_for_patch(
                    user_goal,
                    current_error_context,
                    domain_path,
                    llm
                )

                # 2. 注入PDDL Action
                print("[Evolution] 正在注入 PDDL 逻辑补丁...")
                inject_success = self.pddl_modifier.add_action(
                    domain_path,
                    evolution_data['pddl_patch']
                )

                # 3. 语法预检与物理回滚
                print("[Evolution] 正在进行 PDDL 语法合法性预检...")
                with open(domain_path, 'r', encoding='utf-8') as f:
                    domain_content = f.read()

                check_result = self.planner.verify_syntax(domain_content)

                if not inject_success or not check_result[0]:
                    error_msg = check_result[1] if not check_result[0] else 'PDDLModifier 注入失败'
                    print(f"[Evolution] 语法预检失败！执行物理回滚并重试。")

                    # 物理回滚
                    with open(domain_path, 'w', encoding='utf-8') as f:
                        f.write(domain_backup)

                    current_error_context = f"PDDL语法错误: {error_msg}。请修正，严禁使用 exists 等关键字或未定义谓词。"
                    self.history_errors.append(current_error_context)
                    continue

                # 4. 写入并加载Python技能
                skill_file_name = f"generated_skill_v{attempt}.py"
                skill_path = f"{sandbox_manager.get_sandbox_path()}/skills/{skill_file_name}"

                with open(skill_path, "w", encoding="utf-8") as f:
                    f.write(evolution_data['python_code'])

                print(f"[Evolution] 正在动态加载技能脚本: {skill_file_name}")
                if not self.executor.register_skill_from_file(skill_path):
                    raise Exception("Python 语法错误或 GeneratedSkill 类缺失，无法加载。")

                # 5. 全流程沙盒集成验证
                print("[Evolution] 正在启动全流程集成验证...")
                # 记录当前历史长度作为审计基准（不清空历史，让翻译器能看到完整执行历史）
                history_before_validation = len(self.executor.get_execution_history())

                # 创建测试内核（沙盒模式）
                from algorithm.kernel import AxiomLabsKernel

                test_kernel = AxiomLabsKernel(
                    translator=translator,
                    planner=self.planner,
                    executor=self.executor,
                    storage=storage,
                    max_iterations=5,
                    sandbox_mode=True,  # 启用沙盒模式
                    domain_path=domain_path  # 指定沙盒domain文件路径
                )

                # 设置problem路径（用于调试）
                test_kernel.prob_path = f"{sandbox_manager.get_sandbox_path()}/sandbox_problem.pddl"

                # 设置所有技能的base_path
                self.executor.set_storage_path(sandbox_manager.get_storage_path())

                # 运行内核
                kernel_success = test_kernel.run(user_goal)

                # 虚假进化审计（只检查验证阶段新增的动作）
                target_action = evolution_data.get('action_name', '').lower()
                all_called_actions = [h.lower() for h in self.executor.get_execution_history()]
                validation_called_actions = all_called_actions[history_before_validation:]  # 只取验证阶段动作

                print(f"[Audit] 目标技能: {target_action}")
                print(f"[Audit] 完整调用历史: {all_called_actions}")
                print(f"[Audit] 验证阶段调用历史: {validation_called_actions}")

                has_actually_worked = len(validation_called_actions) > 0
                is_genuine_evolution = target_action in validation_called_actions

                if kernel_success and has_actually_worked and is_genuine_evolution:
                    print(f"进化成功！新技能 '{target_action}' 已实际投入运行。")
                    return {
                        "success": True,
                        "pddl_patch": evolution_data['pddl_patch'],
                        "python_code": evolution_data['python_code'],
                        "skill_file_path": skill_path,
                        "action_name": evolution_data.get('action_name')
                    }
                else:
                    # 审计拒绝
                    if kernel_success and not is_genuine_evolution:
                        current_error_context = f"审计拒绝：虽然任务成功，但你并未调用新技能 '{target_action}'。系统检测到你使用了旧技能组合 {validation_called_actions}。请为新技能设置更低的 (total-cost) 或在 PDDL 中增加必不可少的前提条件，迫使 Planner 选用它。"
                        print(f"[Evolution] \033[91m验证失败：虚假进化被拦截。\033[0m")
                    else:
                        current_error_context = "系统检测到你没有调用任何 Action 就报告了任务完成。在进化模式下，你必须通过编写和使用新技能来达成目标。"
                        print(f"[Evolution] 验证失败：禁止原地踏步。")

                    # 物理回滚
                    with open(domain_path, 'w', encoding='utf-8') as f:
                        f.write(domain_backup)
                    continue

            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"系统崩溃或逻辑异常: {str(e)}")
                current_error_context = f"""
[System Crash Report]
Attempt #{attempt} Failed.
Python Exception: {str(e)}
Traceback:
{error_trace}
Analysis: The generated code caused a Python exception. Fix syntax or library usage.
"""
                self.history_errors.append(current_error_context)

        # 达到上限
        self._generate_final_report(user_goal)
        return {"success": False}

    def _get_system_context(self):
        """获取系统规范"""
        return """
### AxiomLabs 开发规范 (System Rules) ###
1. 技能基类定义:
class MCPBaseSkill:
    def _safe_path(self, *parts): # 自动处理 _dot_ 并返回绝对路径
    async def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 执行技能逻辑，返回MCP结构化响应
        # 使用 self.create_success_response(message, pddl_delta) 或 self.create_error_response(error_message)
2. 返回结果规范:
MCP技能必须返回结构化响应，使用 self.create_success_response(message, pddl_delta)
- message: 人类可读的消息
- pddl_delta: PDDL事实变化，格式如 "(at file folder)" 或 "(not (at file folder))"
3. 文件系统规则:
- 文件名中的 '.' 统一表现为 '_dot_' (PDDL 兼容性)
- 只能操作 self._safe_path() 构建的路径下的文件
"严禁在非删除类操作（如 copy, scan, get_admin）中包含 (not (at ...)) 效果。copy 操作必须保持源文件状态不变。"
"""

    def _ask_llm_for_patch(self, goal: str, error_context: str, pddl_path: str, llm: ILLM) -> Dict:
        """询问LLM生成补丁"""
        system_context = self._get_system_context()

        with open(pddl_path, "r", encoding="utf-8") as f:
            current_domain = f.read()

        prompt = f"""
你现在是 AxiomLabs 核心进化模块。
{system_context}
目标: {goal}
错误反馈: {error_context}

任务：根据目标输出 PDDL Action 补丁和 Python 技能类 (GeneratedSkill) 的 JSON。

[核心约束]:
1. 逻辑守恒：del_facts 仅允许用于物理消失或位移（如 remove/move）。copy 等操作严禁删除源事实。
2. 闭环性：PDDL 的 :effect 必须与 Python 的 ExecutionResult 严格一致。
3. 强制优先级：新 Action 的 :effect 必须包含 (is_created ?new_file)，以确保 Planner 优先使用它而非 create+remove 组合。
4. 类型继承：观察 PDDL Problem 中的目标 (:goal (predicate ?obj1 ...))。
   生成的 Action 参数类型必须与 ?obj1 在 :objects 中定义的类型完全一致或为其父类。
   - 严禁自创如 'name', 'target', 'filename' 等临时类型。
   - 如果目标对象是 - file，参数就写 - file；是 - folder，就写 - folder。
5. 谓词守恒：生成的 Action :effect 必须能够闭环 (:goal) 中的谓词。
   - 如果目标要求 (at A B)，你的 Effect 必须产出 (at ?param_a ?param_b)，不能只产出 (is_created ?param_a)。
6. Python 代码的 args 顺序必须与 PDDL :parameters 顺序严格一一对应。
7. 对象声明：所有出现在 :goal 中的实体必须在 :objects 区块中显式声明其类型。

[PDDL语法约束]:
1. 只能生成 (:action ... ) 块，严禁生成 :predicates, :types, :requirements, :functions 等domain级结构。
2. 严禁在action中重复定义谓词或类型。
3. 所有谓词必须已经在domain的(:predicates)部分定义过。
4. 所有类型必须已经在domain的(:types)部分定义过。

[代码规范]:
1. 路径处理：必须使用 `self._safe_path(folder, filename)` 获取物理路径，严禁手动 replace。
2. 事实返回：self.create_success_response() 的 pddl_delta必须保留原始 args 中的 `_dot_` 命名。
3. PDDL 前提：Precondition 仅限 (scanned), (at), (has_admin_rights) 等现有谓词。

[输出 JSON 模板]:
{{
    "action_name": "remove_file",
    "pddl_patch": "(:action remove_file :parameters (?f - file ?d - folder) :precondition (and (at ?f ?d)) :effect (and (not (at ?f ?d))))",
    "python_code": "from infrastructure.mcp_skills.mcp_base_skill import MCPBaseSkill\\nimport os\\nimport json\\n\\nclass GeneratedSkill(MCPBaseSkill):\\n    @property\\n    def name(self):\\n        return 'remove_file'\\n    \\n    @property\\n    def description(self):\\n        return '删除文件'\\n    \\n    @property\\n    def input_schema(self):\\n        return {{\\n            'type': 'object',\\n            'properties': {{\\n                'file': {{'type': 'string', 'description': '文件名（PDDL格式，点替换为_dot_）'}},\\n                'folder': {{'type': 'string', 'description': '文件夹名'}}\\n            }},\\n            'required': ['file', 'folder']\\n        }}\\n    \\n    async def execute(self, arguments):\\n        file = arguments.get('file')\\n        folder = arguments.get('folder')\\n        target = self._safe_path(folder, file)\\n        try:\\n            os.remove(target)\\n            pddl_delta = f'(not (at {{file}} {{folder}}))'\\n            return self.create_success_response(f'文件 {{file}} 已从 {{folder}} 删除', pddl_delta)\\n        except Exception as e:\\n            return self.create_error_response(str(e))",
    "test_args": ["test_dot_txt", "root"]
}}
"""
        response = llm.chat(
            messages=[
                {"role": "system", "content": "你是一个严谨的系统底层专家，只输出 JSON。"},
                {"role": "user", "content": prompt}
            ],
            response_format={'type': 'json_object'}
        )

        content = response
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")

        import json
        return json.loads(content)

    def _generate_final_report(self, goal: str):
        """生成失败总结报告"""
        print("\n" + "!"*30)
        print("进化任务宣告失败 (已达重试上限)")
        print(f"任务目标: {goal}")
        print("-" * 30)
        print("【失败历程总结】:")
        for i, err in enumerate(self.history_errors):
            print(f"尝试 {i+1}: {err[:100]}...")
        print("-" * 30)
        print("【人工介入建议】:")
        print("1. 检查 Python 技能是否因为路径转义 (_dot_) 导致物理路径拼接错误。")
        print("2. 检查 PDDL 前提条件是否过于苛刻导致 Planner 拒绝生成路径。")
        print("3. 沙盒目录 sandbox_runs/ 中保留了最后一次生成的脚本，请手动调试。")
        print("!"*30 + "\n")
