"""删除文件技能 - AI自学习生成"""
import os
from infrastructure.skills.base_skill import BaseSkill
from interface.executor import ExecutionResult


class GeneratedSkill(BaseSkill):
    """删除文件技能"""

    @property
    def name(self):
        return 'remove_file'

    def execute(self, args):
        """
        删除文件

        :param args: [file_name, folder_name]
        :return: ExecutionResult
        """
        if len(args) != 2:
            return ExecutionResult(False, "需要2个参数: 文件名和文件夹名")

        target = self._safe_path(args[1], args[0])

        try:
            if not os.path.exists(target):
                return ExecutionResult(
                    False,
                    f"文件 {args[0]} 在 {args[1]} 中不存在"
                )

            os.remove(target)
            # 删除文件后，(at file folder) 事实不再成立
            return ExecutionResult(
                success=True,
                message=f"成功删除 {args[0]} 从 {args[1]}",
                add_facts=[],
                del_facts=[f'(at {args[0]} {args[1]})']
            )
        except Exception as e:
            return ExecutionResult(False, str(e))
