# AIOS-PDDL 架构硬编码问题报告

## 概述
通过对整个AIOS-PDDL架构的全面遍历（algorithm、app、config、infrastructure、interface、tests目录），发现了多处硬编码问题。这些硬编码值降低了系统的灵活性和可配置性。

## 硬编码问题分类

### 1. 路径硬编码

#### 1.1 文件路径硬编码
- **文件**: `infrastructure/domain/file_management_expert.py`
  - 第31行: `return "domain.pddl"` - 硬编码domain文件名
  - 建议: 从配置中读取domain文件名

- **文件**: `infrastructure/sandbox/sandbox_manager.py`
  - 第36行: `src_domain = os.path.join(self.tests_path, "domain.pddl")` - 硬编码domain文件名
  - 第37行: `dst_domain = os.path.join(sandbox_dir, "domain_exp.pddl")` - 硬编码输出文件名
  - 第43行: `dst_storage = os.path.join(sandbox_dir, "storage_jail")` - 硬编码存储目录名
  - 第52行: `os.makedirs(os.path.join(sandbox_dir, "skills"), exist_ok=True)` - 硬编码技能目录名

- **文件**: `infrastructure/storage/file_storage.py`
  - 第22行: `def read_domain(self, domain_name: str = "file_management") -> str:` - 硬编码默认domain名称
  - 建议: 移除默认值或从配置读取

#### 1.2 目录结构硬编码
- **文件**: `config/settings.py`
  - 第53-57行: 硬编码了多个路径构建逻辑
  ```python
  tests_path = os.path.join(project_root, "tests")
  storage_path = os.path.join(project_root, "workspace")
  sandbox_runs_path = os.path.join(project_root, "sandbox_runs")
  skills_path = os.path.join(project_root, "infrastructure", "skills")
  temp_dir = os.path.join(project_root, ".temp")
  ```
  - 建议: 这些路径应该可以通过环境变量配置

### 2. 配置值硬编码

#### 2.1 默认配置值硬编码
- **文件**: `config/settings.py`
  - 第72行: `os.path.join(project_root, "downward", "fast-downward.py")` - 硬编码Fast-Downward路径
  - 第77行: `"https://api.deepseek.com"` - 硬编码DeepSeek API URL
  - 第79行: `"deepseek-chat"` - 硬编码模型名称
  - 第80行: `"5"` - 硬编码最大迭代次数
  - 第81行: `"4"` - 硬编码最大进化重试次数
  - 第82行: `"30"` - 硬编码规划超时时间
  - 第85行: `"mcp_server_structured.py"` - 硬编码MCP服务器参数

#### 2.2 算法参数硬编码
- **文件**: `algorithm/evolution.py`
  - 第20行: `self.max_retries = max_retries or 4` - 硬编码最大重试次数
  - 第21行: `self.max_pddl_retries = max_pddl_retries or 2` - 硬编码PDDL重试次数
  - 建议: 这些参数应该从配置读取

- **文件**: `algorithm/kernel.py`
  - 第48行: `def run(self, user_goal: str) -> bool:` 中的迭代逻辑有硬编码限制
  - 第50行: `for iteration in range(self.max_iterations):` - 最大迭代次数来自配置，但默认值硬编码

#### 2.3 超时值硬编码
- **文件**: `infrastructure/mcp_client.py`
  - 多处硬编码超时值（5秒、2秒等）:
    - 第123行: `timeout=5.0`
    - 第134行: `timeout=5.0`
    - 第142行: `timeout=5.0`
    - 第149行: `timeout=5.0`
    - 第253行: `timeout=5.0`
    - 第367行: `timeout=2.0`
    - 第425行: `timeout=3.0`
  - 建议: 超时值应该可配置

- **文件**: `infrastructure/planner/lama_planner.py`
  - 第12行: `def __init__(self, downward_path: str, temp_dir: str, timeout: int = 30):` - 硬编码默认超时30秒
  - 建议: 从配置读取

### 3. 字符串常量硬编码

#### 3.1 领域特定硬编码
- **文件**: `infrastructure/domain/file_management_expert.py`
  - 第11行: `return "file_management"` - 硬编码领域名称
  - 第20-28行: 硬编码规则字符串列表
  - 建议: 规则应该从外部文件加载

#### 3.2 日志/消息硬编码
- **文件**: `infrastructure/pddl/pddl_modifier.py`
  - 第47行: `"\n;; --- AI Generated Action ---\n"` - 硬编码注释
  - 建议: 注释模板可配置

- **文件**: 多个文件中的中文日志消息
  - 整个代码库中混合使用中文和英文日志消息
  - 建议: 统一日志消息格式，支持国际化

#### 3.3 技能名称硬编码
- **文件**: `infrastructure/mcp_skills/` 目录下的技能文件
  - 每个技能文件都硬编码了技能名称（如"compress"、"move"等）
  - 这是设计使然，但技能注册机制可能过于静态

### 4. 逻辑判断硬编码

#### 4.1 条件判断硬编码
- **文件**: `infrastructure/translator/pddl_translator.py`
  - 第34行: `def route_domain(self, user_goal: str) -> str:` 中的领域路由逻辑
  - 目前只返回"file_management"，硬编码了单一领域
  - 建议: 实现真正的多领域路由

