# AIOS-PDDL v0.5.0 快速迭代工具指南

## 🎯 概述

本文档介绍为快速迭代期（一天2-3个小版本）设计的工具集，帮助你在快速开发中保持系统稳定性。

## 📦 工具列表

### 1. 冒烟测试 (`tests/test_smoke.py`)
**目的**: 确保核心功能在快速迭代中不崩溃

#### 使用方法
```bash
# 运行所有冒烟测试
python3 tests/test_smoke.py

# 使用pytest运行（更详细）
python3 -m pytest tests/test_smoke.py -v
```

#### 测试内容
- ✅ `main_demo.py --help` 命令是否正常
- ✅ `auto_trainer.py --help` 命令是否正常
- ✅ `auto_trainer.py --task` 参数解析是否正常
- ✅ 配置导入是否正常
- ✅ 工厂类导入是否正常
- ✅ MCP技能导入是否正常

#### 集成到工作流
```bash
# 每日开始工作前运行
python3 tests/test_smoke.py

# 如果测试失败，使用快速恢复工具
python3 app/quick_recovery.py
```

### 2. 关键配置验证 (`config/settings.py` 中的 `validate_critical()`)
**目的**: 快速检查会导致系统崩溃的关键配置

#### 使用方法
```python
from config.settings import Settings

# 加载配置
config = Settings.load_from_env()

# 完整验证（检查所有配置）
try:
    config.validate()
    print("✅ 所有配置验证通过")
except ValueError as e:
    print(f"❌ 配置错误: {e}")

# 关键验证（快速检查，推荐在快速迭代期使用）
try:
    config.validate_critical()
    print("✅ 关键配置验证通过")
except ValueError as e:
    print(f"❌ 关键配置错误: {e}")
```

#### 验证内容
- ✅ 项目根目录是否存在
- ✅ LLM API密钥是否配置（不能是默认值）
- ✅ Fast-Downward路径是否存在
- ✅ tests目录和PDDL文件是否存在
- ✅ workspace目录是否有写入权限

#### 错误示例
```
❌ 关键配置验证失败:
❌ LLM API密钥未配置（请设置DEEPSEEK_API_KEY环境变量）
❌ Fast-Downward路径不存在: /path/to/downward/fast-downward.py

💡 快速修复建议:
1. 检查.env文件或环境变量
2. 运行 'python app/quick_recovery.py' 进行系统健康检查
3. 参考 README.md 中的安装指南
```

### 3. 快速恢复工具 (`app/quick_recovery.py`)
**目的**: 当系统出现问题时快速恢复到可用状态

#### 使用方法
```bash
# 交互式恢复
python3 app/quick_recovery.py

# 直接快速恢复（非交互式）
python3 -c "from app.quick_recovery import reset_workspace, restore_pddl_files; reset_workspace(); restore_pddl_files()"
```

#### 恢复选项
1. **快速恢复（推荐）**
   - 重置workspace目录到默认状态
   - 恢复PDDL文件从备份
   - 清理沙盒运行目录

2. **完全恢复**
   - 重置workspace目录
   - 恢复PDDL文件
   - 清理回归注册表
   - 清理沙盒运行目录

3. **系统健康检查**
   - 检查所有关键文件和目录
   - 报告系统状态

#### 恢复内容
- 📁 `workspace/` 目录：重置到默认结构
- 📄 `tests/domain.pddl` 和 `tests/problem.pddl`：从备份恢复
- 📋 `tests/regression_registry.json`：清空或备份
- 🗑️ `sandbox_runs/` 目录：清理所有运行记录

### 4. 轻量级日志工具 (`utils/simple_logger.py`)
**目的**: 提供简单、彩色、高效的日志系统

#### 基本使用
```python
from utils.simple_logger import get_logger, info, success, error

# 方式1：使用全局函数
info("系统启动中...")
success("系统启动成功")
error("系统启动失败")

# 方式2：使用日志器实例
logger = get_logger("MyModule")
logger.info("模块初始化")
logger.success("模块加载完成")
logger.error("模块加载失败", error_code=500)

# 方式3：带上下文的日志
logger.set_context(user="alice", task_id=123).info("开始处理任务")
logger.set_context(progress=50).info("任务处理中")
logger.set_context(result="success").success("任务完成")
```

#### 高级功能
```python
# 章节标题
logger.section("数据预处理")

# 步骤跟踪
logger.step(1, 5, "加载数据")
logger.step(2, 5, "清洗数据")
logger.step(3, 5, "特征工程")

# 进度条
for i in range(1, 101):
    logger.progress(i, 100, "训练模型")
    # ... 训练代码
```

#### 日志级别
```python
from utils.simple_logger import LogLevel

logger = get_logger("Test")
logger.debug("调试信息")      # 🔍 灰色
logger.info("一般信息")       # ℹ️ 蓝色  
logger.success("成功信息")    # ✅ 绿色
logger.warning("警告信息")    # ⚠️ 黄色
logger.error("错误信息")      # ❌ 红色
logger.critical("严重错误")   # 💥 红底白字
```

## 🔄 快速迭代工作流

### 每日工作流模板
```bash
# 1. 早上开始工作前
python tests/test_smoke.py              # 确保昨天的工作没破坏核心功能
python app/quick_recovery.py            # 如果需要，快速恢复系统

# 2. 开发新功能
# ... 你的开发工作 ...

# 3. 晚上提交前
python tests/test_smoke.py              # 确保新功能没破坏核心功能
python -c "from config.settings import Settings; Settings.load_from_env().validate_critical()"  # 验证配置

# 4. 创建版本快照（可选）
# 手动备份关键文件或使用git标签
git tag v0.5.1  # 创建git标签作为版本快照
```

