# CoT数据生成器

基于AxiomLabs架构重构的Chain-of-Thought数据生成系统，用于生成高质量、可复现的Agent执行轨迹数据。

## 项目概述

本项目实现了Brain/Nerves双层规划系统，能够：
1. 将复杂任务分解为PDDL格式的任务链
2. 将任务进一步分解为原子动作链
3. 在沙盒环境中执行并验证物理对齐
4. 生成包含完整执行轨迹的CoT数据

## 核心架构

### 双层规划系统
- **Brain层**：高层任务分解与逻辑规划
- **Nerves层**：原子动作执行与物理感知
- **Translator层**：环境事实粒度转换与语义翻译

### 九大原子动作（已完全实现）
1. `scan` - 扫描文件夹
2. `move` - 移动文件
3. `remove` - 删除文件
4. `rename` - 重命名文件
5. `copy` - 复制文件
6. `compress` - 压缩文件
7. `uncompress` - 解压文件
8. `create_file` - 创建文件
9. `create_folder` - 创建文件夹

**状态**: ✅ 所有九大原子动作已实现并通过物理对齐测试

## 快速开始

### 环境准备
```bash
# 进入项目目录
cd cot_generator

# 复制环境配置文件
cp .env.example .env

# 编辑.env文件，设置DEEPSEEK_API_KEY等配置
# 使用文本编辑器打开.env并填写实际值
```

### 运行冒烟测试
```bash
# 运行基础功能测试
python3 tests/test_smoke.py

# 运行配置测试
python3 tests/test_config.py
```

### 运行物理对齐测试
```bash
# 运行全面物理对齐测试
python3 tests/test_physical_alignment_comprehensive.py

# 运行剩余技能测试
python3 tests/test_remaining_skills.py
```

## 项目结构

```
cot_generator/
├── config/            # 配置管理
│   ├── __init__.py
│   ├── constants.py   # 常量定义
│   └── settings.py    # 配置类
├── pddl_configs/     # PDDL配置文件
│   ├── domain_extended.pddl    # 九大原子动作PDDL定义
│   └── problem_example.pddl    # 示例问题文件
├── tests/            # 测试文件
│   ├── test_config.py
│   ├── test_smoke.py
│   ├── test_physical_alignment_comprehensive.py
│   └── test_remaining_skills.py
├── .env.example      # 环境变量示例
└── README.md         # 本文档
```

**架构说明**：
- CoT数据生成器**直接使用主项目的基础设施**（LLM、Translator、Planner、Executor、MCP技能）
- 删除冗余目录，保持架构简洁
- 所有九大原子动作通过主项目的MCP技能实现

## 配置说明

### 主要配置项
```python
# config/settings.py 中的主要配置
DEEPSEEK_API_KEY = "your-api-key"        # DeepSeek API密钥
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# 算法配置
MAX_ITERATIONS = 3
BRAIN_FALSE_LIMIT = 3
NERVES_FALSE_LIMIT = 3
PLANNING_TIMEOUT = 60

# 数据生成配置
DATA_OUTPUT_DIR = "data_output"
MAX_DATA_POINTS_PER_FILE = 1000
```

### 环境变量优先级
1. 系统环境变量
2. .env文件
3. 默认值

## 开发指南

### 第一天：准备环境 ✅
- [x] 创建新的项目结构目录
- [x] 配置开发环境
- [x] 编写基础测试用例

### 第二天：扩展PDDL领域 ✅
- [x] 设计九大原子动作的PDDL定义
- [x] 实现对应的Python技能类
- [x] 测试动作的物理对齐性

### 第三天：实现Translator层
- [ ] 实现粒度转换规则
- [ ] 测试Brain/Nerves环境转换
- [ ] 集成到现有系统中

### 第四天：实现LLM组件
- [ ] 设计并实现BrainLLM
- [ ] 设计并实现NervesLLM
- [ ] 设计并实现AnalysisLLM

### 第五天：实现控制流
- [ ] 实现HypothalamusFilter
- [ ] 实现主控制流算法
- [ ] 集成错误恢复机制

### 第六天：数据生成与输出
- [ ] 定义数据格式Schema
- [ ] 实现数据记录器
- [ ] 实现批量生成工具

## 物理对齐验证

项目已通过全面的物理对齐测试，确保PDDL动作定义与Python技能实现严格一致：

1. **PDDL参数对齐**: 所有九大原子动作的参数数量与类型正确
2. **效果对齐**: 技能执行生成的PDDL事实与PDDL效果完全匹配
3. **文件系统操作**: 技能实际执行的文件系统操作与预期一致
4. **错误处理**: 正确处理各种边界情况和错误场景

运行测试验证：
```bash
cd cot_generator
python3 tests/test_physical_alignment_comprehensive.py
python3 tests/test_remaining_skills.py
```

## 数据格式

生成的CoT数据包含：
- 用户任务描述
- Brain层任务分解链
- Nerves层原子动作链
- 每一步的环境状态变化
- 执行结果与错误信息

示例数据格式：
```json
{
  "task_id": "file_ops_001",
  "user_task": "将root文件夹下的所有txt文件移动到backup文件夹",
  "route_decision": "Brain",
  "brain_layer": {
    "start_env": ["(at file1 root)", "(at file2 root)"],
    "chain_of_mission": ["(scan root)", "(move file1 root backup)"]
  },
  "execution_trace": [
    {
      "step": 1,
      "action": "(scan root)",
      "result": "success",
      "env_changes": ["(scanned root)"]
    }
  ]
}
```

## 技术栈
- **编程语言**: Python 3.8+ (异步/await)
- **规划器**: Fast-Downward (LAMA)
- **LLM集成**: DeepSeek API
- **技能架构**: 异步MCP技能 (九大原子动作)
- **测试框架**: pytest, unittest
- **配置管理**: python-dotenv

## 异步架构说明

本项目采用**全异步架构**，所有技能执行均为异步操作：

### 异步优势
1. **性能优化**: 异步I/O操作提高并发性能
2. **统一接口**: 所有技能使用一致的 `async def execute()` 接口
3. **现代标准**: 符合现代Python异步编程最佳实践
4. **MCP兼容**: 原生支持MCP (Model Context Protocol) 协议

### 技能执行模式
```python
# 异步执行MCP技能
from infrastructure.mcp_skills.scan_skill import ScanSkill

skill = ScanSkill()
result = await skill.execute({"folder": "test_folder"})
```

### 架构简化
- **删除冗余**: 移除了同步技能实现 (`scan_skill.py`, `move_skill.py`)
- **统一基类**: `BaseSkill.execute()` 改为异步接口
- **直接集成**: CoT数据生成器直接使用主项目的MCP技能

## Git工作流

### 推送到当前分支 (cot-data-generator)
```bash
# 添加所有更改
git add .

# 提交更改
git commit -m "[模块] 简要描述"

# 推送到远程分支
git push origin cot-data-generator
```

### 推送到主分支 (main/master)
```bash
# 切换到主分支
git checkout main

# 拉取最新更改
git pull origin main

# 合并功能分支
git merge cot-data-generator

# 解决冲突（如果有）
# 推送到主分支
git push origin main
```

### 创建Pull Request
1. 推送分支到远程：`git push -u origin cot-data-generator`
2. 访问GitHub创建Pull Request
3. 等待代码审查和合并

## 许可证
MIT License

## 维护者
布衣nakili