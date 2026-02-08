"""CoT数据格式Schema定义

基于SchemaFirst.json设计，定义Chain-of-Thought数据生成器的输出格式。
遵循数据纯净原则：不包含最终执行状态、版本等元数据。
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import uuid
import json
from datetime import datetime


@dataclass
class BrainStep:
    """Brain层的一个步骤记录"""
    env: str  # 环境事实字符串
    chain_of_task: List[str]  # 任务链
    change_reason: Optional[str] = None  # 变更原因（仅当任务链变更时）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "Env": self.env,
            "ChainOfTask": self.chain_of_task
        }
        if self.change_reason:
            result["ChangeReason"] = self.change_reason
        return result


@dataclass
class NervesStep:
    """Nerves层的一个步骤记录"""
    task: str  # 任务名称
    env: str  # 环境事实字符串
    chain_of_action: List[str]  # 动作链
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "Task": self.task,
            "Env": self.env,
            "ChainOfAction": self.chain_of_action
        }


@dataclass
class BrainError:
    """Brain层错误记录"""
    env: str  # 发生错误时的环境事实
    chain_of_task: List[str]  # 发生错误时的任务链
    error_message: str  # 错误信息（经AnalysisLLM分析后）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "Env": self.env,
            "ChainOfTask": self.chain_of_task,
            "ErrorMessage": self.error_message
        }


@dataclass
class NervesError:
    """Nerves层错误记录"""
    task: str  # 发生错误的任务
    env: str  # 发生错误时的环境事实
    chain_of_action: List[str]  # 发生错误时的动作链
    error_message: str  # 错误信息（经AnalysisLLM分析后）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "Task": self.task,
            "Env": self.env,
            "ChainOfAction": self.chain_of_action,
            "ErrorMessage": self.error_message
        }


@dataclass
class CoTDataPoint:
    """单个CoT数据点
    
    设计原则：
    1. Brain/Nerves只存储正确步骤，错误步骤放在Error中
    2. 数据纯净：不包含最终执行状态、版本等元数据
    3. 训练数据切分：
       - Brain正确步骤 → 喂给BrainLLM训练
       - Nerves正确步骤 → 喂给NervesLLM训练
       - Error步骤 → 喂给AnalysisLLM训练
    """
    mission_id: str  # 任务ID (UUID格式)
    mission: str  # 原始用户任务描述
    domain: str  # 领域名称
    brain_steps: List[BrainStep] = field(default_factory=list)  # Brain层正确步骤
    nerves_steps: List[NervesStep] = field(default_factory=list)  # Nerves层正确步骤
    brain_errors: List[BrainError] = field(default_factory=list)  # Brain层错误记录
    nerves_errors: List[NervesError] = field(default_factory=list)  # Nerves层错误记录
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保mission_id是字符串格式
        if not isinstance(self.mission_id, str):
            self.mission_id = str(self.mission_id)
    
    @classmethod
    def create_new(cls, mission: str, domain: str = "file-manager-extended") -> "CoTDataPoint":
        """创建新的数据点"""
        return cls(
            mission_id=str(uuid.uuid4()),
            mission=mission,
            domain=domain
        )
    
    def add_brain_step(self, env: str, chain_of_task: List[str], change_reason: Optional[str] = None):
        """添加Brain层正确步骤"""
        self.brain_steps.append(BrainStep(
            env=env,
            chain_of_task=chain_of_task,
            change_reason=change_reason
        ))
    
    def add_nerves_step(self, task: str, env: str, chain_of_action: List[str]):
        """添加Nerves层正确步骤"""
        self.nerves_steps.append(NervesStep(
            task=task,
            env=env,
            chain_of_action=chain_of_action
        ))
    
    def add_brain_error(self, env: str, chain_of_task: List[str], error_message: str):
        """添加Brain层错误记录"""
        self.brain_errors.append(BrainError(
            env=env,
            chain_of_task=chain_of_task,
            error_message=error_message
        ))
    
    def add_nerves_error(self, task: str, env: str, chain_of_action: List[str], error_message: str):
        """添加Nerves层错误记录"""
        self.nerves_errors.append(NervesError(
            task=task,
            env=env,
            chain_of_action=chain_of_action,
            error_message=error_message
        ))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（符合SchemaFirst.json结构）"""
        return {
            "mission_id": self.mission_id,
            "mission": self.mission,
            "domain": self.domain,
            "Brain": [step.to_dict() for step in self.brain_steps],
            "Nerves": [step.to_dict() for step in self.nerves_steps],
            "BrainError": [error.to_dict() for error in self.brain_errors],
            "NervesError": [error.to_dict() for error in self.nerves_errors]
        }
    
    def to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii)
    
    def save_to_file(self, filepath: str):
        """保存到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "CoTDataPoint":
        """从JSON文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 转换数据
        brain_steps = [
            BrainStep(
                env=step.get("Env", ""),
                chain_of_task=step.get("ChainOfTask", []),
                change_reason=step.get("ChangeReason")
            )
            for step in data.get("Brain", [])
        ]
        
        nerves_steps = [
            NervesStep(
                task=step.get("Task", ""),
                env=step.get("Env", ""),
                chain_of_action=step.get("ChainOfAction", [])
            )
            for step in data.get("Nerves", [])
        ]
        
        brain_errors = [
            BrainError(
                env=error.get("Env", ""),
                chain_of_task=error.get("ChainOfTask", []),
                error_message=error.get("ErrorMessage", "")
            )
            for error in data.get("BrainError", [])
        ]
        
        nerves_errors = [
            NervesError(
                task=error.get("Task", ""),
                env=error.get("Env", ""),
                chain_of_action=error.get("ChainOfAction", []),
                error_message=error.get("ErrorMessage", "")
            )
            for error in data.get("NervesError", [])
        ]
        
        return cls(
            mission_id=data.get("mission_id", str(uuid.uuid4())),
            mission=data.get("mission", ""),
            domain=data.get("domain", "file-manager-extended"),
            brain_steps=brain_steps,
            nerves_steps=nerves_steps,
            brain_errors=brain_errors,
            nerves_errors=nerves_errors
        )
    
    def get_training_data(self) -> Dict[str, Any]:
        """获取训练数据切分
        
        返回：
            brain_data: BrainLLM训练数据（正确步骤）
            nerves_data: NervesLLM训练数据（正确步骤）
            analysis_data: AnalysisLLM训练数据（错误步骤）
        """
        return {
            "brain_data": {
                "mission": self.mission,
                "domain": self.domain,
                "steps": [
                    {
                        "env": step.env,
                        "chain_of_task": step.chain_of_task,
                        "change_reason": step.change_reason
                    }
                    for step in self.brain_steps
                ]
            },
            "nerves_data": {
                "mission": self.mission,
                "domain": self.domain,
                "steps": [
                    {
                        "task": step.task,
                        "env": step.env,
                        "chain_of_action": step.chain_of_action
                    }
                    for step in self.nerves_steps
                ]
            },
            "analysis_data": {
                "brain_errors": [
                    {
                        "env": error.env,
                        "chain_of_task": error.chain_of_task,
                        "error_message": error.error_message
                    }
                    for error in self.brain_errors
                ],
                "nerves_errors": [
                    {
                        "task": error.task,
                        "env": error.env,
                        "chain_of_action": error.chain_of_action,
                        "error_message": error.error_message
                    }
                    for error in self.nerves_errors
                ]
            }
        }


