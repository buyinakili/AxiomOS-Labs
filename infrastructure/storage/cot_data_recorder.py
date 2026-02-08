"""CoT数据记录器

负责在CoTDataGenerator执行过程中记录数据，生成符合SchemaFirst格式的数据点。
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod

from config.data_schema import CoTDataPoint, BrainStep, NervesStep, BrainError, NervesError


class IDataRecorder(ABC):
    """数据记录器接口"""
    
    @abstractmethod
    def start_new_recording(self, mission: str, domain: str) -> str:
        """开始新的数据记录"""
        pass
    
    @abstractmethod
    def record_brain_success(self, env: str, chain_of_task: List[str], change_reason: Optional[str] = None):
        """记录Brain层成功步骤"""
        pass
    
    @abstractmethod
    def record_nerves_success(self, task: str, env: str, chain_of_action: List[str]):
        """记录Nerves层成功步骤"""
        pass
    
    @abstractmethod
    def record_brain_error(self, env: str, chain_of_task: List[str], error_message: str):
        """记录Brain层错误"""
        pass
    
    @abstractmethod
    def record_nerves_error(self, task: str, env: str, chain_of_action: List[str], error_message: str):
        """记录Nerves层错误"""
        pass
    
    @abstractmethod
    def save_and_reset(self, filename: Optional[str] = None) -> str:
        """保存当前数据并重置记录器"""
        pass


class CoTDataRecorder(IDataRecorder):
    """CoT数据记录器实现
    
    设计原则：
    1. 实时记录执行过程中的正确步骤和错误
    2. 生成符合SchemaFirst.json格式的数据
    3. 支持数据验证和导出
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化数据记录器
        
        :param output_dir: 输出目录，如果为None则使用默认目录
        """
        self.output_dir = output_dir or self._get_default_output_dir()
        self.current_data_point: Optional[CoTDataPoint] = None
        self._ensure_output_dir()
    
    def _get_default_output_dir(self) -> str:
        """获取默认输出目录（避免使用workspace目录）"""
        # 使用项目根目录下的cot_data目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        cot_data_dir = os.path.join(project_root, "cot_data")
        os.makedirs(cot_data_dir, exist_ok=True)
        return cot_data_dir
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def start_new_recording(self, mission: str, domain: str = "file-manager-extended") -> str:
        """
        开始新的数据记录
        
        :param mission: 用户任务描述
        :param domain: 领域名称
        :return: 任务ID
        """
        self.current_data_point = CoTDataPoint.create_new(mission, domain)
        return self.current_data_point.mission_id
    
    def record_brain_success(
        self, 
        env: str, 
        chain_of_task: List[str], 
        change_reason: Optional[str] = None
    ):
        """
        记录Brain层成功步骤
        
        :param env: 环境事实字符串
        :param chain_of_task: 任务链
        :param change_reason: 变更原因（仅当任务链变更时）
        """
        if self.current_data_point is None:
            raise ValueError("必须先调用start_new_recording开始记录")
        
        self.current_data_point.add_brain_step(env, chain_of_task, change_reason)
    
    def record_nerves_success(
        self, 
        task: str, 
        env: str, 
        chain_of_action: List[str]
    ):
        """
        记录Nerves层成功步骤
        
        :param task: 任务名称
        :param env: 环境事实字符串
        :param chain_of_action: 动作链
        """
        if self.current_data_point is None:
            raise ValueError("必须先调用start_new_recording开始记录")
        
        self.current_data_point.add_nerves_step(task, env, chain_of_action)
    
    def record_brain_error(
        self, 
        env: str, 
        chain_of_task: List[str], 
        error_message: str
    ):
        """
        记录Brain层错误（经AnalysisLLM分析后）
        
        :param env: 发生错误时的环境事实
        :param chain_of_task: 发生错误时的任务链
        :param error_message: 错误信息（经AnalysisLLM分析后）
        """
        if self.current_data_point is None:
            raise ValueError("必须先调用start_new_recording开始记录")
        
        self.current_data_point.add_brain_error(env, chain_of_task, error_message)
    
    def record_nerves_error(
        self, 
        task: str, 
        env: str, 
        chain_of_action: List[str], 
        error_message: str
    ):
        """
        记录Nerves层错误（经AnalysisLLM分析后）
        
        :param task: 发生错误的任务
        :param env: 发生错误时的环境事实
        :param chain_of_action: 发生错误时的动作链
        :param error_message: 错误信息（经AnalysisLLM分析后）
        """
        if self.current_data_point is None:
            raise ValueError("必须先调用start_new_recording开始记录")
        
        self.current_data_point.add_nerves_error(task, env, chain_of_action, error_message)
    
    def get_current_data(self) -> Optional[CoTDataPoint]:
        """获取当前记录的数据点"""
        return self.current_data_point
    
    def save_current_data(self, filename: Optional[str] = None) -> str:
        """
        保存当前记录的数据
        
        :param filename: 文件名，如果为None则自动生成
        :return: 保存的文件路径
        """
        if self.current_data_point is None:
            raise ValueError("没有数据可保存")
        
        if filename is None:
            # 自动生成文件名：mission_id + 时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mission_id_short = self.current_data_point.mission_id[:8]
            filename = f"cot_{mission_id_short}_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        self.current_data_point.save_to_file(filepath)
        return filepath
    
    def save_and_reset(self, filename: Optional[str] = None) -> str:
        """
        保存当前数据并重置记录器
        
        :param filename: 文件名
        :return: 保存的文件路径
        """
        filepath = self.save_current_data(filename)
        self.current_data_point = None
        return filepath
    
    def export_training_data(self, output_dir: Optional[str] = None) -> Dict[str, List[str]]:
        """
        导出训练数据（按LLM类型切分）
        
        :param output_dir: 输出目录，如果为None则使用当前输出目录的子目录
        :return: 导出的文件路径字典
        """
        if self.current_data_point is None:
            raise ValueError("没有数据可导出")
        
        # 确定输出目录
        if output_dir is None:
            output_dir = os.path.join(self.output_dir, "training_data")
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取训练数据切分
        training_data = self.current_data_point.get_training_data()
        mission_id = self.current_data_point.mission_id[:8]
        
        # 导出BrainLLM训练数据
        brain_filepath = os.path.join(output_dir, f"brain_{mission_id}.json")
        with open(brain_filepath, 'w', encoding='utf-8') as f:
            json.dump(training_data["brain_data"], f, indent=2, ensure_ascii=False)
        
        # 导出NervesLLM训练数据
        nerves_filepath = os.path.join(output_dir, f"nerves_{mission_id}.json")
        with open(nerves_filepath, 'w', encoding='utf-8') as f:
            json.dump(training_data["nerves_data"], f, indent=2, ensure_ascii=False)
        
        # 导出AnalysisLLM训练数据
        analysis_filepath = os.path.join(output_dir, f"analysis_{mission_id}.json")
        with open(analysis_filepath, 'w', encoding='utf-8') as f:
            json.dump(training_data["analysis_data"], f, indent=2, ensure_ascii=False)
        
        return {
            "brain": brain_filepath,
            "nerves": nerves_filepath,
            "analysis": analysis_filepath
        }
    
    def validate_current_data(self) -> bool:
        """验证当前数据格式"""
        if self.current_data_point is None:
            return False
        
        # 使用数据点的to_dict方法获取字典格式
        data_dict = self.current_data_point.to_dict()
        
        # 基本验证
        required_fields = ["mission_id", "mission", "domain", "Brain", "Nerves", "BrainError", "NervesError"]
        for field in required_fields:
            if field not in data_dict:
                return False
        
        # 类型验证
        if not isinstance(data_dict["mission_id"], str):
            return False
        if not isinstance(data_dict["mission"], str):
            return False
        if not isinstance(data_dict["domain"], str):
            return False
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取当前数据的统计信息"""
        if self.current_data_point is None:
            return {}
        
        return {
            "mission": self.current_data_point.mission,
            "mission_id": self.current_data_point.mission_id,
            "brain_steps": len(self.current_data_point.brain_steps),
            "nerves_steps": len(self.current_data_point.nerves_steps),
            "brain_errors": len(self.current_data_point.brain_errors),
            "nerves_errors": len(self.current_data_point.nerves_errors),
            "total_steps": len(self.current_data_point.brain_steps) + len(self.current_data_point.nerves_steps),
            "total_errors": len(self.current_data_point.brain_errors) + len(self.current_data_point.nerves_errors)
        }


