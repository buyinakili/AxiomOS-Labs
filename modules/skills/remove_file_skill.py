from modules.skills.base import BaseSkill, SkillResult
import os

class GeneratedSkill(BaseSkill):
    @property
    def name(self):
        return 'remove_file'
    
    def execute(self, args):
        # args[0] = file name, args[1] = folder name
        if len(args) != 2:
            return SkillResult(False, "Expected 2 arguments: file and folder")
        
        target = self._safe_path(args[1], args[0])
        
        try:
            if not os.path.exists(target):
                return SkillResult(False, f"File {args[0]} does not exist in {args[1]}")
            
            os.remove(target)
            # 删除文件后，(at file folder) 事实不再成立
            return SkillResult(True, f"Successfully deleted {args[0]} from {args[1]}", [], [f'(at {args[0]} {args[1]})'])
        except Exception as e:
            return SkillResult(False, str(e))