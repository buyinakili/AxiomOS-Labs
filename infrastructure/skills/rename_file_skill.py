from infrastructure.skills.base_skill import BaseSkill
from interface.executor import ExecutionResult
import os

class GeneratedSkill(BaseSkill):
    @property
    def name(self): return 'rename_file'
    def execute(self, args):
        old_file, new_file, folder = args[0], args[1], args[2]
        old_path = self._safe_path(folder, old_file)
        new_path = self._safe_path(folder, new_file)
        try:
            os.rename(old_path, new_path)
            return ExecutionResult(True, 'Renamed successfully', [f'(at {new_file} {folder})'], [f'(at {old_file} {folder})'])
        except Exception as e:
            return ExecutionResult(False, str(e))