class BatchCoTDataRecorder:
    """批量CoT数据记录器
    
    用于批量处理多个任务的数据记录
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化批量记录器
        
        :param output_dir: 输出目录
        """
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "cot_data",
            "batch"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.recorders: Dict[str, CoTDataRecorder] = {}
        self.completed_tasks: List[Dict[str, Any]] = []
    
    def start_task(self, task_id: str, mission: str, domain: str = "file-manager-extended") -> CoTDataRecorder:
        """
        开始一个新任务的数据记录
        
        :param task_id: 任务ID
        :param mission: 用户任务描述
        :param domain: 领域名称
        :return: 数据记录器实例
        """
        recorder = CoTDataRecorder(os.path.join(self.output_dir, task_id))
        recorder.start_new_recording(mission, domain)
        self.recorders[task_id] = recorder
        return recorder
    
    def complete_task(self, task_id: str, filename: Optional[str] = None) -> str:
        """
        完成任务并保存数据
        
        :param task_id: 任务ID
        :param filename: 文件名
        :return: 保存的文件路径
        """
        if task_id not in self.recorders:
            raise ValueError(f"任务 {task_id} 不存在")
        
        recorder = self.recorders[task_id]
        
        # 在保存和重置之前收集统计信息
        stats = recorder.get_statistics()
        filepath = recorder.save_and_reset(filename)
        
        # 记录完成的任务
        self.completed_tasks.append({
            "task_id": task_id,
            "mission": stats.get("mission", ""),
            "filepath": filepath,
            "statistics": stats
        })
        
        # 从活跃记录器中移除
        del self.recorders[task_id]
        
        return filepath
    
    def get_task_recorder(self, task_id: str) -> Optional[CoTDataRecorder]:
        """获取任务的数据记录器"""
        return self.recorders.get(task_id)
    
    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """获取已完成的任务列表"""
        return self.completed_tasks
    
    def get_summary(self) -> Dict[str, Any]:
        """获取批量处理的摘要信息"""
        total_tasks = len(self.completed_tasks) + len(self.recorders)
        completed_count = len(self.completed_tasks)
        active_count = len(self.recorders)
        
        # 统计总步骤和错误
        total_steps = 0
        total_errors = 0
        
        for task in self.completed_tasks:
            stats = task.get("statistics", {})
            total_steps += stats.get("total_steps", 0)
            total_errors += stats.get("total_errors", 0)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "active_tasks": active_count,
            "total_steps": total_steps,
            "total_errors": total_errors,
            "success_rate": (total_steps / (total_steps + total_errors)) * 100 if (total_steps + total_errors) > 0 else 100
        }
    
    def export_all_training_data(self, output_dir: Optional[str] = None) -> Dict[str, List[str]]:
        """
        导出所有已完成任务的训练数据
        
        :param output_dir: 输出目录
        :return: 导出的文件路径字典
        """
        if output_dir is None:
            output_dir = os.path.join(self.output_dir, "all_training_data")
        os.makedirs(output_dir, exist_ok=True)
        
        brain_files = []
        nerves_files = []
        analysis_files = []
        
        for task in self.completed_tasks:
            filepath = task["filepath"]
            try:
                # 加载数据点
                data_point = CoTDataPoint.load_from_file(filepath)
                
                # 创建临时记录器来导出训练数据
                temp_recorder = CoTDataRecorder()
                temp_recorder.current_data_point = data_point
                
                # 导出训练数据
                exported = temp_recorder.export_training_data(output_dir)
                
                brain_files.append(exported["brain"])
                nerves_files.append(exported["nerves"])
                analysis_files.append(exported["analysis"])
                
            except Exception as e:
                print(f"导出任务 {task['task_id']} 的训练数据时出错: {e}")
        
        return {
            "brain_files": brain_files,
            "nerves_files": nerves_files,
            "analysis_files": analysis_files
        }


