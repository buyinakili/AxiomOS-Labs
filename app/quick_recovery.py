#!/usr/bin/env python3
"""
AIOS-PDDL 快速恢复工具
在快速迭代期，当系统出现问题时快速恢复到可用状态
"""

import os
import sys
import shutil
import json
from pathlib import Path


def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"🔧 {title}")
    print("="*60)


def reset_workspace():
    """重置workspace目录"""
    print_header("重置workspace目录")
    
    workspace_dir = "workspace"
    if os.path.exists(workspace_dir):
        try:
            shutil.rmtree(workspace_dir)
            print(f"✅ 已删除旧的workspace目录: {workspace_dir}")
        except Exception as e:
            print(f"⚠️ 删除workspace目录失败: {e}")
    
    # 创建新的workspace目录结构
    os.makedirs(workspace_dir, exist_ok=True)
    
    # 创建必要的子目录
    subdirs = ["root", "backup", "docs", "archive"]
    for subdir in subdirs:
        os.makedirs(os.path.join(workspace_dir, subdir), exist_ok=True)
        print(f"  📁 创建目录: {subdir}")
    
    # 创建一些测试文件
    test_files = [
        ("root", "readme.txt", "这是一个测试文件"),
        ("root", "notes.md", "# 测试Markdown文件"),
        ("docs", "document.pdf", "PDF文件内容（模拟）"),
    ]
    
    for folder, filename, content in test_files:
        filepath = os.path.join(workspace_dir, folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  📄 创建测试文件: {folder}/{filename}")
    
    print("✅ workspace目录已重置到默认状态")


def restore_pddl_files():
    """恢复PDDL文件到默认状态"""
    print_header("恢复PDDL文件")
    
    pddl_configs_dir = "pddl_configs"
    if not os.path.exists(pddl_configs_dir):
        print(f"❌ PDDL配置目录不存在: {pddl_configs_dir}")
        return False
    
    # 检查备份文件
    backup_files = {
        "domain.pddl.backup": "domain.pddl",
        "problem.pddl.backup": "problem.pddl",
    }
    
    restored = 0
    for backup_name, target_name in backup_files.items():
        backup_path = os.path.join(pddl_configs_dir, backup_name)
        target_path = os.path.join(pddl_configs_dir, target_name)
        
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, target_path)
                print(f"✅ 恢复 {target_name} 从备份")
                restored += 1
            except Exception as e:
                print(f"❌ 恢复 {target_name} 失败: {e}")
        else:
            print(f"⚠️ 备份文件不存在: {backup_name}")
    
    # 如果没有备份，创建默认的PDDL文件
    if restored == 0:
        print("⚠️ 无备份文件，创建默认PDDL文件...")
        create_default_pddl_files()
    
    return True


def create_default_pddl_files():
    """创建默认的PDDL文件"""
    pddl_configs_dir = "pddl_configs"
    os.makedirs(pddl_configs_dir, exist_ok=True)
    
    # 默认domain.pddl
    domain_content = """(define (domain file_management)
  (:requirements :strips :typing)
  
  (:types
    file folder
  )
  
  (:predicates
    (at ?f - file ?d - folder)
    (is_created ?f - file)
    (is_folder ?d - folder)
  )
  
  (:action scan
    :parameters (?d - folder)
    :precondition (is_folder ?d)
    :effect (and )
  )
  
  (:action move
    :parameters (?f - file ?from - folder ?to - folder)
    :precondition (and (at ?f ?from) (is_folder ?to))
    :effect (and (at ?f ?to) (not (at ?f ?from)))
  )
  
  (:action compress
    :parameters (?f - file ?d - folder ?a - file)
    :precondition (and (at ?f ?d))
    :effect (and (is_created ?a) (not (at ?f ?d)))
  )
)
"""
    
    # 默认problem.pddl
    problem_content = """(define (problem file_management_problem)
  (:domain file_management)
  
  (:objects
    readme_dot_txt notes_dot_md document_dot_pdf - file
    root backup docs archive - folder
  )
  
  (:init
    (is_folder root)
    (is_folder backup)
    (is_folder docs)
    (is_folder archive)
    
    (at readme_dot_txt root)
    (at notes_dot_md root)
    (at document_dot_pdf docs)
  )
  
  (:goal (and
    (at readme_dot_txt backup)
    (at notes_dot_md backup)
  ))
)
"""
    
    # 写入文件
    with open(os.path.join(pddl_configs_dir, "domain.pddl"), 'w', encoding='utf-8') as f:
        f.write(domain_content)
    print("✅ 创建默认 domain.pddl")

    with open(os.path.join(pddl_configs_dir, "problem.pddl"), 'w', encoding='utf-8') as f:
        f.write(problem_content)
    print("✅ 创建默认 problem.pddl")

    # 创建备份
    shutil.copy2(os.path.join(pddl_configs_dir, "domain.pddl"),
                 os.path.join(pddl_configs_dir, "domain.pddl.backup"))
    shutil.copy2(os.path.join(pddl_configs_dir, "problem.pddl"),
                 os.path.join(pddl_configs_dir, "problem.pddl.backup"))
    print("✅ 创建PDDL文件备份")


