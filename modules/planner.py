import subprocess
import os
import re

class LAMAPlanner:
    def __init__(self, downward_path):
        """
        :param downward_path: fast-downward.py 的绝对路径
        """
        self.downward_path = downward_path
        # 定义 LAMA 算法的配置别名，'lama-first' 速度最快，适合实时交互
        self.alias = "lama-first" 

    def run_planning(self, domain_path, problem_path):
        """
        执行规划的核心函数
        对应伪代码中的: ChainOfAction, IfAble = LAMA(RuleBase, Mission)
        """
        search_cmd = (
            "lazy_greedy(["
            "ff(), "
            "landmark_sum(lm_factory=lm_rhw())"
            "], cost_type=normal)"
        )

        cmd = [
            "python3", self.downward_path,
            domain_path, problem_path,
            "--search", search_cmd
        ]
        # 清理旧的计划文件，防止读取到上一次的结果
        if os.path.exists("sas_plan"):
            os.remove("sas_plan")

        try:
            print(f"[*] Kernel calling LAMA: {' '.join(cmd)}")
            
            # 2. 启动子进程 (AIOS System Call)
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30 # 设置30秒超时，防止死循环
            )
            
            stdout = process.stdout
            stderr = process.stderr

            abcde = 1
            if (abcde == 0):
                # --- 运行时打印 LAMA 原始搜索日志，方便调试路径 ---
                print("\n" + ">"*20 + " [LAMA Search Log Start] " + ">"*20)
                if stdout:
                    print(stdout)
                if stderr:
                    print("--- Error Log (stderr) ---")
                    print(stderr)
                print(">"*20 + " [LAMA Search Log End] " + ">"*20 + "\n")
                # --------------------------------------------------

            # 3. 分析 LAMA 的返回结果
            if "Solution found." in stdout:
                chain_of_action = self._parse_plan("sas_plan")
                # 打印出找到的路径
                print(f"[Planner] 成功找到规划路径: {[a[0] for a in chain_of_action]}")
                return {
                    "if_able": True,
                    "chain_of_action": chain_of_action,
                    "error_msg": None
                }
            else:
                # 失败：提取错误信息 (eOfLAMA)
                error_context = self._extract_error(stdout, stderr)
                return {
                    "if_able": False,
                    "chain_of_action": [],
                    "error_msg": error_context
                }

        except subprocess.TimeoutExpired:
            return {
                "if_able": False, 
                "chain_of_action": [], 
                "error_msg": "System Error: LAMA Planning Timeout (Calculation took > 30s)"
            }
        except Exception as e:
            return {
                "if_able": False,
                "chain_of_action": [],
                "error_msg": f"System Error: {str(e)}"
            }

    def verify_domain(self, domain_path):
        """
        语法预检：利用 fast-downward 的 translate 脚本检查 PDDL 是否合法
        """

        # 创建一个临时的、最简单的 problem 文件来辅助检查
        temp_prob = os.path.join(os.path.dirname(domain_path), "syntax_check.pddl")
        with open(temp_prob, 'w') as f:
            f.write("(define (problem syntax_check) (:domain file-manager) (:objects x - file root - folder) (:init (at x root) (= (total-cost) 0)) (:goal (not (at x root))))")

        # 运行 translate 阶段（不进行搜索），仅验证语法
        # 命令格式: python3 fast-downward.py --translate domain.pddl problem.pddl
        cmd = ["python3", self.downward_path, "--translate", domain_path, temp_prob]
        
        try:
            # shell=False 更安全，capture_output 捕获错误日志
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if process.returncode != 0:
                # 提取 stderr 中的关键错误信息
                error_msg = process.stderr if process.stderr else process.stdout
                return {"is_valid": False, "error": error_msg.strip()}
            
            return {"is_valid": True, "error": None}
            
        except Exception as e:
            return {"is_valid": False, "error": f"预检过程抛出异常: {str(e)}"}
        finally:
            # 清理垃圾
            if os.path.exists("output.sas"): os.remove("output.sas")
            if os.path.exists(temp_prob): os.remove(temp_prob)

    def _parse_plan(self, plan_file):
        """
        解析 sas_plan 文件，转化为 Steps 数组
        """
        steps = []
        if os.path.exists(plan_file):
            with open(plan_file, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or line.startswith(";"): 
                        continue 
                    
                    # 原始格式: (move file_a folder_x folder_y)
                    # 清洗后: move file_a folder_x folder_y
                    action_str = line.replace("(", "").replace(")", "")
                    
                    # 转化为 [ActionString, StepNumber]
                    steps.append([action_str, i + 1])
            
            # 调试阶段建议保留 sas_plan 文件以便手动检查
            # os.remove(plan_file) 
            return steps
        return []

    def _extract_error(self, stdout, stderr):
        """
        智能错误提取，这是 FalseLLM 分析的基础
        """
        # 逻辑错误：搜索空间遍历完也没找到解
        if "Search stopped without finding a solution" in stdout:
            return "Logic Error: Goal is unreachable. (Possible: Missing prerequisites or incorrect initial state)"
        
        # 语法错误或解析错误
        if "syntax error" in stderr.lower() or "parse error" in stderr.lower() or "error" in stdout.lower():
            # 尝试从 stdout/stderr 中匹配具体的报错位置
            match = re.search(r"(syntax error.*?line \d+|parse error.*?line \d+)", stderr + stdout, re.IGNORECASE | re.DOTALL)
            if match:
                return f"PDDL Parser Error: {match.group(1)}"
            
            # 检查是否有未定义的谓词或类型
            if "undefined" in (stderr + stdout).lower():
                return "PDDL Undefined Error: Check if predicates/types match between Domain and Problem."

        return "Unknown LAMA Error: Check log above for 'LAMA Search Log' details."