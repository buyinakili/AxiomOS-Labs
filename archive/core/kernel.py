# core/kernel.py
class AIOSKernel:
    def __init__(self, translator, planner, executor):
        self.translator = translator
        self.planner = planner
        self.executor = executor

    def run_mission(self, user_query):
        print(f"\n>>> 启动任务: {user_query}")
        
        # 1. 初始规划
        with open("tests/domain.pddl", "r") as f:
            domain_content = f.read()
        
        problem_pddl = self.translator.generate_problem(user_query, domain_content)
        self.translator.save_pddl(problem_pddl, "tests/generated_problem.pddl")
        
        plan_result = self.planner.run_planning("tests/domain.pddl", "tests/generated_problem.pddl")
        
        if not plan_result['if_able']:
            print("Planner 直接报错，可能是初始指令就不合逻辑。")
            return

        # 2. 执行循环
        chain = plan_result['chain_of_action']
        for step_content, step_num in chain:
            success, error_msg = self.executor.execute_step(step_content)
            
            if not success:
                # --- 触发 FalseLLM / SaveLLM 补救逻辑 ---
                print(f"\n[Kernel] 检测到执行失败！激活递归补救流程...")
                print(f"[Kernel] 错误分析: {error_msg}")
                
                # 让 DeepSeek 生成补救目标（SaveMission）
                recovery_query = f"刚才执行 '{step_content}' 失败了，错误是 '{error_msg}'。请给出修复这个问题的指令。"
                print(f"[Kernel] 咨询 DeepSeek 补救方案中...")
                
                # 递归：重新生成补救 PDDL 并执行
                self.run_mission(recovery_query)
                
                # 补救完成后，重新执行当前失败的步骤
                print(f"\n[Kernel] 补救任务完成，尝试恢复主任务...")
                self.run_mission(user_query)
                break