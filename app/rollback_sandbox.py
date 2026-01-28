#!/usr/bin/env python3
"""
沙盒回退脚本 - 回退上一个学习到的技能

功能：
1. 识别上一个沙盒学习到的技能
2. 显示技能详情（domain修改、skills文件、regression_registry条目）
3. 询问用户确认
4. 如果确认，删除相关文件，将项目状态回退到学习该技能之前

使用方法：
    python3 app/rollback_sandbox.py
"""

import json
import os
import sys
import re
import shutil
from datetime import datetime
from typing import Dict, Optional


class SandboxRollback:
    """沙盒回退管理器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.registry_path = os.path.join(self.project_root, "tests", "regression_registry.json")
        self.domain_path = os.path.join(self.project_root, "tests", "domain.pddl")
        self.skills_dir = os.path.join(self.project_root, "infrastructure", "mcp_skills")
        
        self.last_skill_info = None
        self.action_name = None
        self.skill_file_path = None
        
    def get_last_skill(self) -> Optional[Dict]:
        print("[回退] 正在识别上一个学习的技能...")
        
        registry_skill = self._get_last_skill_from_registry()
        if not registry_skill:
            print("[错误] 回归注册表为空或不存在，无法找到上一个技能")
            return None
            
        task_name = registry_skill.get("task_name", "")
        if not task_name:
            goal = registry_skill.get("goal", "")
            task_name = self._extract_action_name_from_goal(goal)
            
        self.action_name = task_name
        print(f"[回退] 识别到技能: {task_name}")
        
        skill_file = self._find_skill_file(task_name)
        self.skill_file_path = skill_file
        
        domain_action = self._find_action_in_domain(task_name)
        
        self.last_skill_info = {
            "task_name": task_name,
            "goal": registry_skill.get("goal", ""),
            "setup_actions": registry_skill.get("setup_actions", []),
            "skill_file": skill_file,
            "domain_action": domain_action,
            "registry_entry": registry_skill
        }
        
        return self.last_skill_info
    
    def _get_last_skill_from_registry(self) -> Optional[Dict]:
        if not os.path.exists(self.registry_path):
            print(f"[警告] 回归注册表文件不存在: {self.registry_path}")
            return None
            
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                tests = json.load(f)
                
            if not tests:
                print("[警告] 回归注册表为空")
                return None
                
            return tests[-1]
        except Exception as e:
            print(f"[错误] 读取回归注册表失败: {e}")
            return None
    
    def _extract_action_name_from_goal(self, goal: str) -> str:
        words = goal.split()
        if words:
            first_word = re.sub(r'[^\w\s]', '', words[0]).lower()
            return f"{first_word}_action"
        return "unknown_action"
    
    def _find_skill_file(self, action_name: str) -> Optional[str]:
        if not os.path.exists(self.skills_dir):
            print(f"[警告] 技能目录不存在: {self.skills_dir}")
            return None
            
        # 策略1: 直接文件名匹配
        possible_patterns = [
            f"{action_name}_skill.py",
            f"{action_name.lower()}_skill.py",
            # 尝试从action_name中提取关键部分
            f"{action_name.split('_')[0]}_skill.py" if '_' in action_name else None,
        ]
        
        for pattern in possible_patterns:
            if pattern:
                file_path = os.path.join(self.skills_dir, pattern)
                if os.path.exists(file_path):
                    return file_path
        
        # 策略2: 遍历所有技能文件，通过内容匹配
        for filename in os.listdir(self.skills_dir):
            if filename.endswith("_skill.py") and filename != "base_skill.py":
                file_path = os.path.join(self.skills_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 检查文件中是否包含action_name
                    if action_name.lower() in content.lower():
                        return file_path
                    
                    # 尝试从技能文件中提取技能名称
                    # 查找 pattern: def name(self): return 'skill_name' 或 @property 返回名称
                    name_patterns = [
                        r"def name\(self\):\s*return\s*['\"]([^'\"]+)['\"]",
                        r"@property\s*\n\s*def name\(self\):\s*return\s*['\"]([^'\"]+)['\"]",
                        r"name\s*=\s*['\"]([^'\"]+)['\"]",
                    ]
                    
                    for pattern in name_patterns:
                        match = re.search(pattern, content)
                        if match:
                            skill_name_in_file = match.group(1)
                            # 检查技能名称是否与action_name相关
                            if (skill_name_in_file.lower() in action_name.lower() or
                                action_name.lower() in skill_name_in_file.lower()):
                                return file_path
                    
                    # 检查文件名中的技能名称是否与action_name相关
                    file_skill_name = filename.replace('_skill.py', '')
                    if (file_skill_name.lower() in action_name.lower() or
                        action_name.lower() in file_skill_name.lower()):
                        return file_path
                        
                except Exception as e:
                    print(f"[调试] 读取技能文件 {filename} 时出错: {e}")
                    continue
        
        # 策略3: 如果还是没找到，尝试查找最近修改的技能文件
        print(f"[警告] 未找到精确匹配的技能文件: {action_name}")
        print(f"[提示] 将尝试查找最近修改的技能文件作为备选")
        
        # 查找最近修改的 _skill.py 文件
        recent_file = None
        recent_time = 0
        
        for filename in os.listdir(self.skills_dir):
            if filename.endswith("_skill.py") and filename != "base_skill.py":
                file_path = os.path.join(self.skills_dir, filename)
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime > recent_time:
                        recent_time = mtime
                        recent_file = file_path
                except:
                    continue
        
        if recent_file:
            print(f"[提示] 使用最近修改的技能文件作为备选: {recent_file}")
            return recent_file
                    
        return None
    
    def _find_action_in_domain(self, action_name: str) -> Optional[str]:
        if not os.path.exists(self.domain_path):
            print(f"[警告] domain文件不存在: {self.domain_path}")
            return None
            
        try:
            with open(self.domain_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            action_pattern = r'\(:action\s+(\w+)[\s\S]*?\)\s*\)'
            actions = re.findall(action_pattern, content)
            
            for action in actions:
                if action_name.lower() in action.lower() or action.lower() in action_name.lower():
                    action_def_pattern = rf'\(:action\s+{action}[\s\S]*?\)\s*\)'
                    match = re.search(action_def_pattern, content)
                    if match:
                        return match.group(0)
            
            lines = content.split('\n')
            in_action = False
            action_lines = []
            
            for i, line in enumerate(lines):
                if '(:action' in line:
                    in_action = True
                    action_lines = [line]
                elif in_action:
                    action_lines.append(line)
                    if line.strip() == ')':
                        in_action = False
                        if i == len(lines) - 1 or '(:action' not in ''.join(lines[i+1:]):
                            return '\n'.join(action_lines)
            
            return None
        except Exception as e:
            print(f"[错误] 解析domain文件失败: {e}")
            return None
    
    def show_rollback_info(self) -> None:
        if not self.last_skill_info:
            print("[错误] 没有可回退的技能信息")
            return
            
        info = self.last_skill_info
        print("\n" + "="*80)
        print("回退信息摘要")
        print("="*80)
        
        print(f"1. 技能名称: {info['task_name']}")
        print(f"2. 目标描述: {info['goal']}")
        
        if info['setup_actions']:
            print(f"3. Setup Actions:")
            for action in info['setup_actions']:
                print(f"   - {action}")
        else:
            print(f"3. Setup Actions: 无")
            
        if info['skill_file']:
            print(f"4. 技能文件: {info['skill_file']}")
            if os.path.exists(info['skill_file']):
                file_size = os.path.getsize(info['skill_file'])
                print(f"   文件大小: {file_size} 字节")
        else:
            print(f"4. 技能文件: 未找到")
            
        if info['domain_action']:
            print(f"5. Domain Action 定义:")
            print(f"   {info['domain_action'][:100]}..." if len(info['domain_action']) > 100 else f"   {info['domain_action']}")
        else:
            print(f"5. Domain Action 定义: 未找到")
            
        print("="*80)
    
    def confirm_rollback(self) -> bool:
        print("\n" + "="*80)
        print("警告: 回退操作将永久删除以下内容:")
        print("  1. 从 tests/domain.pddl 中移除对应的 action")
        print("  2. 删除 infrastructure/mcp_skills/ 中的技能文件")
        print("  3. 从 tests/regression_registry.json 中移除对应条目")
        print("="*80)
        
        while True:
            response = input("\n是否确认回退此技能？(y/n): ").strip().lower()
            if response in ['y', 'yes', '是']:
                return True
            elif response in ['n', 'no', '否']:
                print("回退操作已取消")
                return False
            else:
                print("请输入 y/yes/是 或 n/no/否")
    
    def backup_files(self) -> bool:
        print("\n[回退] 正在创建备份...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 将备份保存到项目根目录的 rollback_backup 目录，避免与沙盒环境冲突
        backup_dir = os.path.join(self.project_root, "rollback_backup", f"rollback_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            if os.path.exists(self.domain_path):
                shutil.copy2(self.domain_path, os.path.join(backup_dir, "domain.pddl.bak"))
                print(f"  - 已备份 domain.pddl")
            
            if os.path.exists(self.registry_path):
                shutil.copy2(self.registry_path, os.path.join(backup_dir, "regression_registry.json.bak"))
                print(f"  - 已备份 regression_registry.json")
            
            if self.skill_file_path and os.path.exists(self.skill_file_path):
                shutil.copy2(self.skill_file_path, os.path.join(backup_dir, os.path.basename(self.skill_file_path)))
                print(f"  - 已备份技能文件: {os.path.basename(self.skill_file_path)}")
            
            print(f"[回退] 备份已保存到: {backup_dir}")
            return True
        except Exception as e:
            print(f"[错误] 创建备份失败: {e}")
            return False
    
    def remove_from_domain(self) -> bool:
        if not os.path.exists(self.domain_path):
            print("[错误] domain.pddl 文件不存在")
            return False
            
        if not self.action_name:
            print("[错误] 未指定要移除的 action 名称")
            return False
            
        print(f"[回退] 正在从 domain.pddl 中移除 action: {self.action_name}")
        
        try:
            with open(self.domain_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            action_pattern = rf'\(:action\s+{self.action_name}[\s\S]*?\)\s*\)'
            new_content = re.sub(action_pattern, '', content)
            
            if new_content != content:
                new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)
                
                with open(self.domain_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"  - 成功从 domain.pddl 中移除 action: {self.action_name}")
                return True
            else:
                print(f"  - 未找到精确匹配的 action，尝试移除最后一个action...")
                
                lines = content.split('\n')
                new_lines = []
                i = 0
                removed = False
                
                # 首先查找 AI Generated Action 注释
                comment_line = -1
                for idx, line in enumerate(lines):
                    if ";; --- AI Generated Action ---" in line:
                        comment_line = idx
                        break
                
                if comment_line >= 0:
                    print(f"  - 找到 AI Generated Action 注释在行 {comment_line}")
                    
                    # 查找注释后的第一个 action
                    action_start = -1
                    for idx in range(comment_line, len(lines)):
                        if '(:action' in lines[idx]:
                            action_start = idx
                            break
                    
                    if action_start >= 0:
                        print(f"  - 找到 action 开始行 {action_start}")
                        
                        # 计算括号平衡以找到 action 结束
                        brace_count = 0
                        action_end = -1
                        for idx in range(action_start, len(lines)):
                            brace_count += lines[idx].count('(')
                            brace_count -= lines[idx].count(')')
                            if brace_count <= 0 and idx > action_start:
                                action_end = idx
                                break
                        
                        if action_end >= 0:
                            print(f"  - 找到 action 结束行 {action_end}")
                            print(f"  - 删除范围: 行 {comment_line} 到 {action_end-1} (不包括最后的右括号)")
                            
                            # 删除从注释行到 action_end-1 (不包括最后的右括号)
                            new_lines = lines[:comment_line] + lines[action_end:]
                            
                            with open(self.domain_path, 'w', encoding='utf-8') as f:
                                f.write('\n'.join(new_lines))
                            print(f"  - 已移除最后一个action (包括注释)")
                            return True
                
                # 如果没找到注释，使用原来的逻辑
                print(f"  - 未找到 AI Generated Action 注释，使用备用逻辑...")
                i = 0
                new_lines = []
                removed = False
                
                while i < len(lines):
                    line = lines[i]
                    if '(:action' in line and not removed:
                        action_start = i
                        brace_count = 0
                        j = i
                        while j < len(lines):
                            brace_count += lines[j].count('(')
                            brace_count -= lines[j].count(')')
                            if brace_count <= 0 and j > action_start:
                                break
                            j += 1
                        
                        remaining = ''.join(lines[j+1:])
                        if '(:action' not in remaining:
                            print(f"  - 移除最后一个action（可能匹配: {line.strip()}）")
                            # 删除从 action_start 到 j-1 (不包括最后的右括号)
                            new_lines = lines[:action_start] + lines[j:]
                            removed = True
                            break
                        else:
                            new_lines.extend(lines[i:j+1])
                            i = j + 1
                            continue
                    else:
                        new_lines.append(line)
                        i += 1
                
                if removed:
                    with open(self.domain_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                    print(f"  - 已移除最后一个action")
                    return True
                else:
                    print(f"  - 未找到可移除的action")
                    return False
                    
        except Exception as e:
            print(f"[错误] 移除domain action失败: {e}")
            return False
    
    def remove_skill_file(self) -> bool:
        if not self.skill_file_path or not os.path.exists(self.skill_file_path):
            print("[警告] 技能文件不存在，跳过删除")
            return True
            
        print(f"[回退] 正在删除技能文件: {self.skill_file_path}")
        
        try:
            os.remove(self.skill_file_path)
            print(f"  - 成功删除技能文件")
            return True
        except Exception as e:
            print(f"[错误] 删除技能文件失败: {e}")
            return False
    
    def remove_from_registry(self) -> bool:
        if not os.path.exists(self.registry_path):
            print("[错误] 回归注册表文件不存在")
            return False
            
        print(f"[回退] 正在从回归注册表中移除条目")
        
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                tests = json.load(f)
            
            if not tests:
                print("  - 回归注册表为空，无需移除")
                return True
            
            removed_entry = tests.pop()
            print(f"  - 已移除条目: {removed_entry.get('task_name', '未知')}")
            
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(tests, f, indent=4, ensure_ascii=False)
            
            print(f"  - 回归注册表已更新")
            return True
        except Exception as e:
            print(f"[错误] 更新回归注册表失败: {e}")
            return False
    
    def execute_rollback(self) -> bool:
        print("="*80)
        print("AxiomLabs 沙盒回退工具")
        print("="*80)
        
        skill_info = self.get_last_skill()
        if not skill_info:
            print("[错误] 无法识别上一个技能，回退终止")
            return False
        
        self.show_rollback_info()
        
        if not self.confirm_rollback():
            return False
        
        if not self.backup_files():
            print("[警告] 备份创建失败，继续执行回退吗？")
            confirm = input("继续执行回退？(y/n): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
                print("回退操作已取消")
                return False
        
        print("\n[回退] 开始执行回退操作...")
        
        success = True
        
        if not self.remove_from_domain():
            print("[警告] 从domain.pddl移除action失败")
            success = False
        
        if not self.remove_skill_file():
            print("[警告] 删除技能文件失败")
            success = False
        
        if not self.remove_from_registry():
            print("[警告] 从回归注册表移除条目失败")
            success = False
        
        print("\n" + "="*80)
        if success:
            print("✓ 回退操作完成！")
            print("项目状态已恢复到学习上一个技能之前")
        else:
            print("⚠ 回退操作部分失败，请检查备份文件")
            print("备份文件保存在 rollback_backup/ 目录中")
        
        print("="*80)
        return success


def main():
    """主函数"""
    try:
        rollback = SandboxRollback()
        success = rollback.execute_rollback()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n回退操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[致命错误] 回退过程发生异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
#python3 app/rollback_sandbox.py