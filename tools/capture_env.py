import os
import json

def capture_to_setup_actions(storage_path="./storage"):
    """
    扫描当前的 storage 目录，将其转化为 RegressionManager 可用的 setup_actions 列表
    """
    setup_actions = []
    
    # 我们认为 root 是默认存在的，所以从 root 内部开始扫
    for root, dirs, files in os.walk(storage_path):
        # 计算相对路径
        rel_path = os.path.relpath(root, storage_path)
        
        # 1. 记录文件夹（排除根目录本身）
        if rel_path != ".":
            # 找到父目录和当前文件夹名
            parent = os.path.dirname(rel_path)
            folder_name = os.path.basename(rel_path)
            # PDDL 逻辑中通常叫 root
            logic_parent = "root" if parent == "" else parent
            setup_actions.append(["create_folder", folder_name, logic_parent])

        # 2. 记录文件
        for f in files:
            if f.startswith("."): continue # 忽略隐藏文件
            safe_name = f.replace(".", "_dot_")
            logic_folder = "root" if rel_path == "." else rel_path
            setup_actions.append(["create_file", safe_name, logic_folder])

    return setup_actions

if __name__ == "__main__":
    # 示例用法
    print("--- 正在捕获当前 storage 环境 ---")
    actions = capture_to_setup_actions()
    
    # 构造一个标准的回归测试 JSON 片段
    example_case = {
        "task_name": "MANUAL_CAPTURED_TASK",
        "goal": "请在此处手动填入你的自然语言目标",
        "setup_actions": actions
    }
    
    print("\n生成的 setup_actions 内容如下：")
    print(json.dumps(actions, indent=4, ensure_ascii=False))
    
    # 也可以直接保存到临时文件
    with open("captured_env.json", "w", encoding="utf-8") as f:
        json.dump(example_case, f, indent=4, ensure_ascii=False)
    print("\n[Done] 已保存到 captured_env.json，你可以直接复制到回归库中。")