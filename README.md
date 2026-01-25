# AIOS-PDDL with evolution and auditing

## 📢 版本更新 v0.4.0

**更新内容**：
- 对架构进行了一次大的重构，降低了绝大部分耦合的内容与硬编码等内容并提高了可拓展性
- 添加了可以指定沙盒模式学习任务的功能（`--task` 参数）
- 修复了沙盒模式中domain读取问题
- **已知问题**：沙盒模式学习出的能力可能在运行模式失败（明天会修复）

## � V2.0 重构计划：迈向 Neuro-Symbolic 逻辑对齐 (In Progress)

经过一阶段的探索，我决定对本项目进行底层架构级的重构，将重心从"简单的 LLM 任务执行"转向"基于符号规划的高纯度逻辑数据合成"。

### 核心架构：三层验证工厂 (Triple-Layer Validation Factory)
1. **语义解析层 (JSON-State Extractor)**：
   - 放弃让 LLM 直接输出不稳定的 PDDL 语法。
   - 引导 LLM 输出结构化的 JSON 任务描述，通过代码模板拼装成标准的 PDDL Problem，彻底消除语法幻觉。
   
2. **符号规划层 (PDDL & Fast Downward)**：
   - 使用工业级规划器 **Fast Downward** 代替 LAMA。
   - 定义 9 个核心原子动作（create, move, compress, setPerm 等），覆盖文件运维领域 90% 以上的长程逻辑链。

3. **物理追踪层 (Predicate Tracker)**：
   - **核心创新**：每一动作执行后，实时在沙盒中进行 Bash 物理断言。
   - 只有逻辑规划（Planner）与物理世界（Sandbox）状态强一致时，才会被记录为有效的思维链（CoT）数据。

> **目标**：产出 100% 物理对齐、无逻辑断层的Agent 执行轨迹，为训练更强逻辑的小模型提供数据。

以下是之前的readme，我会在跑出第一批数据之后整体更新：
我的架构是一个探索性的AI操作系统内核，它融合了大语言模型 (LLM)的推理能力与符号规划(PDDL)的严谨性。

不仅能执行现有功能支持的任务，也能在沙盒训练后习得新的功能，从而完成更多任务
## 🌟 核心亮点 (Core Features)
### 🤖 符号规划驱动的执行引擎(Symbolic programming-driven execution engine)
不同于传统的 Agent 盲目尝试，AIOS 使用 LAMA Planner 在状态空间中寻找最优解，将非确定性的LLM 推理约束在确定性的符号逻辑空间中，确保每一步操作都有逻辑支撑，极大地减少了 Token 消耗和无效尝试。

### 🧬 演化增强机制 (Evolutionary Learning Phase) AIOS 采用“先学习、后部署”的策略：
离线演化 (Offline Evolution)：在专门的沙盒模式下，针对复杂任务进行“进化训练”。系统会通过不断尝试，自动生成 PDDL 逻辑补丁与 Python 技能脚本。

技能持久化 (Skill Persistence)：学习成功的技能将通过审计，正式注入内核技能库，供生产模式下的 PDDL Planner 直接调用。

### 🛡️ 物理沙盒与审计系统(Physical sandbox and audit system)
内置严格的 ExecutionAuditor，确保 LLM 生成的技能在注入前通过语法和逻辑双重验证，防止虚假进化（False Evolution）并保护宿主系统安全。

