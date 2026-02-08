"""CoT数据生成器主控制流

实现伪代码逻辑层集成翻译器版中的主循环，协调HypothalamusFilter、BrainLLM、NervesLLM、
Translator、PDDLChecker、技能执行器等组件，生成完整的Chain-of-Thought数据。
"""
import sys
import os
from typing import List, Set, Dict, Any, Optional, Tuple
import asyncio

# 导入现有组件
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithm.hypothalamus_filter import create_hypothalamus_filter
from infrastructure.llm.brain_llm import create_brain_llm
from infrastructure.llm.nerves_llm import create_nerves_llm
from infrastructure.llm.analysis_llm import create_analysis_llm
from infrastructure.translator.granularity_translator import (
    create_nerves2brain_translator,
    create_brain2nerves_translator,
)
from infrastructure.planner.pddl_checker import (
    create_brain_pddl_checker,
    create_nerves_pddl_checker,
)
from infrastructure.executor.mcp_executor import MCPActionExecutorRefactored as MCPExecutor
from interface.llm import ILLM
from interface.planner import IPlanner


class CoTDataGenerator:
    """CoT数据生成器主类"""
    
    def __init__(
        self,
        llm: ILLM,
        planner: Optional[IPlanner] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化数据生成器
        
        :param llm: 基础LLM客户端
        :param planner: 规划器实例（可选）
        :param config: 配置字典
        """
        self.config = config or {}
        self.llm = llm
        
        # 初始化各组件
        self.hypothalamus_filter = create_hypothalamus_filter()
        self.brain_llm = create_brain_llm(llm)
        self.nerves_llm = create_nerves_llm(llm)
        self.analysis_llm = create_analysis_llm(llm)
        self.n2b_translator = create_nerves2brain_translator()
        self.b2n_translator = create_brain2nerves_translator()
        self.brain_checker = create_brain_pddl_checker(planner)
        self.nerves_checker = create_nerves_pddl_checker(planner)
        self.executor = MCPExecutor()  # 注意：可能需要配置
        
        # 环境变量（来自伪代码）
        self.brian_false_limit = self.config.get("brian_false_limit", 3)
        self.nerves_false_limit = self.config.get("nerves_false_limit", 3)
        
        # 状态变量
        self.brain_false_times = 0
        self.nerves_false_times = 0
        self.if_env_change = False
        self.change_information = ""
    
    def generate(self, user_task: str) -> Dict[str, Any]:
        """
        生成CoT数据的主入口点
        
        :param user_task: 用户任务描述
        :return: 包含完整CoT数据的字典
        """
        # 重置状态
        self.brain_false_times = 0
        self.nerves_false_times = 0
        self.if_env_change = False
        self.change_information = ""
        
        # 步骤1: HypothalamusFilter路由判断
        route = self.hypothalamus_filter.filter(user_task)
        
        if route == "Route_To_Nerves":
            # 直接进入脊髓反射处理流程
            result = self._process_nerves_only(user_task)
        else:
            # 进入Brain+Nerves双层处理流程
            result = self._process_brain_nerves(user_task)
        
        return result
    
    def _process_nerves_only(self, user_task: str) -> Dict[str, Any]:
        """
        处理仅需Nerves层的简单任务
        
        :param user_task: 用户任务
        :return: CoT数据
        """
        # 初始化数据收集
        cot_data = {
            "task": user_task,
            "route": "Route_To_Nerves",
            "brain_layer": {},  # 空Brain层
            "nerves_layers": [],
            "execution_trace": [],
            "success": False,
            "error_messages": [],
        }
        
        # 重置Nerves失败次数
        self.nerves_false_times = 0
        
        # 重试循环
        while self.nerves_false_times < self.nerves_false_limit:
            try:
                # 扫描环境（简化：使用默认环境）
                nerves_start_env = self._scan_environment()
                
                # 获取领域（简化：固定为文件管理）
                domain = "file_management"
                
                # NervesLLM分解为原子动作
                chain_of_action = self.nerves_llm.decompose_action(
                    task=user_task,
                    current_facts=nerves_start_env,
                    domain=domain,
                    previous_failure_reason=None
                )
                print(f"[DEBUG _process_nerves_only] chain_of_action: {chain_of_action}")
                
                # 检查动作可执行性
                if_action_can_execute = self.nerves_checker.check(
                    chain_of_action, domain, nerves_start_env
                )
                print(f"[DEBUG _process_nerves_only] if_action_can_execute: {if_action_can_execute}")
                
                # 验证所有动作可达
                for i, (reachable, state) in enumerate(if_action_can_execute):
                    if not reachable:
                        raise ValueError(f"动作 {chain_of_action[i]} 不可达")
                
                # 执行原子动作
                execution_trace = []
                for i, action in enumerate(chain_of_action):
                    # 执行动作
                    exec_result = self.executor.execute(action)
                    execution_trace.append({
                        "step": i,
                        "action": action,
                        "result": exec_result.success,
                        "message": exec_result.message,
                        "add_facts": exec_result.add_facts,
                        "del_facts": exec_result.del_facts,
                    })
                    print(f"[DEBUG _process_nerves_only] 执行动作 {i}: {action}, 结果: {exec_result.success}")
                
                # 构建Nerves层数据
                nerves_layer_data = {
                    "task": user_task,
                    "task_index": 0,
                    "start_env": list(nerves_start_env),
                    "chain_of_action": chain_of_action,
                    "action_reachability": [
                        {"reachable": reachable, "state": state}
                        for reachable, state in if_action_can_execute
                    ],
                    "execution_trace": execution_trace,
                    "success": True,
                }
                
                cot_data["nerves_layers"].append(nerves_layer_data)
                cot_data["execution_trace"].extend(execution_trace)
                cot_data["success"] = True
                print(f"[DEBUG _process_nerves_only] 成功生成CoT数据，步骤数: {len(execution_trace)}")
                
                return cot_data
                
            except Exception as e:
                print(f"[DEBUG _process_nerves_only] 异常捕获: {e}")
                self.nerves_false_times += 1
                cot_data["error_messages"].append(f"Nerves层失败 {self.nerves_false_times}: {str(e)}")
                if self.nerves_false_times >= self.nerves_false_limit:
                    cot_data["error_messages"].append("Nerves层重试次数超限，任务失败")
                    print(f"[DEBUG _process_nerves_only] 重试次数超限，任务失败")
                    break
                # 准备重试（简化：继续循环）
                continue
        
        return cot_data
    
    def _process_brain_nerves(self, user_task: str) -> Dict[str, Any]:
        """
        处理需要Brain+Nerves双层规划的复杂任务
        
        :param user_task: 用户任务
        :return: CoT数据
        """
        # 初始化数据收集
        cot_data = {
            "task": user_task,
            "route": "Route_To_Brain",
            "brain_layer": {},
            "nerves_layers": [],
            "execution_trace": [],
            "success": False,
            "error_messages": [],
        }
        
        # 重试循环
        while self.brain_false_times < self.brian_false_limit:
            try:
                # 扫描环境（简化：使用空环境）
                brain_start_env = self._scan_environment()
                cot_data["brain_layer"]["start_env"] = list(brain_start_env)
                
                # BrainLLM分解任务
                chain_of_mission = self.brain_llm.decompose_task(
                    user_goal=user_task,
                    current_facts=brain_start_env,
                    available_actions=self._get_available_actions("file_management"),
                    previous_failure_reason=self.change_information if self.if_env_change else None
                )
                cot_data["brain_layer"]["chain_of_mission"] = chain_of_mission
                
                # 检查语法（简化：假设PDDL格式正确）
                # 检查任务可执行性
                if_task_can_execute = self.brain_checker.check(
                    chain_of_mission, brain_start_env
                )
                cot_data["brain_layer"]["mission_reachability"] = [
                    {"reachable": reachable, "state": state}
                    for reachable, state in if_task_can_execute
                ]
                
                # 调试信息：显示每个任务的可达性
                if self.config.get("debug", False):
                    print(f"[CoT Debug] 可达性检查结果:")
                    for i, (reachable, state) in enumerate(if_task_can_execute):
                        print(f"  任务 {i+1}: {chain_of_mission[i]} -> 可达: {reachable}")
                        if not reachable:
                            print(f"    当前状态: {state[:5]}...")  # 只显示前5个事实
                
                # 验证所有任务可达
                for i, (reachable, state) in enumerate(if_task_can_execute):
                    if not reachable:
                        raise ValueError(f"任务 {chain_of_mission[i]} 不可达")
                
                # 执行每一个分解任务
                for i, task in enumerate(chain_of_mission):
                    task_result = self._process_single_task(
                        task=task,
                        task_index=i,
                        start_env=if_task_can_execute[i][1],  # 上一步结束的状态
                        cot_data=cot_data
                    )
                    if not task_result.get("success", True):
                        # 任务失败，触发重试机制
                        self._handle_task_failure(task, i, cot_data)
                        break
                
                # 所有任务成功完成
                cot_data["success"] = True
                return cot_data
                
            except Exception as e:
                self.brain_false_times += 1
                cot_data["error_messages"].append(f"Brain层失败 {self.brain_false_times}: {str(e)}")
                if self.brain_false_times >= self.brian_false_limit:
                    cot_data["error_messages"].append("Brain层重试次数超限，任务失败")
                    break
                # 准备重试（简化：仅记录错误）
                # 实际应调用AnalysisLLM生成修复建议
                continue
        
        return cot_data
    
    def _process_single_task(
        self,
        task: str,
        task_index: int,
        start_env: List[str],
        cot_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理单个分解任务（调用Nerves层）
        
        :param task: PDDL格式任务
        :param task_index: 任务索引
        :param start_env: 起始环境事实列表
        :param cot_data: 累积的CoT数据
        :return: 处理结果字典
        """
        nerves_layer_data = {
            "task": task,
            "task_index": task_index,
            "start_env": start_env,
            "success": False,
        }
        
        # 重置Nerves失败次数
        self.nerves_false_times = 0
        
        # 重试循环
        while self.nerves_false_times < self.nerves_false_limit:
            try:
                # 扫描环境（使用起始环境）
                nerves_start_env = set(start_env)
                
                # 获取领域（简化：固定为文件管理）
                domain = "file_management"
                
                # NervesLLM分解为原子动作
                chain_of_action = self.nerves_llm.decompose_action(
                    task=task,
                    current_facts=nerves_start_env,
                    domain=domain,
                    previous_failure_reason=None  # 可扩展
                )
                nerves_layer_data["chain_of_action"] = chain_of_action
                
                # 检查动作可执行性
                if_action_can_execute = self.nerves_checker.check(
                    chain_of_action, domain, nerves_start_env
                )
                nerves_layer_data["action_reachability"] = [
                    {"reachable": reachable, "state": state}
                    for reachable, state in if_action_can_execute
                ]
                
                # 验证所有动作可达
                for i, (reachable, state) in enumerate(if_action_can_execute):
                    if not reachable:
                        raise ValueError(f"动作 {chain_of_action[i]} 不可达")
                
                # 执行原子动作
                execution_trace = []
                for i, action in enumerate(chain_of_action):
                    # 执行动作
                    exec_result = self.executor.execute(action)
                    execution_trace.append({
                        "step": i,
                        "action": action,
                        "result": exec_result.success,
                        "message": exec_result.message,
                        "add_facts": exec_result.add_facts,
                        "del_facts": exec_result.del_facts,
                    })
                    
                    # 检查执行结果是否与预期状态一致
                    # 简化：仅记录
                
                nerves_layer_data["execution_trace"] = execution_trace
                nerves_layer_data["success"] = True
                
                # 添加到总数据
                cot_data["nerves_layers"].append(nerves_layer_data)
                cot_data["execution_trace"].extend(execution_trace)
                
                return nerves_layer_data
                
            except Exception as e:
                self.nerves_false_times += 1
                nerves_layer_data["error"] = f"Nerves层失败 {self.nerves_false_times}: {str(e)}"
                if self.nerves_false_times >= self.nerves_false_limit:
                    # Nerves失败次数超限，向上层报告失败
                    raise
                # 准备重试（简化：继续循环）
                continue
        
        # 如果循环结束仍未成功，返回失败
        nerves_layer_data["success"] = False
        return nerves_layer_data
    
    def _scan_environment(self) -> Set[str]:
        """
        扫描环境，返回当前环境事实
        
        调用真实的Scan技能获取沙盒环境中的实际文件结构。
        扫描当前目录（沙盒根目录），而不是硬编码的"root"文件夹。
        
        :return: 环境事实集合
        """
        try:
            # 首先确保有管理员权限（Scan技能需要has_admin_rights）
            admin_result = self.executor.execute("(get_admin)")
            if not admin_result.success:
                # 如果获取管理员权限失败，记录警告但继续尝试扫描
                print(f"[WARNING] 获取管理员权限失败: {admin_result.message}")
            
            # 执行扫描当前目录（沙盒根目录）
            # 使用"."表示当前目录，Scan技能会将其转换为物理路径
            scan_result = self.executor.execute("(scan .)")
            if not scan_result.success:
                # 扫描失败，返回空集合（让后续流程处理错误）
                print(f"[ERROR] 扫描环境失败: {scan_result.message}")
                return set()
            
            # 从扫描结果中提取事实
            # scan_result.add_facts 包含Scan技能返回的所有PDDL事实
            facts = set()
            if scan_result.add_facts:
                facts.update(scan_result.add_facts)
            
            # 确保包含has_admin_rights事实（如果get_admin成功）
            if admin_result.success:
                facts.add("(has_admin_rights)")
            
            # 不再添加硬编码的"(is_created root)"事实
            # 让Scan技能返回实际扫描到的事实
            
            print(f"[INFO] 环境扫描完成，获取到 {len(facts)} 个事实")
            return facts
            
        except Exception as e:
            print(f"[ERROR] 环境扫描异常: {e}")
            # 返回空集合，让调用者处理
            return set()
    
    def _get_available_actions(self, domain: str) -> List[str]:
        """
        获取指定领域可用的动作列表
        
        :param domain: 领域名称
        :return: PDDL动作字符串列表
        """
        # 简化：返回文件管理领域的动作
        if domain == "file_management":
            return [
                "(scan ?d)",
                "(move ?f ?src ?dst)",
                "(remove ?f ?d)",
                "(rename ?f ?old_name ?new_name ?d)",
                "(copy ?src ?dst ?src_folder ?dst_folder)",
                "(compress ?f ?d ?a)",
                "(uncompress ?a ?d ?f)",
                "(create_file ?f ?name ?d)",
                "(create_folder ?d ?parent)",
                "(get_admin)",
                "(connect_folders ?d1 ?d2)",
            ]
        return []
    
    def _handle_task_failure(self, task: str, task_index: int, cot_data: Dict[str, Any]):
        """
        处理任务失败（简化实现）
        
        :param task: 失败的任务
        :param task_index: 任务索引
        :param cot_data: CoT数据
        """
        # 记录失败
        cot_data["error_messages"].append(f"任务 {task} 执行失败")
        # 设置环境变化标志（简化）
        self.if_env_change = True
        self.change_information = f"任务 {task} 失败，需要重新规划"


# 工厂函数
def create_cot_data_generator(
    llm: ILLM,
    planner: Optional[IPlanner] = None,
    config: Optional[Dict[str, Any]] = None
) -> CoTDataGenerator:
    """创建CoT数据生成器实例"""
    return CoTDataGenerator(llm, planner, config)


# 测试代码
if __name__ == "__main__":
    # 模拟LLM（测试用）
    class MockLLM:
        def chat(self, messages, temperature=0.1):
            # 返回模拟响应
            return "(scan root)\n(move file1 root backup)"
    
    mock_llm = MockLLM()
    
    generator = create_cot_data_generator(mock_llm)
    
    # 测试简单任务
    test_task = "扫描root文件夹并将file1移动到backup"
    result = generator.generate(test_task)
    
    print("CoT数据生成器测试:")
    print(f"任务: {result['task']}")
    print(f"路由: {result['route']}")
    print(f"成功: {result.get('success', False)}")
    if "error_messages" in result and result["error_messages"]:
        print(f"错误: {result['error_messages']}")