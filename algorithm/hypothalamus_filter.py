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
    
    # 逻辑复杂度关键词（中文）- 真正的逻辑连接词
    LOGIC_KEYWORDS = ["如果", "且", "或", "当...时", "并且", "或者", "除非", "则", "否则", "那么"]
    
    # 实体确定性模糊代词/通配符 - 移除"所有"，因为它不是模糊代词
    FUZZY_PRONOUNS = ["那个", "一些", "相关", "*", "某些", "任意", "每个", "它", "它们", "这个", "这些"]
    
    # 语义复杂度阈值（基于字符数，中文任务通常字符较少）
    SEMANTIC_COMPLEXITY_THRESHOLD = 25  # 字符数超过此值认为复杂，提高阈值避免过度路由到Brain
    
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
        提取任务中的主要动词（改进版，支持中文动词提取，避免从文件名中提取）
        
        :param task: 任务描述
        :return: 动词小写形式，如果未识别则返回空字符串
        """
        task_lower = task.lower()
        
        # 扩展的中文动词到英文白名单映射
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
            "创建": "create_file",  # 匹配"创建文件"或"创建文件夹"
            "创建文件": "create_file",
            "创建文件夹": "create_folder",
            "获取": "get_admin",
            "获取权限": "get_admin",
            "连接": "connect_folders",
            "连接文件夹": "connect_folders",
            "移除": "remove",
            "建立": "create_folder",
            "新建": "create_file",
            "制作": "create_file",
            "备份": "copy",
            "转移": "move",
            "搬运": "move",
            "拷贝": "copy",
            "剪切": "move",
            "改名": "rename",
            "命名": "rename",
            "查看": "read",
            "检查": "scan",
            "搜寻": "scan",
            "查找": "scan",
            "打包": "compress",
            "解包": "uncompress",
            "解压缩": "uncompress",
            "归档": "compress",
        }
        
        # 首先检查中文动词映射（按长度从长到短匹配，避免部分匹配）
        # 优先匹配更具体的动词
        sorted_keys = sorted(chinese_to_english.keys(), key=len, reverse=True)
        for chinese_verb in sorted_keys:
            if chinese_verb in task:
                # 检查是否在常见的文件名模式中（如README.md）
                # 如果是"read"但出现在文件名中，跳过
                if chinese_verb == "读取" or chinese_verb == "查看":
                    # 检查是否在文件名上下文中
                    if "readme" in task_lower or ".md" in task_lower or ".txt" in task_lower:
                        continue  # 可能是文件名的一部分，不是动词
                return chinese_to_english[chinese_verb]
        
        # 然后检查整个任务中是否包含白名单中的英文动词
        # 但排除可能出现在文件名中的动词（如"read"在"README"中）
        for verb in self.NERVES_ACTION_WHITELIST:
            if verb in task_lower:
                # 特殊处理：如果verb是"read"但出现在"README"中，跳过
                if verb == "read" and "readme" in task_lower:
                    continue
                # 检查动词是否在任务的开头部分（更可能是真正的动词）
                # 简单的启发式：动词出现在前1/3部分
                verb_pos = task_lower.find(verb)
                if verb_pos >= 0 and verb_pos < len(task) * 0.3:
                    return verb
        
        # 最后尝试提取第一个中文词（2-4个字符）
        # 中文任务通常以动词开头，取前2-4个字符作为候选
        task_stripped = task.strip()
        if len(task_stripped) >= 2:
            # 尝试2-4个字符的滑动窗口
            for length in range(4, 1, -1):
                if len(task_stripped) >= length:
                    candidate = task_stripped[:length]
                    if candidate in chinese_to_english:
                        return chinese_to_english[candidate]
        
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
        计算语义复杂度（基于字符数和分隔符）
        
        :param task: 任务描述
        :return: 复杂度分数（字符数）
        """
        # 移除多余空格
        task = task.strip()
        
        # 计算字符数（中文字符每个算1，英文字母和数字每个算0.5）
        # 简单实现：直接返回字符数
        complexity = len(task)
        
        # 如果有多个逗号、分号或"然后"等连接词，增加复杂度
        connectors = ["，", "；", ",", ";", "然后", "接着", "之后", "并且", "而且"]
        for connector in connectors:
            if connector in task:
                complexity += 5  # 每个连接词增加复杂度
        
        return complexity
    
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