"""PDDL翻译器实现"""
from typing import Set, Dict, List, Optional
from interface.translator import ITranslator
from interface.llm import ILLM
from interface.storage import IStorage
from interface.domain_expert import IDomainExpert
from config.settings import Settings
from config.constants import CONSTANTS


class PDDLTranslator(ITranslator):
    """PDDL翻译器实现"""

    def __init__(
        self,
        llm: ILLM,
        storage: IStorage,
        domain_experts: Dict[str, IDomainExpert],
        config: Optional[Settings] = None
    ):
        """
        初始化翻译器

        :param llm: LLM客户端
        :param storage: 存储接口
        :param domain_experts: 领域专家字典 {domain_name: expert}
        :param config: 配置对象，如果为None则使用默认配置
        """
        self.llm = llm
        self.storage = storage
        self.domain_experts = domain_experts
        self.config = config or Settings.load_from_env()

    def _should_debug_prompt(self) -> bool:
        """检查是否应该打印调试信息"""
        import os
        return os.environ.get("AXIOMLABS_DEBUG_PROMPT", "").lower() in ("1", "true", "yes")

    def route_domain(self, user_goal: str) -> str:
        """
        路由任务到对应的领域

        :param user_goal: 用户目标描述
        :return: 领域名称
        """
        domain_names = list(self.domain_experts.keys())

        prompt = f"""
请判断以下用户指令属于哪个领域。
指令: "{user_goal}"
可选领域: {domain_names}
只需返回领域名称，不要其他文字。
"""

        # 调试：打印发送给LLM的提示词（仅当环境变量AXIOMLABS_DEBUG_PROMPT为真时）
        import sys
        if self._should_debug_prompt():
            print("\n=== DEBUG: Prompt sent to LLM (route_domain) ===", file=sys.stderr)
            print(prompt, file=sys.stderr)
            print("=== DEBUG END ===\n", file=sys.stderr)
        
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        choice = response.strip().lower()
        # 使用配置中的默认领域名称作为后备
        default_domain = self.config.domain_name if self.config.domain_name in self.domain_experts else domain_names[0]
        return choice if choice in self.domain_experts else default_domain

    def _extract_objects_from_facts(self, memory_facts: Set[str], domain: str) -> Dict[str, str]:
        """
        从事实集合中提取对象及其类型
        
        :param memory_facts: PDDL事实集合
        :param domain: 领域名称（目前仅支持file_management）
        :return: 字典 {对象名: 类型}
        """
        # 目前只处理配置中指定的默认领域
        if domain != self.config.domain_name:
            # 默认返回空，后续可根据需要扩展
            return {}
        
        # 类型映射：谓词 -> 参数位置 -> 类型
        type_mapping = {
            "at": {0: "file", 1: "folder"},
            # 不再包含connected谓词，因为它已被删除
            "scanned": {0: "folder"},
            "is_created": {0: "file"},  # 也可能是folder，但默认为file
            "is_compressed": {0: "file", 1: "archive"},
        }
        
        objects = {}
        for fact in memory_facts:
            # 解析事实，格式如 "(at file_a root)" 或 "(not (at file_a root))"
            # 我们只关心正事实，忽略not
            if fact.startswith("(not"):
                continue
            # 移除括号
            content = fact.strip("()")
            parts = content.split()
            if not parts:
                continue
            predicate = parts[0]
            if predicate not in type_mapping:
                continue
            mapping = type_mapping[predicate]
            for pos, obj in enumerate(parts[1:]):
                if pos in mapping:
                    obj_name = obj
                    obj_type = mapping[pos]
                    # 清理对象名称：去除任何可能残留的括号
                    obj_name = obj_name.strip("()")
                    if not obj_name:
                        continue
                    # 如果对象已存在，检查类型是否冲突；若冲突，优先使用更具体的类型？暂时忽略
                    if obj_name in objects and objects[obj_name] != obj_type:
                        # 类型冲突，暂时保留原有类型（可记录日志）
                        pass
                    else:
                        objects[obj_name] = obj_type
        # 调试打印（仅当环境变量AXIOMLABS_DEBUG_PROMPT为真时）
        import sys
        if self._should_debug_prompt():
            print(f"[DEBUG] 提取的对象: {objects}", file=sys.stderr)
        return objects
    
    def _extract_objects_from_goal(self, goal_content: str, domain: str) -> Dict[str, str]:
        """
        从goal内容中提取对象及其类型
        
        :param goal_content: goal内容字符串，如 "(:goal (and (at file_a backup)))"
        :param domain: 领域名称
        :return: 字典 {对象名: 类型}
        """
        # 目前只处理配置中指定的默认领域
        if domain != self.config.domain_name:
            return {}
        
        # 类型映射：谓词 -> 参数位置 -> 类型
        type_mapping = {
            "at": {0: "file", 1: "folder"},
            "connected": {0: "folder", 1: "folder"},
            "scanned": {0: "folder"},
            "is_created": {0: "file"},
            "is_compressed": {0: "file", 1: "archive"},
        }
        
        objects = {}
        
        # 解析goal内容，提取所有谓词
        import re
        
        # 移除(:goal和可能的(and包装
        content = goal_content.strip()
        if content.startswith("(:goal"):
            # 提取(:goal ...)内部的内容
            match = re.search(r'\(:goal\s+(.*?)\)\s*$', content, re.DOTALL)
            if match:
                inner = match.group(1).strip()
                # 如果包含(and ...)，提取and内部的内容
                if inner.startswith("(and"):
                    inner_match = re.search(r'\(and\s+(.*?)\)\s*$', inner, re.DOTALL)
                    if inner_match:
                        inner = inner_match.group(1).strip()
                content = inner
        
        # 提取所有谓词（包括嵌套）
        predicates = re.findall(r'\([^()]*(?:\([^()]*\)[^()]*)*\)', content)
        
        for pred in predicates:
            # 移除外层括号
            pred = pred.strip()
            # 处理否定谓词：递归剥离 (not ...)
            while pred.startswith('(not'):
                # 移除外层的 (not 和对应的右括号)
                # 格式为 (not <inner>)，其中 inner 可能带有括号
                # 我们直接去掉前5个字符 "(not " 和最后一个字符 ")"
                inner = pred[5:-1].strip()
                pred = inner
            if not pred.startswith('(') or not pred.endswith(')'):
                continue
            inner = pred[1:-1].strip()
            parts = inner.split()
            if not parts:
                continue
            predicate = parts[0]
            if predicate not in type_mapping:
                continue
            mapping = type_mapping[predicate]
            for pos, obj in enumerate(parts[1:]):
                if pos in mapping:
                    obj_name = obj.strip()
                    # 清理对象名称
                    obj_name = obj_name.strip("()")
                    if not obj_name:
                        continue
                    typ = mapping[pos]
                    # 如果对象已存在，检查类型是否冲突
                    if obj_name in objects and objects[obj_name] != typ:
                        # 类型冲突，保留原有类型（记录警告）
                        import sys
                        print(f"[警告] 对象 {obj_name} 类型冲突: 已有类型 {objects[obj_name]}, 新类型 {typ}", file=sys.stderr)
                    else:
                        objects[obj_name] = typ
        
        # 调试打印
        import sys
        if self._should_debug_prompt():
            print(f"[DEBUG] 从goal中提取的对象: {objects}", file=sys.stderr)
        
        return objects
    
    def _escape_goal_objects(self, goal_content: str) -> str:
        """
        转义goal内容中的对象名：将包含点号的对象名中的 '.' 替换为 '_dot_'
        
        :param goal_content: 原始goal内容字符串
        :return: 转义后的goal内容字符串
        """
        import re
        
        # 匹配由字母、数字、下划线、点号、连字符组成的单词（PDDL对象名）
        # 排除已经包含_dot_的单词（已经转义）
        pattern = r'\b[a-zA-Z0-9_.-]+\b'
        
        def replace_match(match):
            word = match.group(0)
            # 如果单词包含点号且不包含_dot_（即未转义）
            if '.' in word and '_dot_' not in word:
                # 替换点为_dot_
                return word.replace('.', '_dot_')
            return word
        
        escaped = re.sub(pattern, replace_match, goal_content)
        
        # 调试输出
        if self._should_debug_prompt() and escaped != goal_content:
            import sys
            print(f"[DEBUG] 转义goal对象: {goal_content} -> {escaped}", file=sys.stderr)
        
        return escaped
    
    def _build_objects_section(self, objects: Dict[str, str]) -> str:
        """
        构建PDDL objects部分
        
        :param objects: 对象字典
        :return: objects部分字符串
        """
        if not objects:
            return ""
        # 按类型分组
        type_to_objs = {}
        for obj, typ in objects.items():
            type_to_objs.setdefault(typ, []).append(obj)
        lines = []
        for typ, objs_list in type_to_objs.items():
            line = " ".join(objs_list) + " - " + typ
            lines.append(line)
        return "\n    ".join(lines)
    
    def _build_init_section(self, memory_facts: Set[str], objects: Dict[str, str] = None,
                           base_init_facts: Set[str] = None) -> str:
        """
        构建PDDL init部分
        
        :param memory_facts: 当前事实集合（增量变更）
        :param objects: 对象字典 {对象名: 类型}，用于生成静态连接事实
        :param base_init_facts: 基础事实集合（第一轮init）
        :return: init部分字符串
        """
        # 如果有基础事实，以其为起点
        if base_init_facts is not None:
            # 深拷贝基础事实，过滤无效内容
            init_facts = set()
            for fact in base_init_facts:
                fact_stripped = fact.strip()
                if not fact_stripped:
                    continue
                # 忽略注释（以;开头）
                if fact_stripped.startswith(";"):
                    continue
                # 忽略not事实
                if fact_stripped.startswith("(not"):
                    continue
                init_facts.add(fact)
        else:
            init_facts = set()
        
        # 应用当前memory_facts（过滤无效内容）
        for fact in memory_facts:
            fact_stripped = fact.strip()
            if not fact_stripped:
                continue
            # 忽略not事实，因为not在PDDL init中不能出现
            if fact_stripped.startswith("(not"):
                continue
            # 忽略注释（以;开头）
            if fact_stripped.startswith(";"):
                continue
            init_facts.add(fact)
        
        # 添加静态连接事实（仅针对file_management领域）
        if objects:
            # 找出所有文件夹
            folders = [obj for obj, typ in objects.items() if typ == "folder"]
            # 生成双向连接
            # 不再生成connected事实，因为connected谓词已被删除
        
        # 添加total-cost（如果不存在）
        init_facts.add("(= (total-cost) 0)")
        
        # 排序以确保一致性
        return "\n    ".join(sorted(init_facts))
    
    def translate(self, user_goal: str, memory_facts: Set[str], domain: str, execution_history: List[str] = None, iteration: int = 0, objects: Dict[str, str] = None, base_init_facts: Set[str] = None) -> str:
        """
        将用户目标和当前事实转换为PDDL Problem

        :param user_goal: 用户目标描述
        :param memory_facts: 当前的PDDL事实集合
        :param domain: 领域名称
        :param execution_history: 执行历史记录（动作名称列表），可选
        :param iteration: 当前迭代次数（0表示第一轮）
        :param objects: 累积的对象映射 {对象名: 类型}，用于后续轮次构建objects部分
        :param base_init_facts: 基础init事实集合（第一轮init），用于增量更新
        :return: PDDL Problem内容
        """
        import sys
        if self._should_debug_prompt():
            print(f"[翻译器] translate called: iteration={iteration}, memory_facts={memory_facts}, objects={objects}", file=sys.stderr)
        # 获取领域专家
        expert = self.domain_experts.get(domain)
        if not expert:
            raise ValueError(f"未知领域: {domain}")

        # 获取Domain内容
        domain_content = self.storage.read_domain(domain)

        # 构建上下文
        facts_str = "\n".join(sorted(list(memory_facts))) if memory_facts else "无"
        
        # 构建执行历史字符串
        history_str = "无"
        if execution_history:
            history_str = "\n".join([f"- {action}" for action in execution_history])
        
        memory_context = f"""用户最终目标: {user_goal}

【当前已知环境事实 (PDDL Predicates)】:
{facts_str}

【执行历史记录 (最近动作)】:
{history_str}

如果上述事实已经完全满足了用户最终目标（例如：对于移动任务，文件已在目标位置且不在原位置；对于删除任务，文件已不存在；对于创建任务，目标文件/文件夹已存在），
请不要生成任何 PDDL，直接回复：GOAL_FINISHED_ALREADY"""

        # 获取领域规则
        rules_str = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(expert.get_rules())])

        # 判断是否为第一轮
        if iteration == 0:
            # 第一轮：使用完整Prompt
            prompt = f"""你现在是[{domain}] 逻辑专家。
任务：根据"已知环境事实"将用户目标转化为 PDDL Problem。

{memory_context}

[核心原则 - 严禁幻觉]:
1. 你绝对不能将"已知环境事实"或任务中没有提到具体信息的目标写入init或goal中。
2. 如果"已知环境事实"或任务中没有提到具体信息，你绝对不能猜测信息，优先将目标设置为可获取信息动作后的唯一谓词，且目标仅为此。
3. 必须在 (:init) 中包含 (= (total-cost) 0)。
4. 避免关键字：严禁出现exists
5. 若已知环境事实为空（即显示为"无"），你必须将goal仅设置为获取信息的动作后的唯一谓词。
6. 严禁发明任何文件对象。如果不知道具体文件名，绝对不能在goal中创建文件对象。

- 执行历史记录了之前执行过的动作，可以帮助你理解当前状态
- 结合已知事实和执行历史来判断目标是否已完成

[领域逻辑规则]:
{rules_str}

[Domain 定义]:
{domain_content}

[输出要求]:
仅输出 PDDL 代码 或 GOAL_FINISHED_ALREADY。
"""
        else:
            # 后续轮次：自动构建objects和init，LLM只生成goal
            # 如果提供了objects，则以其为基础，否则从事实中提取
            if objects is None:
                objects = self._extract_objects_from_facts(memory_facts, domain)
            else:
                # 合并新事实中出现的对象（避免遗漏）
                new_objects = self._extract_objects_from_facts(memory_facts, domain)
                for obj, typ in new_objects.items():
                    if obj not in objects:
                        objects[obj] = typ
            objects_section = self._build_objects_section(objects)
            init_section = self._build_init_section(memory_facts, objects, base_init_facts)
            
            prompt = f"""你现在是 AxiomLabs 的 [{domain}] 逻辑专家。
任务：根据当前状态，仅生成PDDL Problem的(:goal ...)部分。

[当前状态]:
- 已知对象 (:objects):
    {objects_section if objects_section else "（无）"}
- 初始状态 (:init):
    {init_section}

{memory_context}

[领域逻辑规则]:
{rules_str}

[Domain 定义]:
{domain_content}

[要求]:
1. 仅输出 (:goal ...) 部分，不要输出完整的PDDL Problem。
2. 如果当前状态已满足用户目标，请输出 "GOAL_FINISHED_ALREADY"。
3. 避免使用exists关键字。
4. 请你将此任务所有可能出现在goal中的目标，所有可能相关的目标全部写入objects
5. 确保目标谓词与领域谓词匹配，并且参数类型正确。

示例输出:
(:goal (and (at file_a backup)))
或
GOAL_FINISHED_ALREADY

请输出：
"""
        # 调试：打印prompt内容（仅当环境变量AXIOMLABS_DEBUG_PROMPT为真时）
        import sys
        if self._should_debug_prompt():
            print("\n=== DEBUG: Prompt content (before LLM) ===", file=sys.stderr)
            print(prompt, file=sys.stderr)
            print("=== DEBUG END ===\n", file=sys.stderr)

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        # 清理响应
        pddl_code = response
        if "```" in pddl_code:
            pddl_code = pddl_code.split("```")[1]
            if pddl_code.startswith("pddl") or pddl_code.startswith("lisp"):
                pddl_code = pddl_code.split("\n", 1)[1]

        print("\n" + "="*80)
        print(memory_context)
        print("-"*80)
        print(pddl_code)
        print("="*80 + "\n")

        # 如果是后续轮次且LLM返回了goal部分，需要组装完整problem
        if iteration > 0 and not pddl_code.strip().startswith("GOAL_FINISHED_ALREADY"):
            # 提取goal部分
            goal_content = pddl_code.strip()
            # 确保goal内容以(:goal开头)
            if not goal_content.startswith("(:goal"):
                # 可能是纯谓词，包装一下
                goal_content = f"(:goal (and {goal_content}))"
            
            # 转义goal中的对象名（将 '.' 替换为 '_dot_'）
            goal_content = self._escape_goal_objects(goal_content)
            
            # 从goal中提取对象并合并到现有objects中
            goal_objects = self._extract_objects_from_goal(goal_content, domain)
            for obj, typ in goal_objects.items():
                if obj not in objects:
                    objects[obj] = typ
                    print(f"[翻译器] 将goal中的对象添加到objects: {obj} - {typ}")
                elif objects[obj] != typ:
                    print(f"[翻译器] 警告: 对象 {obj} 类型冲突，已有类型 {objects[obj]}，goal中类型 {typ}，保留原有类型")
            
            # 构建完整problem
            objects_section = self._build_objects_section(objects)
            init_section = self._build_init_section(memory_facts, objects, base_init_facts)
            # 使用配置中的领域名称生成PDDL domain和problem名称
            # 将下划线替换为连字符以符合PDDL命名约定
            pddl_domain_name = self.config.domain_name.replace('_', '-')
            # 如果domain_name是"file_management"，则PDDL domain应该是"file-manager"（保持向后兼容）
            if self.config.domain_name == "file_management":
                pddl_domain_name = "file-manager"
            problem_name = f"{self.config.domain_name.replace('_', '-')}-problem"
            problem = f"(define (problem {problem_name})\n  (:domain {pddl_domain_name})\n  (:objects\n    {objects_section}\n  )\n  (:init\n    {init_section}\n  )\n  {goal_content}\n  (:metric minimize (total-cost))\n)"
            # 打印组装后的完整problem
            print("[翻译器] 组装完整PDDL Problem:")
            print(problem)
            print("="*80 + "\n")
            return problem
        else:
            # 第一轮或GOAL_FINISHED_ALREADY，直接返回LLM的输出
            return pddl_code.strip()
    