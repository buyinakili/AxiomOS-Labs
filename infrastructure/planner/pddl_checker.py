"""PDDL检查器实现 - 验证PDDL动作序列的可达性并预测状态

提供BrainPDDLChecker和NervesPDDLChecker，对应伪代码逻辑层中的两个检查器函数。
"""
from typing import List, Tuple, Set, Optional, Dict, Any
import re
from interface.planner import IPlanner
from infrastructure.planner.lama_planner import LAMAPlanner


class PDDLCheckerBase:
    """PDDL检查器基类，提供通用的可达性验证和状态预测功能"""
    
    def __init__(self, planner: Optional[IPlanner] = None):
        """
        初始化检查器
        
        :param planner: 规划器实例，如果为None则创建默认的LAMAPlanner
        """
        self.planner = planner or LAMAPlanner()
        
        # 缓存领域内容
        self._domain_cache: Dict[str, str] = {}
        
    def load_domain(self, domain_file: str) -> str:
        """
        加载PDDL领域文件内容
        
        :param domain_file: 领域文件路径
        :return: 领域内容字符串
        """
        if domain_file in self._domain_cache:
            return self._domain_cache[domain_file]
        
        with open(domain_file, 'r') as f:
            content = f.read()
        
        self._domain_cache[domain_file] = content
        return content
    
    def check_sequence(
        self,
        actions: List[str],
        domain_content: str,
        initial_facts: Set[str],
        domain_name: str = "file-manager-extended"
    ) -> List[Tuple[bool, List[str]]]:
        """
        检查动作序列的可达性并返回每一步的预测状态
        
        :param actions: PDDL动作列表，如 ["(scan root)", "(move file1 root backup)"]
        :param domain_content: PDDL领域定义内容
        :param initial_facts: 初始环境事实集合
        :param domain_name: 领域名称（用于构建Problem）
        :return: 列表，每个元素为 (是否可达, 该步执行后的环境事实列表)
        """
        if not actions:
            return []
        
        # 调用状态模拟器
        simulator = PDDLStateSimulator(domain_content)
        current_state = set(initial_facts)
        results = []
        
        for i, action in enumerate(actions):
            # 检查动作是否可应用
            applicable, next_state = simulator.apply_action(action, current_state)
            if not applicable:
                # 如果不可应用，标记为不可达，并保持当前状态不变
                results.append((False, sorted(current_state)))
                # 后续动作都标记为不可达（因为序列中断）
                for _ in range(i + 1, len(actions)):
                    results.append((False, sorted(current_state)))
                return results
            else:
                results.append((True, sorted(next_state)))
                current_state = next_state
        
        return results
    
    def check_sequence_with_planner(
        self,
        actions: List[str],
        domain_content: str,
        initial_facts: Set[str],
        domain_name: str = "file-manager-extended"
    ) -> List[Tuple[bool, Set[str]]]:
        """
        使用规划器验证动作序列的可达性（更准确但较慢）
        
        为每个动作构建一个规划问题，检查从当前状态执行该动作是否可达。
        返回每一步的可达性和预测状态。
        """
        # 由于实现较复杂，暂不实现，留作扩展
        raise NotImplementedError("使用规划器的详细验证暂未实现")


class PDDLStateSimulator:
    """简单的PDDL状态模拟器，基于领域定义应用动作效果"""
    
    def __init__(self, domain_content: str):
        """
        初始化模拟器
        
        :param domain_content: PDDL领域内容
        """
        self.domain_content = domain_content
        # 解析动作效果（简化：硬编码已知动作的效果）
        self._init_action_effects()
    
    def _init_action_effects(self):
        """初始化动作效果映射（基于domain_extended.pddl）"""
        # 效果模式：对于每个动作，定义添加和删除的谓词模式
        # 格式：{动作名: (添加模式列表, 删除模式列表)}
        # 模式中使用 {0}, {1} 等占位符对应参数
        self.effects = {
            "scan": (
                ["(scanned {0})"],  # 添加
                []                  # 删除
            ),
            "move": (
                ["(at {0} {2})", "(is_created {0})"],  # 添加
                ["(at {0} {1})"]                      # 删除
            ),
            "remove": (
                [],                                   # 添加
                ["(at {0} {1})"]                      # 删除
            ),
            "rename": (
                ["(has_name {0} {2})", "(is_created {0})"],  # 添加
                ["(has_name {0} {1})"]                       # 删除
            ),
            "copy": (
                ["(at {1} {3})", "(is_copied {0} {1})", "(is_created {1})"],  # 添加
                []                                                           # 删除
            ),
            "compress": (
                ["(is_created {2})", "(at {2} {1})", "(is_compressed {0} {2})"],  # 添加
                []                                                               # 删除
            ),
            "uncompress": (
                ["(at {2} {1})", "(is_created {2})"],  # 添加
                ["(is_compressed {2} {0})"]            # 删除
            ),
            "create_file": (
                ["(at {0} {2})", "(has_name {0} {1})", "(is_created {0})"],  # 添加
                []                                                          # 删除
            ),
            "create_folder": (
                ["(is_empty {0})", "(is_created {0})"],  # 添加
                []                                      # 删除
            ),
            "get_admin": (
                ["(has_admin_rights)"],  # 添加
                []                       # 删除
            ),
            "connect_folders": (
                ["(connected {0} {1})", "(connected {1} {0})"],  # 添加
                []                                              # 删除
            ),
        }
    
    def parse_action(self, action_str: str) -> Tuple[str, List[str]]:
        """
        解析PDDL动作字符串
        
        :param action_str: 如 "(scan root)" 或 "(move file1 root backup)"
        :return: (动作名, 参数列表)
        """
        # 移除括号和多余空格
        action_str = action_str.strip()
        if action_str.startswith('(') and action_str.endswith(')'):
            action_str = action_str[1:-1]
        
        parts = action_str.split()
        if not parts:
            raise ValueError(f"无效的动作字符串: {action_str}")
        
        action_name = parts[0]
        params = parts[1:]
        return action_name, params
    
    def apply_action(self, action_str: str, state: Set[str]) -> Tuple[bool, Set[str]]:
        """
        尝试应用动作到当前状态，返回是否可应用及应用后的新状态
        
        :param action_str: PDDL动作字符串
        :param state: 当前状态事实集合
        :return: (是否可应用, 新状态)
        """
        try:
            action_name, params = self.parse_action(action_str)
        except ValueError:
            return False, state
        
        # 检查前置条件（简化：仅检查has_admin_rights）
        # 注意：实际应检查所有前置条件，这里为简化只检查管理员权限
        if action_name != "get_admin":
            if "(has_admin_rights)" not in state:
                return False, state
        
        # 检查动作是否在效果映射中
        if action_name not in self.effects:
            # 未知动作，假设不可应用
            return False, state
        
        add_patterns, del_patterns = self.effects[action_name]
        
        # 创建新状态副本
        new_state = set(state)
        
        # 应用删除效果
        for pattern in del_patterns:
            try:
                fact = pattern.format(*params)
                if fact in new_state:
                    new_state.remove(fact)
            except (IndexError, KeyError):
                # 参数不匹配，忽略
                pass
        
        # 应用添加效果
        for pattern in add_patterns:
            try:
                fact = pattern.format(*params)
                new_state.add(fact)
            except (IndexError, KeyError):
                # 参数不匹配，忽略
                pass
        
        return True, new_state


