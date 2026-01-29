from infrastructure.mcp_skills.mcp_base_skill import MCPBaseSkill
import os
import json

class GeneratedSkill(MCPBaseSkill):
    @property
    def name(self):
        return 'rename_file'
    
    @property
    def description(self):
        return '重命名文件'
    
    @property
    def input_schema(self):
        return {
            'type': 'object',
            'properties': {
                'old_file': {'type': 'string', 'description': '原文件名（PDDL格式，点替换为_dot_）'},
                'new_file': {'type': 'string', 'description': '新文件名（PDDL格式，点替换为_dot_）'},
                'folder': {'type': 'string', 'description': '文件夹名'}
            },
            'required': ['old_file', 'new_file', 'folder']
        }
    
    async def execute(self, arguments):
        old_file = arguments.get('old_file')
        new_file = arguments.get('new_file')
        folder = arguments.get('folder')
        old_path = self._safe_path(folder, old_file)
        new_path = self._safe_path(folder, new_file)
        try:
            os.rename(old_path, new_path)
            pddl_delta = f'(and (not (at {old_file} {folder})) (at {new_file} {folder}))'
            return self.create_success_response(f'文件 {old_file} 已重命名为 {new_file} 在 {folder} 中', pddl_delta)
        except Exception as e:
            return self.create_error_response(str(e))