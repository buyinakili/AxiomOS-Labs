import os
import re
import shutil
from openai import OpenAI
from modules.translator import PDDLTranslator
from modules.planner import LAMAPlanner
from modules.executor import ActionExecutor

class AIOSKernel:
    def __init__(self, translator, planner, executor, max_iter=5):
        self.translator = translator
        self.planner = planner
        self.executor = executor # 现在接收的是 ActionExecutor 实例
        self.domain_path = "tests/domain.pddl"
        self.prob_path = "tests/generated_problem.pddl"
        # 优化：使用 set 存储 PDDL 格式的事实，确保唯一性
        self.memory_facts = set() 
        self.max_iter = max_iter
        self.current_domain = None

    def _extract_goal_predicates(self, problem_pddl: str) -> list:
        """
        从生成的 PDDL Problem 文本中粗略提取 (:goal ...) 块中的谓词。
        这是一种简单的字符串解析方案。
        """
        # 匹配 (:goal (and ... )) 或 (:goal (predicate ...))
        goal_match = re.search(r'\(:goal\s+\(and\s+(.*?)\s*\)\s*\)', problem_pddl, re.DOTALL)
        if not goal_match:
            # 尝试匹配非 and 的单目标
            goal_match = re.search(r'\(:goal\s+(.*?)\s*\)', problem_pddl, re.DOTALL)
        
        if goal_match:
            goal_content = goal_match.group(1).strip()
            # 分割出具体的谓词
            # 这里使用正则匹配括号对
            predicates = re.findall(r'\(.*?\)', goal_content)
            return [p.strip() for p in predicates]
        return []

    def run(self, user_goal):
        if not hasattr(self, 'current_domain') or self.current_domain is None:
            self.current_domain = self.translator.route_task(user_goal)
            print(f"[Kernel] 路由判定成功：进入 [{self.current_domain}] 专家模式")

        for i in range(self.max_iter):
            print(f"\n{'='*10} 迭代 {i+1} ({self.current_domain}) {'='*10}")
            if i > 0: # 第一次通常由用户触发 scan，后面每轮强制同步
                print(f"[Kernel] 正在进行迭代前物理状态同步...")
                sync_result = self.executor.execute_step("scan", ["root"]) 
                if sync_result.is_success:
                    self.memory_facts.update(sync_result.add_facts)
            # 构造上下文：直接将 set 中的 PDDL Predicates 传给 LLM
            facts_str = "\n".join(sorted(list(self.memory_facts))) if self.memory_facts else "未知"
            memory_context = f"""用户最终目标: {user_goal}\n【当前已知环境事实 (PDDL Predicates)】:\n{facts_str},如果上述事实已经表明目标文件不存在、或者已经满足了用户的删除/移动等需求，
            请不要生成任何 PDDL，直接回复：GOAL_FINISHED_ALREADY"""
            print(facts_str)
            
            problem_pddl = self.translator.generate_problem(memory_context, self.current_domain)
            goal_predicates = self._extract_goal_predicates(problem_pddl)
            if goal_predicates:
                # 检查是否所有目标谓词都已在内存事实中
                is_all_achieved = True
                for gp in goal_predicates:
                    # 去掉多余空格进行比较
                    if gp not in self.memory_facts:
                        is_all_achieved = False
                        break
                
                if is_all_achieved:
                    print(f"[Kernel] 预检拦截：检测到 LLM 生成的目标 {goal_predicates} 均已在事实库中达成。")
                    print(f"[Kernel] 判定为任务完成。")
                    return True
            # --- 预检逻辑结束 ---

            if "GOAL_FINISHED_ALREADY" in problem_pddl:
                print(f"[Kernel] 任务完成：环境状态已满足目标。")
                return True
            
            self.translator.save_pddl(problem_pddl, self.prob_path)
            #current_domain_path = self.translator.experts[self.current_domain]["domain_file"]
            res = self.planner.run_planning(self.domain_path, self.prob_path)
            
            if not res['if_able']:
                print(f"[Kernel] 规划受阻: {res['error_msg']}")
                # 将错误作为一种负面事实记录，引导 LLM 调整策略
                self.memory_facts.add(f"; Logic Feedback: {res['error_msg']}")
                continue 

            # 检查规划路径是否为空。如果为空，说明目标已达成。
            if not res['chain_of_action']:
                print(f"[Kernel] 规划器报告：当前状态已满足目标，无需执行额外动作。")
                return True

            # 获取完整的规划链条 (ChainOfAction)
            chain = res['chain_of_action']
            print(f"[Kernel] 收到规划链条，包含 {len(chain)} 个步骤。开始自动执行...")

            chain_success = True
            for action_str, step_num in chain:
                parts = action_str.split()
                verb = parts[0]
                args = parts[1:]

                # 执行当前 Steps
                result = self.executor.execute_step(verb, args)
                
                if result.is_success:
                    print(f"[Kernel] 步骤 {step_num} 执行成功: {result.message}")
    
                    # 1. 严格遵循技能汇报的删除事实
                    if hasattr(result, 'del_facts') and result.del_facts:
                        for df in result.del_facts:
                            if df in self.memory_facts:
                                self.memory_facts.remove(df)
                                print(f"[Kernel] 遵循技能指令，已从事实库移除: {df}")
                                    # 合并新事实
                    self.memory_facts.update(result.add_facts)
                else:
                    print(f"[Kernel] 步骤 {step_num} 执行失败: {result.message}")
                    # 这里的失败会触发你文档中的 FalseLLM 逻辑
                    self.memory_facts.add(f"; Error: {result.message}")
                    chain_success = False
                    break # 阻断链条，进入下一轮迭代重新规划

            if chain_success:
                print(f"[Kernel] 链条执行完毕，等待下一轮验证。")
                continue
        
        print(f"[Kernel] 达到最大迭代次数，任务未完成。")
        return False

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DOWNWARD_PATH

if __name__ == "__main__":
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    translator = PDDLTranslator(client)
    planner = LAMAPlanner(DOWNWARD_PATH)
    
    from modules.executor import ActionExecutor
    executor = ActionExecutor() 
    
    kernel = AIOSKernel(translator, planner, executor)

    #kernel.run("把root下的txt文件移动到backup文件夹下")
    #kernel.run("把backup下的txt文件移动到root文件夹下")
    #kernel.run("删除 root 下的 txt 文件")
    kernel.run("重命名root下的txt文件为new.txt")
    #kernel.run("帮我在backup目录里创建一个bad文件夹，然后创建一个good.txt文件放在里面，然后再把root里面的txt文件移动到bad文件夹里")
    #python3 main_demo.py