class BrainPDDLChecker:
    """Brain层PDDL检查器 - 验证高层任务链的可达性"""
    
    def __init__(self, planner: Optional[IPlanner] = None):
        """
        初始化BrainPDDLChecker
        
        :param planner: 规划器实例
        """
        self.base_checker = PDDLCheckerBase(planner)
        # Brain层使用固定的领域文件
        self.domain_file = "cot_generator/pddl_configs/domain_extended.pddl"
    
    def check(self, actions: List[str], initial_facts: Set[str]) -> List[Tuple[bool, List[str]]]:
        """
        检查PDDL动作序列的可达性（Brain层接口）
        
        :param actions: PDDL动作列表
        :param initial_facts: 初始环境事实集合
        :return: 列表，每个元素为 (是否可达, 该步执行后的环境事实列表)
        """
        domain_content = self.base_checker.load_domain(self.domain_file)
        return self.base_checker.check_sequence(actions, domain_content, initial_facts)


class NervesPDDLChecker:
    """Nerves层PDDL检查器 - 验证原子动作链的可达性"""
    
    def __init__(self, planner: Optional[IPlanner] = None):
        """
        初始化NervesPDDLChecker
        
        :param planner: 规划器实例
        """
        self.base_checker = PDDLCheckerBase(planner)
        # Nerves层可以接受不同的领域，默认使用扩展领域
        self.default_domain_file = "cot_generator/pddl_configs/domain_extended.pddl"
    
    def check(self, actions: List[str], domain: str, initial_facts: Set[str]) -> List[Tuple[bool, List[str]]]:
        """
        检查PDDL动作序列的可达性（Nerves层接口）
        
        :param actions: PDDL动作列表
        :param domain: 领域名称或领域文件路径
        :param initial_facts: 初始环境事实集合
        :return: 列表，每个元素为 (是否可达, 该步执行后的环境事实列表)
        """
        # 如果domain是文件路径，加载文件内容；否则使用默认领域
        if domain.endswith('.pddl'):
            domain_content = self.base_checker.load_domain(domain)
        else:
            # 假设domain是领域名称，使用默认文件
            domain_content = self.base_checker.load_domain(self.default_domain_file)
        
        return self.base_checker.check_sequence(actions, domain_content, initial_facts)


# 工厂函数，便于创建检查器实例
def create_brain_pddl_checker(planner: Optional[IPlanner] = None) -> BrainPDDLChecker:
    """创建BrainPDDLChecker实例"""
    return BrainPDDLChecker(planner)

def create_nerves_pddl_checker(planner: Optional[IPlanner] = None) -> NervesPDDLChecker:
    """创建NervesPDDLChecker实例"""
    return NervesPDDLChecker(planner)


# 测试代码
if __name__ == "__main__":
    # 简单测试
    initial_facts = {
        "(has_admin_rights)",
        "(at file1 root)",
        "(connected root backup)",
    }
    
    actions = [
        "(scan root)",
        "(move file1 root backup)",
    ]
    
    brain_checker = create_brain_pddl_checker()
    results = brain_checker.check(actions, initial_facts)
    
    print("BrainPDDLChecker测试:")
    for i, (reachable, state) in enumerate(results):
        print(f"  步骤 {i+1} ({actions[i]}): 可达={reachable}, 状态大小={len(state)}")
        if reachable:
            print(f"    状态示例: {list(state)[:3]}")
    
    nerves_checker = create_nerves_pddl_checker()
    results2 = nerves_checker.check(actions, "file_management", initial_facts)
    
    print("\nNervesPDDLChecker测试:")
    for i, (reachable, state) in enumerate(results2):
        print(f"  步骤 {i+1} ({actions[i]}): 可达={reachable}, 状态大小={len(state)}")