# AIOS - 自演化智能操作系统

## Claude 协作规则

**重要：与 Claude 协作时的注意事项**

- **提问 vs 修改**：当用户提出问题时，Claude 应该**仅回答问题**，不要主动修改代码
- **明确指令**：只有当用户明确说"修改"、"修复"、"帮我改"等指令时，才可以进行代码修改
- **询问确认**：如果回答问题后认为需要修改代码，应该先询问用户是否需要修改，而不是直接动手

---

## 项目概述

AIOS（Autonomous Intelligent Operating System）是一个**自演化智能操作系统内核**，核心创新是将大语言模型（LLM）的概率性约束在符号逻辑的确定性空间中，实现可靠的任务执行和自主学习能力。

### 核心特性

- **符号规划驱动执行**：使用PDDL和Fast Downward规划器确保逻辑严密
- **自演化学习**：在沙盒环境中自动学习新技能
- **三层验证架构**：语义解析层、符号规划层、物理追踪层
- **清洁架构设计**：算法与工程完全分离，易于测试和扩展

---

## 架构设计

项目采用**三层分离架构**（Clean Architecture），实现算法与工程的完全解耦：

```
┌─────────────────────────────────────────────────────┐
│           Algorithm Layer（算法层）                  │
│   - 纯业务逻辑，不依赖具体实现                       │
│   - 只依赖接口定义                                   │
│   - 可独立测试                                       │
└──────────────────┬──────────────────────────────────┘
                   ↓ 依赖
┌─────────────────────────────────────────────────────┐
│         Interface Layer（接口抽象层）                │
│   - 定义所有抽象接口（ABC）                          │
│   - 算法层和工程层的契约                             │
└──────────────────┬──────────────────────────────────┘
                   ↑ 实现
┌─────────────────────────────────────────────────────┐
│      Infrastructure Layer（工程实现层）              │
│   - 具体技术实现                                     │
│   - 可替换、可扩展                                   │
│   - 处理所有技术细节                                 │
└─────────────────────────────────────────────────────┘
```

### 目录结构

```
AIOS/
├── interface/                      # 接口层（抽象定义）
│   ├── planner.py                  # 规划器接口
│   ├── translator.py               # 翻译器接口
│   ├── executor.py                 # 执行器接口
│   ├── storage.py                  # 存储接口
│   ├── llm.py                      # LLM接口
│   ├── skill.py                    # 技能接口
│   └── domain_expert.py            # 领域专家接口
│
├── algorithm/                      # 算法层（纯逻辑）
│   ├── kernel.py                   # 核心流程编排算法
│   ├── evolution.py                # 进化算法（待实现）
│   ├── curriculum.py               # 课程生成算法（待实现）
│   └── regression.py               # 回归测试算法（待实现）
│
├── infrastructure/                 # 工程层（具体实现）
│   ├── translator/
│   │   └── pddl_translator.py      # PDDL翻译器实现
│   ├── planner/
│   │   └── lama_planner.py         # LAMA规划器实现
│   ├── executor/
│   │   └── action_executor.py      # 动作执行器实现
│   ├── storage/
│   │   └── file_storage.py         # 文件存储实现
│   ├── llm/
│   │   └── deepseek_client.py      # DeepSeek LLM实现
│   ├── skills/                     # 技能实现
│   │   ├── base_skill.py           # 技能基类
│   │   ├── filesystem_skills.py    # 基础文件系统技能
│   │   ├── remove_file_skill.py    # AI学习：删除文件
│   │   └── rename_file_skill.py    # AI学习：重命名文件
│   └── domain/                     # 领域专家实现
│       └── file_management_expert.py
│
├── config/                         # 配置管理
│   └── settings.py                 # 统一配置类
│
├── app/                            # 应用层（组装）
│   ├── factory.py                  # 依赖注入工厂
│   └── main_demo.py                # 生产模式入口
│
├── tests/                          # PDDL定义和测试数据
│   ├── domain.pddl                 # 主Domain定义
│   └── regression_registry.json    # 回归测试用例库
│
├── storage/                        # 物理存储
│   ├── root/                       # 模拟根目录
│   └── backup/                     # 模拟备份目录
│
└── downward/                       # Fast Downward规划器
```

