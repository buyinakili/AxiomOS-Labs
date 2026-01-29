"""LAMA规划器实现"""
import subprocess
import os
import re
from typing import Tuple, Optional
from interface.planner import IPlanner, PlanningResult
from config.settings import Settings


class LAMAPlanner(IPlanner):
    """基于Fast Downward的LAMA规划器实现"""

    def __init__(self, config: Optional[Settings] = None, temp_dir: str = None, timeout: int = None):
        """
        初始化LAMA规划器

        :param config: 系统配置，如果为None则使用默认配置
        :param temp_dir: 临时文件目录，如果为None则使用配置中的temp_dir
        :param timeout: 规划超时时间（秒），如果为None则使用配置中的planning_timeout
        """
        self.config = config or Settings.load_from_env()
        self.downward_path = self.config.downward_path
        self.temp_dir = temp_dir or self.config.temp_dir
        self.timeout = timeout or self.config.planning_timeout
        self.alias = "lama-first"

        # 确保临时目录存在
        os.makedirs(self.temp_dir, exist_ok=True)

    def plan(self, domain_content: str, problem_content: str) -> PlanningResult:
        """
        执行规划

        :param domain_content: Domain PDDL内容
        :param problem_content: Problem PDDL内容
        :return: PlanningResult对象
        """
        # 写临时文件
        domain_file = os.path.join(self.temp_dir, "temp_domain.pddl")
        problem_file = os.path.join(self.temp_dir, "temp_problem.pddl")
        plan_file = os.path.join(self.temp_dir, "sas_plan")

        with open(domain_file, "w") as f:
            f.write(domain_content)
        with open(problem_file, "w") as f:
            f.write(problem_content)

        # 清理旧的计划文件
        if os.path.exists(plan_file):
            os.remove(plan_file)

        # 构建命令
        search_cmd = (
            "lazy_greedy(["
            "ff(), "
            "landmark_sum(lm_factory=lm_rhw())"
            "], cost_type=normal)"
        )

        cmd = [
            "python3", self.downward_path,
            domain_file, problem_file,
            "--search", search_cmd
        ]

        try:
            print(f"[LAMA] 开始规划...")

            # 执行规划
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.temp_dir
            )

            stdout = process.stdout
            stderr = process.stderr

            # 分析结果
            if "Solution found." in stdout:
                actions = self._parse_plan(plan_file)
                print(f"[LAMA] 规划成功，找到 {len(actions)} 个步骤")
                return PlanningResult(
                    success=True,
                    actions=actions,
                    error=None
                )
            else:
                error_msg = self._extract_error(stdout, stderr)
                print(f"[LAMA] 规划失败: {error_msg}")
                return PlanningResult(
                    success=False,
                    actions=[],
                    error=error_msg
                )

        except subprocess.TimeoutExpired:
            return PlanningResult(
                success=False,
                actions=[],
                error=f"规划超时（超过{self.timeout}秒）"
            )
        except Exception as e:
            return PlanningResult(
                success=False,
                actions=[],
                error=f"系统错误: {str(e)}"
            )

    def verify_syntax(self, domain_content: str) -> Tuple[bool, str]:
        """
        验证PDDL语法

        :param domain_content: Domain PDDL内容
        :return: (is_valid, error_message)
        """
        # 创建临时文件
        domain_file = os.path.join(self.temp_dir, "syntax_check_domain.pddl")
        problem_file = os.path.join(self.temp_dir, "syntax_check_problem.pddl")

        with open(domain_file, "w") as f:
            f.write(domain_content)

        # 创建最简单的Problem用于语法检查
        minimal_problem = (
            "(define (problem syntax_check) "
            "(:domain file-manager) "
            "(:objects x - file root - folder) "
            "(:init (at x root) (= (total-cost) 0)) "
            "(:goal (not (at x root))))"
        )
        with open(problem_file, "w") as f:
            f.write(minimal_problem)

        # 运行translate阶段 - 使用绝对路径，不在temp_dir中执行
        cmd = ["python3", os.path.abspath(self.downward_path), "--translate",
               os.path.abspath(domain_file), os.path.abspath(problem_file)]

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,  # 使用配置的超时值
                cwd=os.path.dirname(os.path.abspath(self.downward_path))  # 在downward目录中执行
            )

            if process.returncode != 0:
                error_msg = process.stderr if process.stderr else process.stdout
                return (False, error_msg.strip())

            return (True, "")

        except Exception as e:
            return (False, f"语法检查异常: {str(e)}")
        finally:
            # 清理临时文件
            output_sas = os.path.join(self.temp_dir, "output.sas")
            if os.path.exists(output_sas):
                os.remove(output_sas)

    def _parse_plan(self, plan_file: str) -> list:
        """
        解析sas_plan文件

        :param plan_file: 计划文件路径
        :return: [(action_str, step_num), ...]
        """
        steps = []
        if os.path.exists(plan_file):
            with open(plan_file, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or line.startswith(";"):
                        continue

                    # 移除括号
                    action_str = line.replace("(", "").replace(")", "")
                    steps.append((action_str, i + 1))

        return steps

    def _extract_error(self, stdout: str, stderr: str) -> str:
        """
        提取错误信息

        :param stdout: 标准输出
        :param stderr: 错误输出
        :return: 错误描述
        """
        if "Search stopped without finding a solution" in stdout:
            return "目标不可达（可能缺少前提条件或初始状态不正确）"

        if "syntax error" in stderr.lower() or "parse error" in stderr.lower():
            match = re.search(
                r"(syntax error.*?line \d+|parse error.*?line \d+)",
                stderr + stdout,
                re.IGNORECASE | re.DOTALL
            )
            if match:
                return f"PDDL语法错误: {match.group(1)}"

        if "undefined" in (stderr + stdout).lower():
            return "PDDL未定义错误: 检查谓词/类型是否在Domain和Problem中匹配"

        return "未知LAMA错误，请查看日志"
