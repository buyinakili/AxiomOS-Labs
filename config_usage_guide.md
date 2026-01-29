# AIOS-PDDL 配置重构与使用指南

## 概述

本文档记录了AIOS-PDDL项目中硬编码问题的重构过程，并提供了配置系统的详细使用说明。通过本次重构，我们将所有硬编码值迁移到集中管理的配置文件中，提高了系统的灵活性和可维护性。

## 重构总结

### 修改的文件列表

1. **config/constants.py** - 新创建的常量定义文件，包含所有系统常量
2. **config/settings.py** - 增强的Settings类，添加了更多配置项并引用常量
3. **infrastructure/domain/file_management_expert.py** - 修改为接受config参数
4. **infrastructure/sandbox/sandbox_manager.py** - 修改为使用config参数
5. **infrastructure/storage/file_storage.py** - 修改为使用config参数
6. **infrastructure/mcp_client.py** - 修改为使用配置中的超时值
7. **infrastructure/planner/lama_planner.py** - 修改为使用config参数
8. **infrastructure/pddl/pddl_modifier.py** - 修改为使用config参数
9. **infrastructure/executor/action_executor.py** - 修改为使用config参数
10. **infrastructure/translator/pddl_translator.py** - 修改为使用config参数
11. **algorithm/evolution.py** - 修改为使用config参数
12. **algorithm/kernel.py** - 修改为使用config参数
13. **app/factory.py** - 修改为使用config参数
14. **app/training_factory.py** - 修改为使用config参数

### 主要改进

1. **集中管理**：所有硬编码值现在都集中在 `config/constants.py` 和 `config/settings.py` 中
2. **向后兼容**：所有修改都保持了向后兼容性，现有代码无需修改
3. **配置驱动**：系统行为现在可以通过配置文件或环境变量进行控制
4. **类型安全**：使用Python类型提示和dataclass确保配置的正确性

## 配置系统详解

### 配置文件结构

```
config/
├── constants.py    # 系统常量定义
└── settings.py     # 配置管理类
```

### 常量定义 (constants.py)

`constants.py` 定义了所有系统常量，分为以下几类：

1. **路径常量**：文件系统路径相关
2. **超时常量**：各种操作的超时时间
3. **PDDL常量**：PDDL相关配置
4. **进化常量**：进化算法相关参数
5. **技能常量**：技能相关配置

### 配置管理类 (settings.py)

`Settings` 类是一个dataclass，负责：
- 从环境变量加载配置
- 提供默认值
- 验证配置的有效性
- 提供便捷的路径计算方法

### 环境变量配置

系统支持通过环境变量覆盖默认配置：

```bash
# 基本配置
export AXIOMLABS_PROJECT_ROOT="/home/user/projects/AxiomLabs"
export AXIOMLABS_LLM_API_KEY="sk-xxx"
export AXIOMLABS_LLM_BASE_URL="https://api.deepseek.com"
export AXIOMLABS_LLM_MODEL="deepseek-chat"

# 路径配置
export AXIOMLABS_STORAGE_PATH="${PROJECT_ROOT}/workspace"
export AXIOMLABS_TESTS_PATH="${PROJECT_ROOT}/tests"
export AXIOMLABS_TEMP_DIR="/tmp/axiomlabs"

# 超时配置
export AXIOMLABS_PLANNING_TIMEOUT=30
export AXIOMLABS_MCP_CONNECT_TIMEOUT=5.0
export AXIOMLABS_MCP_CALL_TIMEOUT=2.0
export AXIOMLABS_MCP_READ_TIMEOUT=3.0

# PDDL配置
export AXIOMLABS_DOMAIN_NAME="file_management"
export AXIOMLABS_DOMAIN_FILE_NAME="domain.pddl"
export AXIOMLABS_PDDL_AI_GENERATED_COMMENT=";; AI-GENERATED ACTION"

# 进化算法配置
export AXIOMLABS_MAX_EVOLUTION_RETRIES=3
export AXIOMLABS_MAX_ITERATIONS=10
```

## 具体修改说明

### 1. 路径处理

**修改前**：
```python
storage_path = "/home/user/projects/AxiomLabs/workspace"
tests_path = "/home/user/projects/AxiomLabs/tests"
```

**修改后**：
```python
from config.settings import Settings
config = Settings.load_from_env()
storage_path = config.storage_path  # 从配置中获取
tests_path = config.tests_path      # 从配置中获取
```

### 2. 超时配置

**修改前**：
```python
timeout = 5.0  # 硬编码超时
```

