# AxiomOS Labs v0.4.2
## 一项致力于通过神经符号与沙盒审计自演进重构通用智能底层逻辑的前沿探索

## 重构计划：CoA数据生成器
经过一阶段的探索，本项目决定了接下来的方向，即CoA数据生成器

生成出的CoA数据会完开源供社区使用，敬请期待

## 目前的核心架构

### 三层验证工厂
1. **语义解析层**：将自然语言目标翻译为PDDL问题描述，确保意图准确映射。
2. **符号规划层**：基于Fast‑Downward规划器生成可执行的行动序列，保证逻辑一致性。
3. **物理追踪层**：通过MCP或本地技能执行动作，实时更新环境状态并验证物理对齐。

### 模块化设计
- **接口层** (`interface/`)：定义抽象接口，隔离业务逻辑与具体实现。
- **基础设施层** (`infrastructure/`)：提供PDDL规划器、MCP客户端、技能执行器等具体实现。
- **算法层** (`algorithm/`)：封装进化算法、内核调度等核心业务逻辑。
- **应用层** (`app/`)：提供生产模式入口与自动化训练工具。

## 预计 v0.6.0 主要目标
1. **物理对齐**：确保PDDL规划结果与真实世界执行效果完全一致。
2. **数据生成**：产出高质量、可复现的Agent执行轨迹，用于模型训练。
3. **优化算法**：优化算法，使架构可以处理更复杂的问题

## 快速开始

### 环境准备
```bash
# 克隆仓库
git clone https://github.com/buyinakili/AxiomOS-Labs
cd AxiomOS

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制示例文件并填写实际值）
cp .env.example .env
# 编辑 .env，设置 DEEPSEEK_API_KEY、DOWNWARD_PATH 等
```

### 运行示例任务
```bash
# 使用MCP模式（默认）
python3 app/main_demo.py "将root下的txt文件重命名为new.txt"

# 使用本地技能模式
export USE_MCP=false
python3 app/main_demo.py
```

### 运行自动化训练
```bash
python3 app/auto_trainer.py

#指定自动化训练任务与轮次
python3 app/auto_trainer.py --task "在backup目录下新建new_folder文件夹" --rounds 3
```

---

## 🤝 贡献与参与(Contribute and participate)
本项目欢迎对志同道合的伙伴加入！
提交 Issue 报告 Bug
提交 Pull Request 改进进化算法
Star 这个仓库支持项目探索

## 🗺️ 项目路线 (Roadmap)
短期：
1. 优化llm翻译任务为problem的逻辑
2. 重构架构为数据生成器
3. 更换LAMA为更优符号规划器
中期：
1. 使用生成的CoA数据运用强化学习调优模型
2. 拓展其他领域
后期：
1. 使用虚拟机优化沙盒
2. 引入prompt的自学习
3. 创造新的符号领域规划语言（可能）

## 📺 v0.3.1演示视频 (Demo)
【一个融合了LLM与PDDL规划的沙盒审计自演进智能体AIOS架构】

https://www.bilibili.com/video/BV1RMzuBjEym/?share_source=copy_web&vd_source=a2c7eebd10946ecc96e9cc3ad330438d

这支视频演示了本项目v0.3.1版本时从只有简单功能到运行一次沙盒模式后学会了两个新功能并测试通过的全流程

## 🏗️ 架构设计 (Architecture)
![3C1E0CCB4EAD607926BD901063CABD0A](https://github.com/user-attachments/assets/195e37c3-864a-43e2-9aa8-592457b6a9f7)
图为v0.3.1流程示意图

## Author: [Nakili] License: MIT

## 维护者

AxiomOS Labs 开发团队  
*最后更新：2026年1月*