---

## 核心组件说明

### 1. 接口层（interface/）

定义系统所有核心接口，算法层只依赖这些接口，不依赖具体实现。

**主要接口：**
- `IPlanner`: 规划器接口，定义 `plan()` 和 `verify_syntax()` 方法
- `ITranslator`: 翻译器接口，定义 `route_domain()` 和 `translate()` 方法
- `IExecutor`: 执行器接口，定义 `execute()` 和技能管理方法
- `IStorage`: 存储接口，定义PDDL文件读写方法
- `ILLM`: LLM接口，定义 `chat()` 方法
- `ISkill`: 技能接口，所有技能必须实现此接口
- `IDomainExpert`: 领域专家接口，提供特定领域的规则

**数据传输对象（DTO）：**
- `PlanningResult`: 规划结果
- `ExecutionResult`: 执行结果

### 2. 算法层（algorithm/）

纯业务逻辑，只依赖接口，不包含任何技术实现细节。

**核心算法：**
- `AIOSKernel`: 核心流程编排
  - 领域路由
  - PDDL生成
  - 规划执行
  - 事实库管理
  - 迭代控制

### 3. 工程层（infrastructure/）

所有接口的具体实现，处理技术细节。

**主要实现：**
- `LAMAPlanner`: 基于Fast Downward的规划器实现
- `PDDLTranslator`: PDDL翻译器实现
- `ActionExecutor`: 动作执行器实现
- `FileStorage`: 基于文件系统的存储实现
- `DeepSeekClient`: DeepSeek LLM客户端实现
- `BaseSkill`: 技能基类，提供路径处理等通用功能

### 4. 配置层（config/）

统一的配置管理，所有配置项集中在 `Settings` 类中。

**配置项：**
- 路径配置：项目根路径、存储路径、测试路径等
- Fast Downward配置：可执行文件路径、超时时间
- LLM配置：API密钥、基础URL、模型名称
- 运行配置：最大迭代次数、进化重试次数等

### 5. 应用层（app/）

负责组装所有组件，通过依赖注入将具体实现注入到算法层。

**核心类：**
- `AIOSFactory`: 依赖注入工厂，负责创建和组装所有组件
- `main_demo.py`: 生产模式入口

---

## 核心工作流程

### 生产模式流程

```
1. 用户输入目标
   ↓
2. [Translator] 领域路由（判断任务属于哪个领域）
   ↓
3. [Translator] 生成PDDL Problem（结合已知事实）
   ↓
4. [Planner] Fast Downward规划
   ├─ 成功 → 返回动作序列
   └─ 失败 → 记录错误，进入下一轮迭代
   ↓
5. [Executor] 逐步执行动作
   ├─ 成功 → 更新事实库（add_facts, del_facts）
   └─ 失败 → 记录错误，进入下一轮迭代
   ↓
6. 检查目标是否达成
   ├─ 是 → 任务完成
   └─ 否 → 返回步骤3（最多5次迭代）
```

### 事实库管理

系统维护一个 `memory_facts: Set[str]`，存储当前环境的PDDL事实。

**事实更新规则：**
1. 每个技能执行后返回 `add_facts` 和 `del_facts`
2. Kernel根据返回结果更新事实库
3. 下一轮规划使用更新后的事实库

**示例：**
```python
# 初始状态
memory_facts = {
    "(at test_dot_txt root)",
    "(connected root backup)"
}

# 执行 move test_dot_txt root backup
result = executor.execute("move test_dot_txt root backup")
# result.add_facts = ["(at test_dot_txt backup)"]
# result.del_facts = ["(at test_dot_txt root)"]

# 更新后
memory_facts = {
    "(at test_dot_txt backup)",
    "(connected root backup)"
}
```

---

## 使用方法

### 环境准备

1. **安装依赖**：
```bash
pip install openai python-dotenv
```