# 工具函数
def validate_cot_data(data: Dict[str, Any]) -> bool:
    """验证CoT数据格式是否符合SchemaFirst规范"""
    required_fields = ["mission_id", "mission", "domain", "Brain", "Nerves", "BrainError", "NervesError"]
    
    # 检查必需字段
    for field in required_fields:
        if field not in data:
            return False
    
    # 检查字段类型
    if not isinstance(data["mission_id"], str):
        return False
    if not isinstance(data["mission"], str):
        return False
    if not isinstance(data["domain"], str):
        return False
    if not isinstance(data["Brain"], list):
        return False
    if not isinstance(data["Nerves"], list):
        return False
    if not isinstance(data["BrainError"], list):
        return False
    if not isinstance(data["NervesError"], list):
        return False
    
    return True


def create_example_data() -> CoTDataPoint:
    """创建示例数据点"""
    data_point = CoTDataPoint.create_new(
        mission="扫描workspace文件夹，然后创建一个backup文件夹",
        domain="file-manager-extended"
    )
    
    # 添加Brain层步骤
    data_point.add_brain_step(
        env="(at file1 workspace) (at file2 workspace)",
        chain_of_task=["(scan workspace)", "(create_folder backup)"]
    )
    
    # 添加Nerves层步骤
    data_point.add_nerves_step(
        task="(scan workspace)",
        env="(at file1 workspace) (at file2 workspace)",
        chain_of_action=["(scan workspace)"]
    )
    
    data_point.add_nerves_step(
        task="(create_folder backup)",
        env="(scanned workspace) (at file1 workspace) (at file2 workspace)",
        chain_of_action=["(create_folder backup)"]
    )
    
    return data_point


if __name__ == "__main__":
    # 测试代码
    example = create_example_data()
    print("示例数据点:")
    print(example.to_json())
    
    # 测试训练数据切分
    training_data = example.get_training_data()
    print("\n训练数据切分:")
    print(f"Brain数据: {len(training_data['brain_data']['steps'])} 个步骤")
    print(f"Nerves数据: {len(training_data['nerves_data']['steps'])} 个步骤")
    print(f"Analysis数据: {len(training_data['analysis_data']['brain_errors'])} 个Brain错误, "
          f"{len(training_data['analysis_data']['nerves_errors'])} 个Nerves错误")