💡 想了解本项目与 MCP 或其他 Agent 架构的本质区别？请移步 FAQ.md 查看深度对线记录。
## 🏗️ 架构设计 (Architecture)
![3C1E0CCB4EAD607926BD901063CABD0A](https://github.com/user-attachments/assets/195e37c3-864a-43e2-9aa8-592457b6a9f7)
这张图是我架构目前的流程示意图
### 文件结构图 (Project Structure)
AIOS/

├── modules/          # 核心逻辑与技能库

├── tests/            # PDDL 领域与问题定义

├── storage/          # 模拟物理文件系统

├── auto_trainer.py   # 演化/沙盒模式入口

└── main_demo.py      # 内核运行入口

## 📺 演示视频 (Demo)
【一个融合了LLM与PDDL规划的沙盒审计自演进智能体AIOS架构】

https://www.bilibili.com/video/BV1RMzuBjEym/?share_source=copy_web&vd_source=a2c7eebd10946ecc96e9cc3ad330438d

这支视频演示了该架构从只有简单功能到运行一次沙盒模式后学会了两个新功能并测试通过的全流程

并且还有对于如上架构图的详细解析

## 快速开始 (Quick Start)
1. 环境配置

LAMA基于Linux，我是用的wsl，请按需配置
```
git clone https://github.com/buyinakili/AIOS-PDDL-with-evolution-and-auditing.git
cd AIOS
# 确保已安装 Fast-Downward 规划器
export DOWNWARD_PATH=/your/path/to/fast-downward.py
```
在AIOS目录下新建文件.env，配置你的deepseekKey（目前只适配了deepseek）
```
DEEPSEEK_API_KEY=你的deepseekKey
# 本地 Fast Downward 的路径，示例如下（这是我的）
DOWNWARD_PATH=/home/nakili/projects/AIOS/downward/fast-downward.py
```
2. 启动演示
尝试一个已经可以解决的文件操作任务
```
python3 main_demo.py --goal "将root下的txt文件移动到backup文件夹下"
```
**或者**

尝试一个目前无法解决的文件操作任务
```
python3 main_demo.py --goal "将root下的txt文件重命名为AIOS.txt"
```

3. 沙盒模式学习
**自动模式**（LLM自动出题，默认学习3次）：
```
python3 app/auto_trainer.py
```

**指定任务模式**（学习特定任务）：
```
python3 app/auto_trainer.py --task "重命名文件" --rounds 5
```

**参数说明**：
- `--auto` 或 `-a`：自动模式（默认）
- `--task "任务描述"` 或 `-t "任务描述"`：指定要学习的任务
- `--rounds 数字` 或 `-r 数字`：学习轮次/重试次数

看看沙盒模式能学到什么新技能吧
## 🤝 贡献与参与(Contribute and participate)
我欢迎对AIOS-PDDL架构感兴趣的大佬加入！
提交 Issue 报告 Bug
提交 Pull Request 改进进化算法
Star 这个仓库支持我的探索

##🗺️ 项目路线图 (Roadmap)
[x] Phase 1: 基于 PDDL 的静态文件管理内核

[x] Phase 2: 物理沙盒环境与手动进化训练循环（现阶段）

[ ] Phase 3: 架构总体重构，更改为逻辑数据生成器（正在做）

后面是之前的计划

[ ] Phase 4: 开放LLM自检，检查现有功能并优化，并保证通过回归测试

[ ] Phase 5: 探索新的领域（不只是文件操作），同时在这个过程中优化prompt

[ ] Phase 6: 多领域协同合作、进化，目标解决多领域问题

[ ] Phase 7：尝试实现自我学习新领域，自己写prompt

[ ] Phase 8：...
## 我的一些话
我是一个大三人工智能专业在读本科生，
我在包括三天半的数学建模比赛的共计十天中
从零与AI协作写出了该架构。

本来我是在写一个助手agent项目，其实就是兴趣爱好。

写了三天之后，我发现现在的LLM有很多不足之处，最大的问题就是

**无论怎么优化，这都是个概率模型**。

LLM输出的任何结果都是基于概率的。

于是我为了我的助手agent去找有没有别的模型可以解决这个问题

找到了SSM、RAG等等，但是这些模型也有自身或多或少的问题，无法实现我的需求

我认识到现在的时代需要一个**类似操作系统的AIOS**

我一开始不知道这个名字，我将其命名为元系统

这个系统调配agent的种种功能，负责agent的自我认知，自我学习等

我为我的想法感到雀跃，我以为我是第一个想到的

然后我就去找有没有相关论文，关注有没有跟我相同的想法

过了两天，我看到MIT发布了RLMs，我惊恐地认为别人不仅想到了，还已经实现了

仔细看了论文才知道，不是这么回事，这才稍稍安定

我意识到我或许永远无法知道世界上的人有没有想到，想法是否和我完全一致

于是我决定自己做一个，即使有人和我撞想法，我从零实现的架构也一定会有独属于我的创新

十天之后的前天，我的修好了一些让架构成功率不高的最后几个bug

昨天剪了我自媒体游戏攻略的视频，今天终于把发布架构的演示视频做完了

我会持续迭代我的架构，即使无人在意

我相信技术的积累总会改变我个人的价值

Author: [Nakili] License: MIT
