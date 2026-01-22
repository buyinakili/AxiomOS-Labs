import os
import shutil
import time
import zipfile

def create_update_package():
    print("=== AIOS 系统版本压缩打包工具 ===")
    
    # 1. 获取版本号
    version = input("请输入当前版本号 (例如 1.0.2): ").strip()
    if not version:
        version = time.strftime("%Y%m%d_%H%M%S")
        print(f"未检测到版本号，将使用时间戳: {version}")

    # 2. 定义路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    save_root = os.path.join(project_root, "SaveAIOS")
    version_tag = f"AIOS_v{version}"
    temp_dir = os.path.join(save_root, version_tag) # 临时存放文件夹
    zip_file_path = f"{temp_dir}.zip"             # 最终生成的压缩包路径

    # 定义需要打包的内容
    include_dirs = ["tests", "storage", "modules", "core","tools"]
    include_files = ["main_demo.py", "train_env_v1.py","auto_trainer.py","config.py",".env"]

    # 3. 检查冲突
    if os.path.exists(zip_file_path):
        choice = input(f"压缩包 {version_tag}.zip 已存在，是否覆盖？(y/n): ")
        if choice.lower() != 'y':
            print("取消打包。")
            return
        os.remove(zip_file_path)

    # 4. 创建临时结构
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        print(f"\n[1/3] 正在收集文件到临时目录...")
        # 拷贝目录
        for d in include_dirs:
            src_path = os.path.join(project_root, d)
            dst_path = os.path.join(temp_dir, d)
            if os.path.exists(src_path):
                shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '.DS_Store', 'sas_plan', 'output.sas', 'sandbox_runs'
                ))
                print(f"  - 已加入目录: {d}")

        # 拷贝文件
        for f in include_files:
            src_file = os.path.join(project_root, f)
            dst_file = os.path.join(temp_dir, f)
            if os.path.exists(src_file):
                shutil.copy2(src_file, dst_file)
                print(f"  - 已加入文件: {f}")

        # 5. 执行压缩
        print(f"[2/3] 正在生成压缩包: {version_tag}.zip ...")
        
        # 使用 shutil 的高层接口直接打包整个临时目录
        # base_name: 压缩包文件名（不含后缀）, format: 格式, root_dir: 被压缩的根目录
        shutil.make_archive(temp_dir, 'zip', temp_dir)

        print(f"[3/3] 清理临时文件...")
    
    finally:
        # 无论成功失败，都清理掉中间生成的文件夹，保持 SaveAIOS 干净
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    print(f"\n打包成功！")
    print(f"最终位置: {zip_file_path}")

if __name__ == "__main__":
    create_update_package()
    
#python3 update_system.py