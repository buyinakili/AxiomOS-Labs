import os
import json
import shutil
import traceback
from modules.pddl_modifier import PDDLModifier
from modules.skills.base import SkillResult

class EvolutionManager:
    def __init__(self, executor,planner, max_retries=4):
        """
        :param executor: ActionExecutor 实例
        :param max_retries: 最大重试次数 (你要求的 4 次)
        """
        self.executor = executor
        self.planner = planner
        self.modifier = PDDLModifier()
        self.max_retries = max_retries
        self.history_errors = [] # 记录重试过程中的错误日志

    def run_evolution_loop(self, user_goal, sandbox_manager, task_data,llm_client):
        """
        核心进化循环：失败 -> 反思 -> 修复 -> 再尝试
        """
        print(f"\n[Evolution] 启动进化任务: {user_goal}")
        current_error_context = "这是第一次尝试，请根据任务创建缺失的 PDDL Action 和 Python 技能。"
        
        for attempt in range(1, self.max_retries + 1):
            print(f"\n{'-'*20} 尝试次数: {attempt}/{self.max_retries} {'-'*20}")
            
            if attempt > 1:
                print("[Evolution] 正在为新一轮尝试重置物理沙盒状态...")
                if os.path.exists(sandbox_manager.storage_path):
                    shutil.rmtree(sandbox_manager.storage_path)
                os.makedirs(os.path.join(sandbox_manager.storage_path, "root"), exist_ok=True)
                os.makedirs(os.path.join(sandbox_manager.storage_path, "backup"), exist_ok=True)

                for skill in self.executor.skills.values():
                    skill.base_path = sandbox_manager.storage_path
                
                for action in task_data.get('setup_actions', []):
                    # 使用 self.executor 确保状态一致
                    self.executor.execute_step(" ".join(action))
                
                # 关键：环境准备好了，现在清空历史，准备记录“进化的关键动作”
                self.executor.execution_history = [] 
                print("[Evolution] 沙盒物理环境已重置。")
                
            
            try:
                # 0. 【新增】备份当前 Domain 状态用于回滚
                domain_path = sandbox_manager.get_pddl_path()
                with open(domain_path, 'r', encoding='utf-8') as f:
                    domain_backup = f.read()

                # 1. 调用 LLM 获取补丁
                print("[Evolution] 正在咨询 LLM 如何进化...")
                evolution_data = self._ask_llm_for_patch(user_goal, current_error_context, sandbox_manager, llm_client)
                
                # 2. 注入 PDDL Action
                print("[Evolution] 正在注入 PDDL 逻辑补丁...")
                inject_success = self.modifier.add_action_to_domain(
                    domain_path, 
                    evolution_data['pddl_patch']
                )
                
                # 3. 【新增】语法预检与物理回滚
                print("[Evolution] 正在进行 PDDL 语法合法性预检...")
                # 修复调用路径：直接调用 self.planner
                check_result = self.planner.verify_domain(domain_path) 
                
                if not inject_success or not check_result['is_valid']:
                    error_msg = check_result.get('error', 'PDDLModifier 注入失败')
                    print(f"[Evolution] 语法预检失败！执行物理回滚并重试。")
                    
                    # 物理回滚：将 domain 文件恢复到注入前的状态
                    with open(domain_path, 'w', encoding='utf-8') as f:
                        f.write(domain_backup)
                    
                    # 记录错误引导 LLM
                    current_error_context = f"PDDL语法错误: {error_msg}。请修正，严禁使用 exists 等关键字或未定义谓词。"
                    self.history_errors.append(current_error_context)
                    continue # 关键：跳过后续步骤，直接进入下一次尝试
                
                # 4. 写入并加载 Python 技能
                skill_file_name = f"generated_skill_v{attempt}.py"
                skill_path = os.path.join(sandbox_manager.current_sandbox_path, "skills", skill_file_name)
                with open(skill_path, "w", encoding="utf-8") as f:
                    f.write(evolution_data['python_code'])
                
                print(f"[Evolution] 正在动态加载技能脚本: {skill_file_name}")
                if not self.executor.register_dynamic_skill(skill_path):
                    raise Exception("Python 语法错误或 GeneratedSkill 类缺失，无法加载。")

                # 4. 全流程沙盒集成验证 (完美镜像真实模式)
                print("[Evolution] 正在启动全流程集成验证 (Translator -> Planner -> Executor)...")
                self.executor.execution_history = []
                from main_demo import AIOSKernel
                from modules.translator import PDDLTranslator
                from modules.planner import LAMAPlanner
                #initial_facts = self._scan_initial_state(sandbox_manager.storage_path)
                #filtered_facts = [f for f in initial_facts if "deleted_dot_txt" not in f]
                # 初始化沙盒专用内核组件
                # 注意：这里的 fast-downward 路径需与你 main_demo.py 中一致
                temp_planner = LAMAPlanner("/home/nakili/projects/AIOS/downward/fast-downward.py")
                temp_translator = PDDLTranslator(llm_client)
                
                test_kernel = AIOSKernel(temp_translator, temp_planner, self.executor)
                sandbox_domain = os.path.join(sandbox_manager.current_sandbox_path, "domain_exp.pddl")
                # 【核心重定向】: 强制内核使用沙盒内的 PDDL 文件和物理路径
                test_kernel.domain_path = sandbox_domain
                test_kernel.prob_path = os.path.join(sandbox_manager.current_sandbox_path, "sandbox_problem.pddl")

                print(f"[Evolution] 正在从物理沙盒同步真实环境状态...")
                test_kernel.memory_facts.clear() # 确保干净
                
                # 扫描 root 文件夹 (假设大部分测试都在 root 下)
                # 如果你的测试涉及多层级，这里可以用 os.walk 递归
                sandbox_root = os.path.join(sandbox_manager.storage_path, "root")
                if os.path.exists(sandbox_root):
                    for f_name in os.listdir(sandbox_root):
                        if f_name.startswith("."): continue
                        
                        # 处理文件名转义 (a.txt -> a_dot_txt)
                        safe_name = f_name.replace(".", "_dot_")
                        
                        # 生成正确的事实
                        if os.path.isfile(os.path.join(sandbox_root, f_name)):
                            real_fact = f"(at {safe_name} root)"
                            test_kernel.memory_facts.add(real_fact)
                            print(f"  -> 捕获事实: {real_fact}")
                        elif os.path.isdir(os.path.join(sandbox_root, f_name)):
                            # 如果是文件夹，生成连接关系
                            test_kernel.memory_facts.add(f"(connected root {safe_name})")
                            test_kernel.memory_facts.add(f"(connected {safe_name} root)")
   

                for skill in self.executor.skills.values():
                    skill.base_path = os.path.abspath(sandbox_manager.storage_path)

                kernel_success = test_kernel.run(user_goal)
                
                # --- [新增：虚假进化审计逻辑] ---
                target_action = evolution_data.get('action_name', '').lower()
                # 提取执行历史中所有调用过的动作名称
                actual_called_actions = [str(h).lower() for h in self.executor.execution_history]
                
                print(f"[Audit] 目标技能: {target_action}")
                print(f"[Audit] 实际调用历史: {actual_called_actions}")

                # 判定 1: 必须有动作执行
                has_actually_worked = len(actual_called_actions) > 0
                
                # 判定 2: 执行的动作中必须包含本次新进化的技能
                is_genuine_evolution = target_action in actual_called_actions

                if kernel_success and has_actually_worked and is_genuine_evolution:
                    # --- [审计通过] ---
                    print(f"进化成功！新技能 '{target_action}' 已实际投入运行。")
                    #self.executor.execution_history = [] 
                    return {
                        "success": True,
                        "pddl_patch": evolution_data['pddl_patch'],
                        "python_code": evolution_data['python_code'],
                        "skill_file_path": skill_path,
                        "action_name": evolution_data.get('action_name')
                    }
                else:
                    # --- [审计拒绝] ---
                    if kernel_success and not is_genuine_evolution:
                        current_error_context = f"审计拒绝：虽然任务成功，但你并未调用新技能 '{target_action}'。系统检测到你使用了旧技能组合 {actual_called_actions}。请为新技能设置更低的 (total-cost) 或在 PDDL 中增加必不可少的前提条件，迫使 Planner 选用它。"
                        print(f"[Evolution] \033[91m验证失败：虚假进化被拦截。\033[0m")
                        # 物理回滚后，必须重置执行历史，确保下一轮审计从零开始
                        self.executor.execution_history = []
                    else:
                        current_error_context = "系统检测到你没有调用任何 Action 就报告了任务完成。在进化模式下，你必须通过编写和使用新技能来达成目标。"
                        print(f"[Evolution] 验证失败：禁止原地踏步。")
                    
                    # 物理回滚并重试
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

        # 5. 达到上限，输出总结报告
        self._generate_final_report(user_goal)
        return {"success": False}

    def _get_system_context(self):
        return """
        ### AIOS 开发规范 (System Rules) ###
        1. 技能基类定义:
        class BaseSkill:
            def _safe_path(self, *parts): # 自动处理 _dot_ 并返回绝对路径
        2. 返回结果规范:
        SkillResult(is_success, message, add_facts=[], del_facts=[])
        - add_facts: 执行成功后需要写入环境的 PDDL 事实列表
        3. 文件系统规则:
        - 文件名中的 '.' 统一表现为 '_dot_' (PDDL 兼容性)
        - 只能操作 self.base_path 目录下的文件
        “严禁在非删除类操作（如 copy, scan, get_admin）中包含 (not (at ...)) 效果。copy 操作必须保持源文件状态不变。”
        """

    def _ask_llm_for_patch(self, goal, error_context, sandbox_manager, llm_client):
        system_context = self._get_system_context()
        pddl_path = sandbox_manager.get_pddl_path() 
        with open(pddl_path, "r", encoding="utf-8") as f:
            current_domain = f.read()

        # 核心 Prompt 设计：强制要求返回 JSON，并提供 BaseSkill 的模板
        prompt = f"""
你现在是 AIOS 核心进化模块。
{system_context}
目标: {goal}
错误反馈: {error_context}

任务：根据目标输出 PDDL Action 补丁和 Python 技能类 (GeneratedSkill) 的 JSON。

[核心约束 - 逻辑与物理对齐]:
1. 逻辑守恒：del_facts 仅允许用于物理消失或位移（如 remove/move）。copy 等操作严禁删除源事实。
2. 闭环性：PDDL 的 :effect 必须与 Python 的 SkillResult 严格一致。
3. 强制优先级：新 Action 的 :effect 必须包含 (is_created ?new_file)，以确保 Planner 优先使用它而非 create+remove 组合。

[代码规范]:
1. 路径处理：必须使用 `self._safe_path(folder, filename)` 获取物理路径，严禁手动 replace。
2. 事实返回：SkillResult 的 add/del_facts 必须保留原始 args 中的 `_dot_` 命名。
3. PDDL 前提：Precondition 仅限 (scanned), (at), (has_admin_rights) 等现有谓词。

[输出 JSON 模板]:
{{
    "action_name": "remove_file",
    "pddl_patch": "(:action remove_file :parameters (?f - file ?d - folder) ...)",
    "python_code": "from modules.skills.base import BaseSkill, SkillResult\\nimport os\\n\\nclass GeneratedSkill(BaseSkill):\\n    @property\\n    def name(self): return 'remove_file'\\n    def execute(self, args):\\n        target = self._safe_path(args[1], args[0])\\n        try:\\n            os.remove(target)\\n            return SkillResult(True, 'Deleted', [], [f'(at {{args[0]}} {{args[1]}})'])\\n        except Exception as e:\\n            return SkillResult(False, str(e))",
    "test_args": ["test_dot_txt", "root"]
}}
"""
        # 调用真正的 DeepSeek 接口
        response = llm_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个严谨的系统底层专家，只输出 JSON。"},
                {"role": "user", "content": prompt}
            ],
            response_format={ 'type': 'json_object' } # 强制 JSON 输出
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        
        return json.loads(content)
        #return json.loads(response.choices[0].message.content)

    def _generate_final_report(self, goal):
        """
        你要求的失败总结报告
        """
        print("\n" + "!"*30)
        print("进化任务宣告失败 (已达重试上限)")
        print(f"任务目标: {goal}")
        print("-" * 30)
        print("【失败历程总结】:")
        for i, err in enumerate(self.history_errors):
            print(f"尝试 {i+1}: {err[:100]}...") # 截取关键报错
        print("-" * 30)
        print("【人工介入建议】:")
        print("1. 检查 Python 技能是否因为路径转义 (_dot_) 导致物理路径拼接错误。")
        print("2. 检查 PDDL 前提条件是否过于苛刻导致 Planner 拒绝生成路径。")
        print("3. 沙盒目录 sandbox_runs/ 中保留了最后一次生成的脚本，请手动调试。")
        print("!"*30 + "\n")