# AIOS-PDDL with evolution and auditing
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
（这里贴上b站分享链接）
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

3.执行过程中会报规划受阻，这时候就要用到沙盒模式
```
python3 auto_trainer.py 
```
看看沙盒模式能学到什么新技能吧
## 🤝 贡献与参与(Contribute and participate)
我欢迎对AIOS-PDDL架构感兴趣的大佬加入！
提交 Issue 报告 Bug
提交 Pull Request 改进进化算法
Star 这个仓库支持我的探索

##🗺️ 项目路线图 (Roadmap)
[x] Phase 1: 基于 PDDL 的静态文件管理内核

[x] Phase 2: 物理沙盒环境与手动进化训练循环（现阶段）

[ ] Phase 3: 内核实时异常检测 ，当 Planner报告规划受阻时，实时挂起任务并自动触发进化进程（开发中）。

[ ] Phase 4: 架构总体重构，降低耦合与提高可拓展性

[ ] Phase 5: 开放LLM自检，检查现有功能并优化，并保证通过回归测试

[ ] Phase 6: 探索新的领域（不只是文件操作），同时在这个过程中优化prompt

[ ] Phase 7: 多领域协同合作、进化，目标解决多领域问题

[ ] Phase 8：尝试实现自我学习新领域，自己写prompt

[ ] Phase 9：...
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
