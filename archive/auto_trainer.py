# auto_trainer.py
import time
import os
import shutil
import sys
import signal # 补充缺失的 import
from openai import OpenAI
from modules.sandbox import SandboxManager
from modules.executor import ActionExecutor
from modules.evolution_manager import EvolutionManager
from modules.pddl_modifier import PDDLModifier
from modules.planner import LAMAPlanner
from modules.curriculum_manager import CurriculumManager
# === 新增 Import ===
from modules.regression_manager import RegressionManager 
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, PROJECT_ROOT, DOWNWARD_PATH
# 使用 config 中的配置
CLIENT = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
"""
STOP_TRAINING = False
def signal_handler(sig, frame):
    global STOP_TRAINING
    print("\n[System] 接收到停止信号！正在完成当前步骤并安全退出...")
    STOP_TRAINING = True
signal.signal(signal.SIGINT, signal_handler)
"""
def promote_skill(skill_data, project_root):
    """
    技能晋升逻辑：将沙盒验证成功的代码合并到主系统
    """
    print(f"\n[Promoter] 正在晋升技能: {skill_data['action_name']} ...")
    
    # 1. 合并 PDDL 到 tests/domain.pddl
    main_domain_path = os.path.join(project_root, "tests", "domain.pddl")
    PDDLModifier.add_action_to_domain(main_domain_path, skill_data['pddl_patch'])
    print(f"  - PDDL Action 已追加到主 Domain。")

    # 2. 移动 Python 文件到 modules/skills/
    new_filename = f"{skill_data['action_name']}_skill.py"
    target_skill_path = os.path.join(project_root, "modules", "skills", new_filename)
    
    shutil.copy(skill_data['skill_file_path'], target_skill_path)
    print(f"  - Python 脚本已部署到: {target_skill_path}")

    print("[Promoter] 晋升完成！重启系统后即可使用新能力。")

def setup_environment(executor, sm, setup_actions):
    """
    根据 LLM 生成的 setup_actions 列表，调用现有技能准备环境
    """
    print("[Trainer] 正在执行环境预设 (Setup)...")
    # 临时把 executor 指向沙盒路径
    for skill in executor.skills.values():
        skill.base_path = sm.storage_path

    for action in setup_actions:
        skill_name = action[0]
        args = action[1:]
        print(f"  -> 执行预设动作: {skill_name} {args}")
        
        if skill_name in executor.skills:
            res = executor.execute_step(skill_name, args)
            if not res.is_success:
                print(f"  [Warning] 预设动作失败: {res.message}")
        else:
            print(f"  [Warning] 未知预设动作: {skill_name}")

def start_auto_training():
    print("=== AIOS 全自动进化训练矩阵 (Autonomous Mode) ===")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    domain_path = os.path.join(project_root, "tests", "domain.pddl")
    
    # 初始化课程经理 和 回归经理
    curriculum_mgr = CurriculumManager(CLIENT, domain_path)
    regression_mgr = RegressionManager(CLIENT, os.path.join(project_root, "tests", "regression_registry.json"))

    # 设定训练轮次
    training_rounds = 3 
    base_executor = ActionExecutor()
    
    for i in range(training_rounds):
        """
        if STOP_TRAINING: 
            break
        print(f"\n>>> 进入第 {i+1} 轮自主训练周期")"""
        base_executor.execution_history = []
        # 1. LLM 提出任务
        task_data = curriculum_mgr.propose_next_task(base_executor)
        if not task_data:
            print("[Trainer] 无法生成任务，跳过本轮。")
            continue

        goal = task_data['goal']
        setup_actions = []
        
        time.sleep(1.5)

        # 2. 创建干净沙盒
        sm = SandboxManager()
        sandbox_path = sm.create_sandbox()
        
        # 3. 初始化执行器与环境
        executor = ActionExecutor()
        setup_environment(executor, sm, setup_actions)

        # 4. 运行进化
        planner = LAMAPlanner("/home/nakili/projects/AIOS/downward/fast-downward.py")
        executor_for_evo = ActionExecutor()
        ev_manager = EvolutionManager(executor=executor_for_evo, planner=planner, max_retries=4)
        
        # 这里的 task_data 包含了 LLM 预期的动作名称
        result = ev_manager.run_evolution_loop(goal, sm, task_data, CLIENT)
        
        # --- [审计开始] ---
        if result['success']:
            target_action = result.get('action_name', '').lower()
            
            # 【精准指向】：访问 ev_manager 正在使用的 executor
            # 此时这个 history 应该包含 ['get_admin', 'scan', 'rename_file'...]
            actual_history = ev_manager.executor.execution_history
            history = [h.lower() for h in actual_history]
            
            print(f"[Trainer] 正在从实例 {id(ev_manager.executor)} 审计执行路径: {history}")

            if target_action and target_action not in history:
                print(f"[Trainer] \033[91m审计拦截：进化动作 '{target_action}' 未出现在执行路径 {history} 中！\033[0m")
                print(f"[Trainer] 判定为“虚假完成”（逃课），拒绝晋升。")
                result['success'] = False 
                result['error'] = f"Audit Failure: Action '{target_action}' was never called."
        # --- [审计结束] ---

        # 5. 结果验证与晋升
        if result['success']:
            print(f"[Trainer] 任务 '{goal}' 沙盒训练成功且通过路径审计！")
            
            # === 新增流程：回归测试 ===
            # 获取本次生成的 domain (在沙盒里) 和 skill 路径
            candidate_domain = sm.get_pddl_path()
            candidate_skill = result['skill_file_path']
            
            print(f"[Trainer] 正在启动回归测试以确保系统稳定性...")
            is_safe = regression_mgr.run_regression_suite(candidate_domain, candidate_skill)
            
            if is_safe:
                print(f"[Trainer] 回归测试通过！批准晋升。")
                promote_skill(result, project_root)
                # 将本次成功的任务加入回归库，确保以后不忘
                regression_mgr.save_new_test(task_data)
            else:
                print(f"[Trainer] 回归测试失败！本次进化产生副作用，将被丢弃。")
        else:
            print(f"[Trainer] 任务 '{goal}' 训练失败。")
            
    print("[System] 自动训练已停止。")
    sys.exit(0)
    

if __name__ == "__main__":
    start_auto_training()
#python3 auto_trainer.py