### 遇到问题时的解决流程
```
问题：运行main_demo.py时崩溃
解决：
1. python tests/test_smoke.py              # 查看哪个测试失败
2. python app/quick_recovery.py            # 选择快速恢复
3. python tests/test_smoke.py              # 再次验证
4. 如果还失败，检查配置：
   python -c "from config.settings import Settings; print(Settings.load_from_env())"
```

## 🛠️ 工具集成示例

### 在现有代码中使用新工具

#### 示例1：在main_demo.py中添加配置验证
```python
# 在app/main_demo.py的main函数开头添加
def main():
    # ... 参数解析 ...
    
    # 关键配置验证
    try:
        config.validate_critical()
    except ValueError as e:
        print(f"❌ 配置错误，无法启动系统:\n{e}")
        sys.exit(1)
    
    # ... 原有代码 ...
```

#### 示例2：在auto_trainer.py中使用新日志系统
```python
# 在app/auto_trainer.py开头添加
from utils.simple_logger import get_logger

logger = get_logger("AutoTrainer")

# 替换原有的print语句
# print(f"[Main] 配置加载完成")  # 旧
logger.info("配置加载完成")      # 新

# print(f"[Trainer] 任务生成成功: {task_data['goal']}")  # 旧
logger.success(f"任务生成成功: {task_data['goal']}")     # 新
```

#### 示例3：添加自动化健康检查
```python
# utils/daily_check.py  # 建议创建此文件
#!/usr/bin/env python3
"""每日健康检查脚本"""
import subprocess
import sys
from utils.simple_logger import get_logger

logger = get_logger("DailyCheck")

def run_check():
    logger.section("AIOS-PDDL 每日健康检查")
    
    # 1. 运行冒烟测试
    logger.info("运行冒烟测试...")
    result = subprocess.run([sys.executable, "tests/test_smoke.py"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.success("冒烟测试通过")
    else:
        logger.error("冒烟测试失败")
        print(result.stdout)
        print(result.stderr)
        return False
    
    # 2. 检查配置
    logger.info("检查关键配置...")
    # ... 配置检查代码 ...
    
    logger.success("所有检查通过，系统健康")
    return True

if __name__ == "__main__":
    success = run_check()
    sys.exit(0 if success else 1)
```

## 📈 版本管理建议

### 版本命名规则
```
v0.5.0    - 当前稳定版（准备发布）
v0.5.1    - 今日第一个更新（功能A）
v0.5.2    - 今日第二个更新（功能B）  
v0.5.3    - 今日第三个更新（修复bug）
v0.6.0    - 下一个稳定版（功能积累到一定程度）
```

### 版本快照工具（建议创建）
```python
# utils/create_snapshot.py  # 建议创建此文件
import shutil
import os
from datetime import datetime

def create_snapshot(version):
    """创建版本快照"""
    snapshot_dir = f"snapshots/{version}"
    os.makedirs(snapshot_dir, exist_ok=True)
    
    # 备份关键文件
    key_files = [
        "tests/domain.pddl",
        "tests/problem.pddl", 
        "tests/regression_registry.json",
        "config/.env.example",
        "requirements.txt",
        "README.md"
    ]
    
    for file in key_files:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(snapshot_dir, os.path.basename(file)))
    
    print(f"✅ 已创建版本快照: {snapshot_dir}")
```

## 🚀 快速开始

### 5分钟设置
1. **安装依赖**（如果还没安装）:
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**:
   ```bash
   cp .env.example .env
   # 编辑.env文件，设置你的API密钥
   ```

3. **运行健康检查**:
   ```bash
   python tests/test_smoke.py
   python app/quick_recovery.py  # 如果需要，选择快速恢复
   ```

4. **开始开发**:
   ```bash
   # 开发新功能...
   ```

5. **提交前验证**:
   ```bash
   python tests/test_smoke.py
   ```

## 📞 故障排除

### 常见问题

#### Q1: 冒烟测试失败，显示"ModuleNotFoundError"
**A**: 确保在项目根目录运行测试，或设置PYTHONPATH:
```bash
export PYTHONPATH=/path/to/your/project:$PYTHONPATH
python tests/test_smoke.py
```

#### Q2: 配置验证失败，显示"LLM API密钥未配置"
**A**: 检查.env文件或环境变量:
```bash
# 检查当前环境变量
echo $DEEPSEEK_API_KEY

# 或者检查.env文件
cat .env | grep DEEPSEEK_API_KEY
```

#### Q3: 快速恢复工具无法恢复PDDL文件
**A**: 手动创建备份或使用默认文件:
```bash
# 手动创建PDDL文件备份
cp tests/domain.pddl tests/domain.pddl.backup
cp tests/problem.pddl tests/problem.pddl.backup

# 然后再次运行快速恢复
python app/quick_recovery.py
```

#### Q4: 日志没有颜色
**A**: 颜色只在终端中显示，在重定向或某些IDE中可能不显示。这是正常现象。

## 🎯 总结

这些工具的设计原则是：
1. **轻量级** - 不影响开发速度
2. **实用** - 解决实际问题
3. **可集成** - 容易整合到现有工作流
4. **快速** - 执行时间短，不拖慢迭代

在快速迭代期，**保持迭代速度比追求完美更重要**。使用这些工具确保基本稳定性，继续快速向v0.6.0、v0.7.0前进！

---

*最后更新: 2026-01-29*
*版本: v0.5.0*
*维护者: AIOS-PDDL 开发团队*