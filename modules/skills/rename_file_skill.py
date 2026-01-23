from modules.skills.base import BaseSkill, SkillResult
import os

class GeneratedSkill(BaseSkill):
    @property
    def name(self): return 'rename_file'
    def execute(self, args):
        old_file_name = args[0]
        new_file_name = args[1]
        folder_name = args[2]
        old_path = self._safe_path(folder_name, old_file_name)
        new_path = self._safe_path(folder_name, new_file_name)
        try:
            os.rename(old_path, new_path)
            return SkillResult(True, 'Renamed successfully', [f'(at {new_file_name} {folder_name})', f'(is_created {new_file_name})'], [f'(at {old_file_name} {folder_name})'])
        except Exception as e:
            return SkillResult(False, str(e))