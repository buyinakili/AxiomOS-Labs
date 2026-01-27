"""PDDL翻译器实现"""
from typing import Set, Dict, List
from interface.translator import ITranslator
from interface.llm import ILLM
from interface.storage import IStorage
from interface.domain_expert import IDomainExpert


class PDDLTranslator(ITranslator):
    """PDDL翻译器实现"""

    def __init__(
        self,
        llm: ILLM,
        storage: IStorage,
        domain_experts: Dict[str, IDomainExpert]
    ):
        """
        初始化翻译器

        :param llm: LLM客户端
        :param storage: 存储接口
        :param domain_experts: 领域专家字典 {domain_name: expert}
        """
        self.llm = llm
        self.storage = storage
        self.domain_experts = domain_experts

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

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        choice = response.strip().lower()
        return choice if choice in self.domain_experts else domain_names[0]

    def translate(self, user_goal: str, memory_facts: Set[str], domain: str, execution_history: List[str] = None) -> str:
        """
        将用户目标和当前事实转换为PDDL Problem

        :param user_goal: 用户目标描述
        :param memory_facts: 当前的PDDL事实集合
        :param domain: 领域名称
        :param execution_history: 执行历史记录（动作名称列表），可选
        :return: PDDL Problem内容
        """
        # 获取领域专家
        expert = self.domain_experts.get(domain)
        if not expert:
            raise ValueError(f"未知领域: {domain}")

        # 获取Domain内容
        domain_content = self.storage.read_domain(domain)

        # 构建上下文
        facts_str = "\n".join(sorted(list(memory_facts))) if memory_facts else "未知"
        
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

        # 构建Prompt
        prompt = f"""你现在是 AIOS 的 [{domain}] 逻辑专家。
任务：根据"已知事实"将用户目标转化为 PDDL Problem。

[核心原则 - 严禁幻觉]:
1. 仅能使用"已知环境事实"或任务中明确提到的对象、位置和状态。
2. 如果"已知环境事实"或任务中没有提到具体信息，你绝对不能猜测信息，优先将目标设置为获取信息的操作。
3. 必须在 (:init) 中包含 (= (total-cost) 0)。
4. 必须在 PDDL 末尾添加 (:metric minimize (total-cost)) 以追求最优路径。
5. 避免关键字：严禁出现exists

[扫描规则]:
- 如果不知道文件的完整名称，目标必须**仅包含** (scanned folder)，不能包含其他谓词
- init 中不能预先设置 (scanned ...) 谓词

[执行历史使用规则]:
- 执行历史记录了之前执行过的动作，可以帮助你理解当前状态
- 例如：如果执行历史中有"scan root"和"remove_file good_dot_txt root"，说明已经扫描过root文件夹并删除了good_dot_txt文件
- 结合已知事实和执行历史来判断目标是否已完成

[特殊指令]:
如果"已知事实"已经完全满足了"用户最终目标"，请不要输出 PDDL，只需直接输出字符串: GOAL_FINISHED_ALREADY

[领域逻辑规则]:
{rules_str}

[Domain 定义]:
{domain_content}

[上下文事实与目标]:
{memory_context}

[输出要求]:
仅输出 PDDL 代码 或 GOAL_FINISHED_ALREADY。
"""

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

        return pddl_code.strip()