# 工具函数
def create_cot_data_recorder(output_dir: Optional[str] = None) -> CoTDataRecorder:
    """创建CoT数据记录器工厂函数"""
    return CoTDataRecorder(output_dir)


def create_batch_cot_data_recorder(output_dir: Optional[str] = None) -> BatchCoTDataRecorder:
    """创建批量CoT数据记录器工厂函数"""
    return BatchCoTDataRecorder(output_dir)


if __name__ == "__main__":
    # 测试代码
    print("测试CoTDataRecorder...")
    
    # 创建记录器
    recorder = create_cot_data_recorder()
    
    # 开始新记录
    mission_id = recorder.start_new_recording("测试任务：扫描文件夹并创建备份")
    print(f"开始记录任务: {mission_id}")
    
    # 记录Brain层成功步骤
    recorder.record_brain_success(
        env="(at file1 workspace) (at file2 workspace)",
        chain_of_task=["(scan workspace)", "(create_folder backup)"]
    )
    
    # 记录Nerves层成功步骤
    recorder.record_nerves_success(
        task="(scan workspace)",
        env="(at file1 workspace) (at file2 workspace)",
        chain_of_action=["(scan workspace)"]
    )
    
    # 记录Brain层错误
    recorder.record_brain_error(
        env="(at file1 workspace) (at file2 workspace)",
        chain_of_task=["(move file1 workspace backup)"],
        error_message="目标文件夹backup不存在"
    )
    
    # 获取统计信息
    stats = recorder.get_statistics()
    print(f"统计信息: {stats}")
    
    # 保存数据
    filepath = recorder.save_current_data()
    print(f"数据已保存到: {filepath}")
    
    # 导出训练数据
    exported = recorder.export_training_data()
    print(f"训练数据已导出: {exported}")
    
    print("\n测试BatchCoTDataRecorder...")
    
    # 创建批量记录器
    batch_recorder = create_batch_cot_data_recorder()
    
    # 开始多个任务
    task1_recorder = batch_recorder.start_task("task_001", "任务1：创建文件夹")
    task2_recorder = batch_recorder.start_task("task_002", "任务2：移动文件")
    
    # 记录一些数据
    task1_recorder.record_brain_success(
        env="(empty workspace)",
        chain_of_task=["(create_folder test)"]
    )
    
    # 完成任务
    batch_recorder.complete_task("task_001")
    batch_recorder.complete_task("task_002")
    
    # 获取摘要
    summary = batch_recorder.get_summary()
    print(f"批量处理摘要: {summary}")