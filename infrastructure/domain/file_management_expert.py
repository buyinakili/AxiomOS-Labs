"""文件管理领域专家"""
from typing import List
from interface.domain_expert import IDomainExpert


class FileManagementExpert(IDomainExpert):
    """文件管理领域专家实现"""

    @property
    def domain_name(self) -> str:
        return "file_management"

    def get_rules(self) -> List[str]:
        """
        获取文件管理领域的规则

        :return: 规则列表
        """
        return [
            "文件名点号转义：所有的 '.' 必须替换为 '_dot_'",
            "路径连通性：必须在 (:init) 中定义文件夹双向连接，如 (connected root backup) (connected backup root)",
            "实体补全：(:objects) 必须包含所有在目标中出现的 file 和 folder",
            "若任务开始时已知文件位置，必须在init中写明",
            "[严禁行为] 严禁在目标中对不存在于 (:init) 中的文件使用 at 谓词，除非该任务是 create_file",
            "凡是在 (:init) 中出现的所有对象，必须在 (:objects) 中声明其类型",
            "如果是'创建'任务，必须要在目标中包含创建完目标创建文件应在的位置，防止planner随便找个地方创建"
        ]

    def get_domain_file(self) -> str:
        return "domain.pddl"