2. **配置环境变量**（创建 `.env` 文件）：
```env
DEEPSEEK_API_KEY=sk-your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DOWNWARD_PATH=/home/nakili/projects/AIOS/downward/fast-downward.py
```

3. **确保Fast Downward可执行**：
```bash
chmod +x downward/fast-downward.py
```

### 运行生产模式

```bash
# 方式1：命令行参数指定任务
python3 app/main_demo.py "删除root下的txt文件"

# 方式2：交互式（修改main_demo.py中的默认任务）
python3 app/main_demo.py
```

### 示例任务

```bash
# 扫描文件夹
python3 app/main_demo.py "扫描root文件夹"

# 移动文件
python3 app/main_demo.py "把root下的txt文件移动到backup文件夹下"

# 删除文件
python3 app/main_demo.py "删除root下的txt文件"

# 重命名文件
python3 app/main_demo.py "重命名root下的txt文件为new.txt"
```

---

## 技能系统

### 已有技能

**基础技能（硬编码）：**
1. `scan`: 扫描文件夹，返回文件和连接关系
2. `move`: 移动文件
3. `get_admin`: 获取管理员权限（模拟）
4. `compress`: 压缩文件（模拟）

**AI学习技能：**
5. `remove_file`: 删除文件
6. `rename_file`: 重命名文件

### 技能开发

所有技能必须实现 `ISkill` 接口：

```python
from infrastructure.skills.base_skill import BaseSkill
from interface.executor import ExecutionResult

class MySkill(BaseSkill):
    @property
    def name(self):
        return 'my_skill'

    def execute(self, args):
        # 实现技能逻辑
        # 使用 self._safe_path() 处理路径
        # 返回 ExecutionResult
        return ExecutionResult(
            success=True,
            message="操作成功",
            add_facts=["(new_fact)"],
            del_facts=["(old_fact)"]
        )
```

**技能文件命名规范：**
- 文件名必须以 `_skill.py` 结尾
- 类名必须为 `GeneratedSkill`（动态加载）
- 放在 `infrastructure/skills/` 目录下

---

## PDDL相关

### 文件名转义规则

所有包含 `.` 的文件名必须转义为 `_dot_`：
```
test.txt    → test_dot_txt
data.json   → data_dot_json
```

技能基类提供了自动转换方法：
- `_safe_path()`: 自动将 `_dot_` 转换为 `.` 并构建路径
- `_to_pddl_name()`: 将文件名转换为PDDL格式
- `_from_pddl_name()`: 将PDDL格式转换回文件名

### Domain定义

主Domain文件位于 `tests/domain.pddl`，定义了：
- **类型**：file, folder, archive
- **谓词**：at, connected, has_admin_rights, scanned, is_created, is_compressed
- **动作**：scan, move, get_admin, compress, remove_file, rename_file等

---

## 扩展指南

### 添加新领域

1. **创建领域专家**：
```python
# infrastructure/domain/network_expert.py
from interface.domain_expert import IDomainExpert

class NetworkExpert(IDomainExpert):
    @property
    def domain_name(self):
        return "network_operation"

    def get_rules(self):
        return [
            "1. 未探测的IP不可直接操作",
            "2. 必须先ping再连接"
        ]

    def get_domain_file(self):
        return "network_domain.pddl"
```

2. **在Factory中注册**：
```python
# app/factory.py
domain_experts = {
    "file_management": FileManagementExpert(),
    "network_operation": NetworkExpert()  # 新增
}
```

### 替换LLM实现

1. **创建新的LLM客户端**：
```python
# infrastructure/llm/claude_client.py
from interface.llm import ILLM

class ClaudeClient(ILLM):
    def chat(self, messages, temperature=0, response_format=None):
        # 实现Claude API调用
        pass
```

2. **在Factory中替换**：
```python
# app/factory.py
llm = ClaudeClient(api_key=config.llm_api_key)
```

### 添加新的规划器

1. **实现IPlanner接口**：
```python
# infrastructure/planner/custom_planner.py
from interface.planner import IPlanner, PlanningResult

class CustomPlanner(IPlanner):
    def plan(self, domain_content, problem_content):
        # 实现自定义规划逻辑
        pass

    def verify_syntax(self, domain_content):
        # 实现语法检查
        pass
```