def clear_regression_registry():
    """清理回归注册表"""
    print_header("清理回归注册表")
    
    registry_path = os.path.join("pddl_configs", "regression_registry.json")
    
    if os.path.exists(registry_path):
        try:
            # 读取当前内容（用于备份）
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)
            
            # 创建备份
            backup_path = os.path.join("pddl_configs", "regression_registry.json.backup")
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
            print(f"✅ 已备份回归注册表: {backup_path}")
            
            # 清空注册表
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            print("✅ 已清空回归注册表")
            
        except Exception as e:
            print(f"❌ 处理回归注册表失败: {e}")
    else:
        print("ℹ️ 回归注册表不存在，无需清理")


def clear_sandbox_runs():
    """清理沙盒运行目录"""
    print_header("清理沙盒运行目录")
    
    sandbox_dir = "sandbox_runs"
    if os.path.exists(sandbox_dir):
        try:
            # 只删除内容，保留目录
            for item in os.listdir(sandbox_dir):
                item_path = os.path.join(sandbox_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            print(f"✅ 已清理沙盒运行目录: {sandbox_dir}")
        except Exception as e:
            print(f"⚠️ 清理沙盒运行目录失败: {e}")
    else:
        print(f"ℹ️ 沙盒运行目录不存在: {sandbox_dir}")


def check_system_health():
    """检查系统健康状态"""
    print_header("系统健康检查")
    
    checks = [
        ("项目根目录", ".", os.path.exists),
        ("pddl_configs目录", "pddl_configs", os.path.exists),
        ("workspace目录", "workspace", os.path.exists),
        ("domain.pddl文件", "pddl_configs/domain.pddl", os.path.exists),
        ("problem.pddl文件", "pddl_configs/problem.pddl", os.path.exists),
        ("config目录", "config", os.path.exists),
        ("app目录", "app", os.path.exists),
    ]
    
    all_ok = True
    for check_name, path, check_func in checks:
        if check_func(path):
            print(f"✅ {check_name}: {path}")
        else:
            print(f"❌ {check_name}: {path} (不存在)")
            all_ok = False
    
    return all_ok


def main():
    """主函数"""
    print("="*60)
    print("AIOS-PDDL 快速恢复工具 v0.5.0")
    print("="*60)
    print("功能: 在快速迭代期快速恢复系统到可用状态")
    print("="*60)
    
    # 检查当前目录
    current_dir = os.getcwd()
    print(f"当前目录: {current_dir}")
    
    # 显示选项
    print("\n请选择恢复操作:")
    print("1. 快速恢复（推荐） - 重置workspace和PDDL文件")
    print("2. 完全恢复 - 重置所有内容到默认状态")
    print("3. 仅检查系统健康状态")
    print("4. 退出")
    
    try:
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == "1":
            # 快速恢复
            reset_workspace()
            restore_pddl_files()
            clear_sandbox_runs()
            print_header("快速恢复完成")
            print("✅ 系统已快速恢复到可用状态")
            print("💡 建议运行: python tests/test_smoke.py 验证系统")
            
        elif choice == "2":
            # 完全恢复
            reset_workspace()
            restore_pddl_files()
            clear_regression_registry()
            clear_sandbox_runs()
            print_header("完全恢复完成")
            print("✅ 系统已完全恢复到默认状态")
            print("💡 所有用户数据和训练记录已被清除")
            
        elif choice == "3":
            # 仅检查
            if check_system_health():
                print_header("系统健康状态: ✅ 正常")
                print("所有关键文件和目录都存在")
            else:
                print_header("系统健康状态: ⚠️ 有问题")
                print("建议运行快速恢复（选项1）修复问题")
                
        elif choice == "4":
            print("退出恢复工具")
            return
            
        else:
            print("❌ 无效选项，请重新运行")
            
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
    except Exception as e:
        print(f"\n❌ 恢复过程中发生错误: {e}")
        print("请手动检查文件系统状态")


if __name__ == "__main__":
    main()