- **文件**: `infrastructure/executor/action_executor.py`
  - 第38行: `self.execution_history.append(action_name.lower())` - 硬编码小写转换
  - 第96行: `if hasattr(module, 'GeneratedSkill'):` - 硬编码类名"GeneratedSkill"
  - 建议: 类名可配置

#### 4.2 错误处理硬编码
- **文件**: 多个文件中的错误消息字符串
  - 错误消息硬编码为中文或英文字符串
  - 建议: 定义错误代码和消息映射

### 5. 网络/API端点硬编码

#### 5.1 API端点硬编码
- **文件**: `config/settings.py`
  - 第77行: `"https://api.deepseek.com"` - 硬编码DeepSeek API端点
  - 建议: 完全通过环境变量配置

#### 5.2 MCP服务器配置硬编码
- **文件**: `infrastructure/mcp_client.py`
  - 第80行: `self.server_args = server_args or ["mcp_server_structured.py"]` - 硬编码服务器脚本
  - 建议: 从配置读取

### 6. 测试数据硬编码

#### 6.1 测试文件硬编码
- **文件**: `tests/domain.pddl` 和 `tests/problem.pddl`
  - 硬编码的测试PDDL文件内容
  - 这是测试数据，属于正常情况

#### 6.2 测试用例硬编码
- **文件**: `algorithm/regression.py`
  - 测试用例从文件加载，但测试文件路径硬编码
  - 建议: 测试路径可配置

## 影响分析

### 负面影响
1. **缺乏灵活性**: 硬编码值使得系统难以适应不同环境
2. **维护困难**: 需要修改代码来改变配置值
3. **部署复杂**: 在不同环境中部署需要代码修改
4. **测试困难**: 难以模拟不同配置场景

### 正面因素
1. **简单性**: 硬编码值使代码更简单直接
2. **性能**: 避免了配置读取的开销
3. **明确性**: 值在代码中明确可见

## 改进建议

### 高优先级改进
1. **将路径配置化**: 将所有文件路径和目录路径移到配置文件中
2. **外部化API配置**: 将API端点、密钥、模型等完全外部化
3. **参数化算法参数**: 将迭代次数、超时等参数移到配置

### 中优先级改进
1. **统一配置管理**: 使用统一的配置管理系统
2. **支持多领域**: 实现真正的多领域路由和配置
3. **国际化支持**: 将日志消息外部化

### 低优先级改进
1. **动态技能发现**: 实现技能的动态发现和注册
2. **插件化架构**: 支持插件化扩展

## 具体修改建议

### 1. 创建集中式配置常量文件
```python
# config/constants.py
class Constants:
    # 文件路径相关
    DOMAIN_FILE_NAME = "domain.pddl"
    PROBLEM_FILE_NAME = "problem.pddl"
    SANDBOX_STORAGE_DIR = "storage_jail"
    SANDBOX_SKILLS_DIR = "skills"
    
    # 算法参数
    DEFAULT_MAX_ITERATIONS = 5
    DEFAULT_MAX_EVOLUTION_RETRIES = 4
    DEFAULT_PLANNING_TIMEOUT = 30
    
    # MCP配置
    DEFAULT_MCP_SERVER_SCRIPT = "mcp_server_structured.py"
    
    # 超时配置
    MCP_CONNECTION_TIMEOUT = 5.0
    MCP_TOOL_CALL_TIMEOUT = 5.0
    MCP_DISCONNECT_TIMEOUT = 2.0
```

### 2. 增强Settings类
- 添加更多配置项
- 支持从多个来源加载配置（环境变量、配置文件、命令行参数）
- 提供配置验证和默认值

### 3. 重构硬编码的路径构建
```python
# 当前硬编码方式
src_domain = os.path.join(self.tests_path, "domain.pddl")

# 改进后
from config.constants import Constants
src_domain = os.path.join(self.tests_path, Constants.DOMAIN_FILE_NAME)
```

### 4. 实现配置驱动的领域专家
```python
class FileManagementExpert(IDomainExpert):
    def __init__(self, config: Settings):
        self.config = config
    
    @property
    def domain_name(self) -> str:
        return self.config.domain_name or "file_management"
    
    def get_domain_file(self) -> str:
        return self.config.domain_file_name or "domain.pddl"
```

## 结论

AIOS-PDDL架构中存在多处硬编码问题，主要集中在路径、配置值和字符串常量方面。这些问题降低了系统的灵活性和可维护性，但考虑到项目的当前阶段（研究原型），部分硬编码是合理的简化。

建议按照优先级逐步改进，首先解决影响部署和灵活性的高优先级问题，如外部化API配置和路径配置化。对于研究原型来说，保持代码简单性也很重要，因此需要平衡配置灵活性和代码复杂度。

## 发现统计

- 路径硬编码: 8处
- 配置值硬编码: 12处
- 字符串常量硬编码: 15+处
- 逻辑判断硬编码: 5处
- 超时值硬编码: 10+处
- 总计: 50+处硬编码问题

---
*报告生成时间: 2026-01-29*
*分析范围: algorithm/, app/, config/, infrastructure/, interface/, tests/ 目录*
*排除目录: SaveAIOS/, downward/ (按用户要求)*