2. **在Factory中替换**：
```python
planner = CustomPlanner()
```

---

## 测试

### 单元测试示例

由于采用依赖注入，可以轻松mock接口进行测试：

```python
from algorithm.kernel import AIOSKernel
from unittest.mock import Mock

def test_kernel_basic_flow():
    # Mock所有依赖
    mock_translator = Mock()
    mock_planner = Mock()
    mock_executor = Mock()
    mock_storage = Mock()

    # 配置Mock行为
    mock_translator.route_domain.return_value = "file_management"
    mock_translator.translate.return_value = "(define ...)"
    # ...

    # 创建内核
    kernel = AIOSKernel(
        translator=mock_translator,
        planner=mock_planner,
        executor=mock_executor,
        storage=mock_storage
    )

    # 测试
    result = kernel.run("test task")
    assert result == True
```

---

## 故障排查

### 常见问题

**1. "DOWNWARD_PATH不存在"**
- 检查 `.env` 文件中的路径是否正确
- 确保Fast Downward可执行权限

**2. "LLM API Key未配置"**
- 检查 `.env` 文件中是否设置了 `DEEPSEEK_API_KEY`

**3. "规划失败：目标不可达"**
- 检查初始事实库是否正确
- 检查PDDL Domain中是否定义了相应的动作
- 查看详细的PDDL输出（系统会打印）

**4. "技能未找到GeneratedSkill类"**
- 确保技能文件中的类名为 `GeneratedSkill`
- 检查技能文件是否在正确的目录

### 调试模式

修改 `main_demo.py` 以查看详细日志：

```python
# 添加更详细的日志输出
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 架构优势

### 1. 算法与工程分离
- **算法层**：纯逻辑，易于理解和验证
- **工程层**：技术细节，可独立优化
- **测试性**：可以轻松mock接口进行单元测试

### 2. 高度可扩展
- 新增领域：实现 `IDomainExpert` 并注册
- 替换LLM：实现 `ILLM` 接口
- 替换规划器：实现 `IPlanner` 接口
- 添加技能：实现 `ISkill` 接口

### 3. 配置集中管理
- 所有配置项在 `Settings` 类中
- 支持环境变量和默认值
- 易于管理和维护

### 4. 依赖注入
- 通过 `AIOSFactory` 组装组件
- 松耦合，易于替换实现
- 支持测试和开发环境分离

---

## 后续开发计划

### 待实现功能

1. **进化管理器**（`algorithm/evolution.py`）
   - 沙盒环境管理
   - 自动生成PDDL补丁和Python技能
   - 虚假进化审计

2. **课程管理器**（`algorithm/curriculum.py`）
   - 智能出题算法
   - 任务难度递进

3. **回归测试管理器**（`algorithm/regression.py`）
   - 自动回归测试
   - 新技能安全验证

4. **训练模式入口**（`app/auto_trainer.py`）
   - 自动训练流程
   - 技能晋升机制

### 优化方向

1. 性能优化：
   - PDDL解析缓存
   - 规划结果缓存
   - 并行执行支持

2. 功能增强：
   - 支持更多领域（网络操作、数据库操作等）
   - 支持复合技能（技能组合）
   - 支持条件执行和循环

3. 用户体验：
   - Web界面
   - 任务历史记录
   - 可视化执行过程

---

## 贡献指南

### 开发流程

1. 接口优先：修改或新增功能时，先定义或修改接口
2. 实现分离：算法逻辑在 `algorithm/`，技术实现在 `infrastructure/`
3. 配置统一：新增配置项在 `Settings` 类中
4. 测试覆盖：为新功能编写单元测试

### 代码风格

- 遵循PEP 8规范
- 使用类型提示
- 编写清晰的文档字符串
- 保持函数简洁（单一职责）

---

## 联系方式

项目地址：`/home/nakili/projects/AIOS`

---

## 许可证

本项目为个人研究项目。

---

**最后更新：2026-01-25**
