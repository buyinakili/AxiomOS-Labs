"""HypothalamusFilter - 任务路由判断

根据伪代码逻辑层实现，判断用户任务是否可直接由Nerves层执行（简单任务），
还是需要经过Brain层分解（复杂任务）。
"""
import re
from typing import List, Set


class HypothalamusFilter:
    """下丘脑过滤器：任务路由决策"""
    
    # Nerves动作白名单（脊髓反射可直接执行的动作）
    NERVES_ACTION_WHITELIST = [
        "move", "delete", "copy", "read", "rename", "write",
        "scan", "compress", "uncompress", "create_file", "create_folder",
        "get_admin", "connect_folders", "remove"
    ]
    
    # 逻辑复杂度关键词（中文）
    LOGIC_KEYWORDS = ["如果", "所有", "除了", "且", "或", "当...时", "并且", "或者", "除非"]
    
    # 实体确定性模糊代词/通配符
    FUZZY_PRONOUNS = ["那个", "一些", "相关", "*", "所有", "某些", "任意", "每个"]
    
    # 语义复杂度阈值（简单实现：单词数量）
    SEMANTIC_COMPLEXITY_THRESHOLD = 10  # 单词数超过此值认为复杂
    
    def filter(self, task: str) -> str:
        """
        过滤任务，返回路由决策
        
        :param task: 用户任务描述（字符串）
        :return: "Route_To_Brain" 或 "Route_To_Nerves"
        """
        # 维度1: 动作原子性检查（提取动词并查表）
        verb = self._extract_verb(task)
        if verb not in self.NERVES_ACTION_WHITELIST:
            return "Route_To_Brain"
        
        # 维度2: 逻辑复杂度检查（检查逻辑连接词）
        if self._contains_logic_keywords(task):
            return "Route_To_Brain"
        
        # 维度3: 实体确定性检查（检查是否含有模糊代词或通配符）
        if self._contains_fuzzy_pronouns(task):
            return "Route_To_Brain"
        
        # 维度4: 语义跨度预判（通过极轻量模型或规则计算信息熵）
        if self._calculate_semantic_complexity(task) > self.SEMANTIC_COMPLEXITY_THRESHOLD:
            return "Route_To_Brain"
        
        # 所有检查通过，判定为简单任务，可跳过BrainLLM
        return "Route_To_Nerves"
    
    def _extract_verb(self, task: str) -> str:
        """
        提取任务中的主要动词（简化实现）
        
        :param task: 任务描述
        :return: 动词小写形式，如果未识别则返回空字符串
        """
        # 简单分词，取第一个单词作为动词（英文场景）
        words = task.strip().split()
        if not words:
            return ""
        
        # 如果是中文，尝试提取动词（这里简化处理）
        # 实际应使用更复杂的NLP，此处仅作示例
        first_word = words[0].lower()
        
        # 移除标点
        first_word = re.sub(r'[^\w]', '', first_word)
        
        # 映射常见中文动词到英文白名单
        chinese_to_english = {
            "移动": "move",
            "删除": "delete",
            "复制": "copy",
            "读取": "read",
            "重命名": "rename",
            "写入": "write",
            "扫描": "scan",
            "压缩": "compress",
            "解压": "uncompress",
            "创建文件": "create_file",
            "创建文件夹": "create_folder",
            "获取权限": "get_admin",
            "连接文件夹": "connect_folders",
            "移除": "remove",
        }
        
        if first_word in chinese_to_english:
            return chinese_to_english[first_word]
        
        # 检查是否直接是白名单中的英文动词
        if first_word in self.NERVES_ACTION_WHITELIST:
            return first_word
        
        # 尝试匹配任务中的动词模式
        for verb in self.NERVES_ACTION_WHITELIST:
            if verb in task.lower():
                return verb
        
        return ""
    
    def _contains_logic_keywords(self, task: str) -> bool:
        """检查任务是否包含逻辑关键词"""
        for keyword in self.LOGIC_KEYWORDS:
            if keyword in task:
                return True
        return False
    
    def _contains_fuzzy_pronouns(self, task: str) -> bool:
        """检查任务是否包含模糊代词或通配符"""
        for pronoun in self.FUZZY_PRONOUNS:
            if pronoun in task:
                return True
        return False
    
    def _calculate_semantic_complexity(self, task: str) -> int:
        """
        计算语义复杂度（简化：单词数量）
        
        :param task: 任务描述
        :return: 复杂度分数
        """
        # 简单实现：按空格分割单词数
        words = task.strip().split()
        return len(words)
    
    def is_nerves_action(self, verb: str) -> bool:
        """检查动词是否在Nerves白名单中"""
        return verb in self.NERVES_ACTION_WHITELIST


# 工厂函数
def create_hypothalamus_filter() -> HypothalamusFilter:
    """创建HypothalamusFilter实例"""
    return HypothalamusFilter()


# 测试代码
if __name__ == "__main__":
    filter = create_hypothalamus_filter()
    
    test_cases = [
        ("移动文件到备份文件夹", "Route_To_Nerves"),  # 简单动作
        ("如果文件存在则删除它", "Route_To_Brain"),   # 包含逻辑关键词
        ("删除那个文件", "Route_To_Brain"),          # 包含模糊代词
        ("扫描root文件夹", "Route_To_Nerves"),
        ("将所有txt文件复制到backup文件夹，并且压缩它们", "Route_To_Brain"),  # 复杂
    ]
    
    print("HypothalamusFilter测试:")
    for task, expected in test_cases:
        result = filter.filter(task)
        status = "✓" if result == expected else "✗"
        print(f"  {status} 任务: '{task}' => {result} (期望: {expected})")