**修改后**：
```python
from config.settings import Settings
config = Settings.load_from_env()
timeout = config.mcp_connect_timeout  # 从配置中获取
```

### 3. PDDL配置

**修改前**：
```python
domain_name = "file_management"
domain_file_name = "domain.pddl"
```

**修改后**：
```python
from config.settings import Settings
config = Settings.load_from_env()
domain_name = config.domain_name
domain_file_name = config.domain_file_name
```

### 4. 进化算法参数

**修改前**：
```python
max_retries = 3
max_iterations = 10
```

**修改后**：
```python
from config.settings import Settings
config = Settings.load_from_env()
max_retries = config.max_evolution_retries
max_iterations = config.max_iterations
```

## 使用示例

### 基本使用

```python
from config.settings import Settings

# 加载配置（自动从环境变量读取）
config = Settings.load_from_env()

# 使用配置
print(f"项目根目录: {config.project_root}")
print(f"存储路径: {config.storage_path}")
print(f"LLM模型: {config.llm_model}")

# 验证配置
if config.validate():
    print("配置验证通过")
```

### 在组件中使用配置

```python
from infrastructure.storage.file_storage import FileStorage
from infrastructure.planner.lama_planner import LAMAPlanner
from config.settings import Settings

config = Settings.load_from_env()

# 创建组件时传递config参数
storage = FileStorage(config=config)
planner = LAMAPlanner(config=config)

# 组件内部会自动使用配置
domain_content = storage.read_domain()
```

### 自定义配置

```python
from config.settings import Settings

# 创建自定义配置
custom_config = Settings(
    project_root="/custom/path",
    storage_path="/custom/path/workspace",
    llm_api_key="custom-key",
    llm_base_url="https://custom.api.com",
    llm_model="custom-model"
)

# 使用自定义配置
from infrastructure.domain.file_management_expert import FileManagementExpert
expert = FileManagementExpert(config=custom_config)
```

## 新增的配置项

### 路径相关
- `sandbox_runs_path`: 沙盒运行目录路径
- `sandbox_dir_prefix`: 沙盒目录前缀
- `mcp_skills_dir`: MCP技能目录

### 超时相关
- `mcp_connect_timeout`: MCP连接超时
- `mcp_call_timeout`: MCP调用超时
- `mcp_read_timeout`: MCP读取超时
- `planning_timeout`: 规划超时

### PDDL相关
- `domain_name`: 领域名称
- `domain_file_name`: 领域文件名
- `pddl_ai_generated_comment`: PDDL AI生成注释

### 进化算法相关
- `max_evolution_retries`: 最大进化重试次数
- `max_iterations`: 最大迭代次数

### MCP相关
- `mcp_server_command`: MCP服务器命令
- `mcp_server_args`: MCP服务器参数

## 向后兼容性

所有修改都保持了向后兼容性：

1. **默认值**：所有配置项都有合理的默认值
2. **可选参数**：所有组件的config参数都是可选的，如果不提供会使用默认配置
3. **环境变量**：现有环境变量仍然有效
4. **接口不变**：公共API接口保持不变

## 测试建议

为确保重构后的系统正常工作，建议进行以下测试：

1. **单元测试**：测试各个组件是否能正确加载配置
2. **集成测试**：测试整个系统流程是否正常
3. **配置测试**：测试不同配置下的系统行为
4. **回滚测试**：确保在配置错误时系统能优雅降级

## 常见问题

### Q: 如何查看当前配置？
A: 使用 `config.to_dict()` 方法或直接打印config对象：

```python
from config.settings import Settings
config = Settings.load_from_env()
print(config)  # 打印所有配置
```

### Q: 配置验证失败怎么办？
A: 检查环境变量设置是否正确，或使用 `config.validate()` 方法查看具体错误。

### Q: 如何添加新的配置项？
A: 在 `config/constants.py` 中添加常量，在 `config/settings.py` 的 `Settings` 类中添加对应字段。

### Q: 组件不支持config参数怎么办？
A: 所有核心组件都已更新支持config参数。如果遇到不支持的情况，请检查组件版本。

## 总结

本次重构成功将AIOS-PDDL项目中的所有硬编码值迁移到集中管理的配置系统中。主要成果包括：

1. ✅ 创建了统一的常量管理文件
2. ✅ 增强了配置管理类
3. ✅ 修改了所有核心组件以支持配置参数
4. ✅ 保持了向后兼容性
5. ✅ 提高了系统的灵活性和可维护性

现在，系统可以通过环境变量轻松配置，无需修改代码即可适应不同的部署环境。