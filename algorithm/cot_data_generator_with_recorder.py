"""CoT数据生成器（带数据记录器集成）

增强版的CoTDataGenerator，集成数据记录器功能，能够生成符合SchemaFirst格式的数据。
"""
import sys
import os
from typing import List, Set, Dict, Any, Optional, Tuple
import asyncio

# 导入现有组件
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithm.cot_data_generator import CoTDataGenerator as BaseCoTDataGenerator
from infrastructure.storage.cot_data_recorder import CoTDataRecorder, create_cot_data_recorder
from config.data_schema import CoTDataPoint
from interface.llm import ILLM
from interface.planner import IPlanner


class CoTDataGeneratorWithRecorder(BaseCoTDataGenerator):
    """带数据记录器的CoT数据生成器（默认使用沙盒）"""
    
    def __init__(
        self,
        llm: ILLM,
        planner: Optional[IPlanner] = None,
        config: Optional[Dict[str, Any]] = None,
        recorder: Optional[CoTDataRecorder] = None,
        use_sandbox: bool = True
    ):
        """
        初始化带记录器的数据生成器
        
        :param llm: 基础LLM客户端
        :param planner: 规划器实例（可选）
        :param config: 配置字典
        :param recorder: 数据记录器实例（如果为None则创建新的）
        :param use_sandbox: 是否使用沙盒模式（默认True）
        """
        # 保存沙盒相关状态
        self.use_sandbox = use_sandbox
        self.sandbox_manager = None
        self.original_sandbox_env = None
        
        # 如果使用沙盒，先创建沙盒并设置环境变量
        if self.use_sandbox:
            self._setup_sandbox()
        
        # 调用父类初始化
        super().__init__(llm, planner, config)
        
        # 初始化数据记录器
        self.recorder = recorder or create_cot_data_recorder(
            output_dir=config.get("output_dir") if config else None
        )
        
        # 记录器状态
        self.current_mission_id: Optional[str] = None
    
    def _setup_sandbox(self):
        """设置沙盒环境"""
        try:
            from infrastructure.sandbox.sandbox_manager import SandboxManager
            
            # 创建沙盒管理器
            self.sandbox_manager = SandboxManager()
            sandbox_path = self.sandbox_manager.create_sandbox()
            
            # 保存原始环境变量
            self.original_sandbox_env = os.environ.get("SANDBOX_STORAGE_PATH")
            
            # 设置沙盒环境变量
            os.environ["SANDBOX_STORAGE_PATH"] = self.sandbox_manager.get_storage_path()
            
            print(f"🔒 沙盒模式已启用: {sandbox_path}")
            
        except Exception as e:
            print(f"⚠️ 沙盒设置失败，将使用非沙盒模式: {e}")
            self.use_sandbox = False
            self.sandbox_manager = None
    
    def _cleanup_sandbox(self):
        """清理沙盒环境"""
        if self.sandbox_manager and self.use_sandbox:
            try:
                # 恢复原始环境变量
                if self.original_sandbox_env is not None:
                    os.environ["SANDBOX_STORAGE_PATH"] = self.original_sandbox_env
                else:
                    os.environ.pop("SANDBOX_STORAGE_PATH", None)
                
                # 清理沙盒（可选，通常保留供调试）
                # self.sandbox_manager.clean_up()
                
                print("🔓 沙盒环境已清理")
                
            except Exception as e:
                print(f"⚠️ 沙盒清理失败: {e}")
    
    def generate_with_recording(self, user_task: str, save_to_file: bool = True) -> Dict[str, Any]:
        """
        生成CoT数据并记录到数据记录器
        
        :param user_task: 用户任务描述
        :param save_to_file: 是否保存到文件
        :return: 包含完整CoT数据和记录信息的字典
        """
        # 开始新的数据记录
        self.current_mission_id = self.recorder.start_new_recording(
            mission=user_task,
            domain=self.config.get("domain", "file-manager-extended")
        )
        
        # 调用父类的generate方法，但拦截关键事件进行记录
        result = self._generate_with_interception(user_task)
        
        # 添加记录器信息到结果
        result["recorder_info"] = {
            "mission_id": self.current_mission_id,
            "data_point": self.recorder.get_current_data().to_dict() if self.recorder.get_current_data() else None
        }
        
        # 如果需要，保存数据到文件
        if save_to_file and self.recorder.get_current_data():
            filepath = self.recorder.save_and_reset()
            result["recorder_info"]["saved_filepath"] = filepath
            self.current_mission_id = None
        
        return result
    
    def _generate_with_interception(self, user_task: str) -> Dict[str, Any]:
        """
        拦截父类generate方法的关键事件进行记录
        
        这个方法会重写父类的关键方法调用，在适当的位置插入记录器调用。
        由于父类的实现较复杂，这里采用简化策略：先运行父类方法，然后从结果中提取信息进行记录。
        """
        # 运行父类的generate方法
        original_result = super().generate(user_task)
        
        # 从原始结果中提取信息并记录
        self._record_from_result(original_result, user_task)
        
        return original_result
    
    def _record_from_result(self, result: Dict[str, Any], user_task: str):
        """从生成结果中提取信息并记录到数据记录器"""
        if not self.recorder or not self.current_mission_id:
            return
        
        # 记录Brain层信息
        brain_layer = result.get("brain_layer", {})
        if brain_layer:
            start_env = brain_layer.get("start_env", [])
            chain_of_mission = brain_layer.get("chain_of_mission", [])
            mission_reachability = brain_layer.get("mission_reachability", [])
            
            # 记录Brain层成功步骤
            if chain_of_mission and mission_reachability:
                for i, (reachable, predicted_state) in enumerate(mission_reachability):
                    if reachable:
                        env_str = self._format_env(predicted_state if i > 0 else start_env)
                        self.recorder.record_brain_success(
                            env=env_str,
                            chain_of_task=[chain_of_mission[i]] if i < len(chain_of_mission) else []
                        )
        
        # 记录Nerves层信息
        nerves_layers = result.get("nerves_layers", [])
        for nerves_layer in nerves_layers:
            if nerves_layer.get("success", False):
                task = nerves_layer.get("task", "")
                start_env = nerves_layer.get("start_env", [])
                chain_of_action = nerves_layer.get("chain_of_action", [])
                action_reachability = nerves_layer.get("action_reachability", [])
                
                if chain_of_action and action_reachability:
                    for i, (reachable, predicted_state) in enumerate(action_reachability):
                        if reachable:
                            env_str = self._format_env(predicted_state if i > 0 else start_env)
                            self.recorder.record_nerves_success(
                                task=task,
                                env=env_str,
                                chain_of_action=[chain_of_action[i]] if i < len(chain_of_action) else []
                            )
        
        # 记录错误信息
        error_messages = result.get("error_messages", [])
        for error_msg in error_messages:
            # 简化处理：将错误记录为Brain层错误
            # 在实际实现中，需要根据错误类型判断是Brain还是Nerves错误
            self.recorder.record_brain_error(
                env="",
                chain_of_task=[],
                error_message=error_msg
            )
    
    def _format_env(self, env_data) -> str:
        """格式化环境数据为字符串"""
        if isinstance(env_data, list):
            return " ".join(env_data)
        elif isinstance(env_data, str):
            return env_data
        else:
            return str(env_data)
    
    def record_brain_success_direct(
        self, 
        env: str, 
        chain_of_task: List[str], 
        change_reason: Optional[str] = None
    ):
        """直接记录Brain层成功步骤（供外部调用）"""
        if self.recorder and self.current_mission_id:
            self.recorder.record_brain_success(env, chain_of_task, change_reason)
    
    def record_nerves_success_direct(
        self, 
        task: str, 
        env: str, 
        chain_of_action: List[str]
    ):
        """直接记录Nerves层成功步骤（供外部调用）"""
        if self.recorder and self.current_mission_id:
            self.recorder.record_nerves_success(task, env, chain_of_action)
    
    def record_brain_error_direct(
        self, 
        env: str, 
        chain_of_task: List[str], 
        error_message: str
    ):
        """直接记录Brain层错误（供外部调用）"""
        if self.recorder and self.current_mission_id:
            self.recorder.record_brain_error(env, chain_of_task, error_message)
    
    def record_nerves_error_direct(
        self, 
        task: str, 
        env: str, 
        chain_of_action: List[str], 
        error_message: str
    ):
        """直接记录Nerves层错误（供外部调用）"""
        if self.recorder and self.current_mission_id:
            self.recorder.record_nerves_error(task, env, chain_of_action, error_message)
    
    def save_current_data(self, filename: Optional[str] = None) -> Optional[str]:
        """保存当前记录的数据"""
        if self.recorder and self.recorder.get_current_data():
            return self.recorder.save_and_reset(filename)
        return None
    
    def get_current_data_point(self) -> Optional[CoTDataPoint]:
        """获取当前数据点"""
        if self.recorder:
            return self.recorder.get_current_data()
        return None
    
    def export_training_data(self, output_dir: Optional[str] = None) -> Optional[Dict[str, List[str]]]:
        """导出训练数据"""
        if self.recorder and self.recorder.get_current_data():
            return self.recorder.export_training_data(output_dir)
        return None


# 工厂函数
def create_cot_data_generator_with_recorder(
    llm: ILLM,
    planner: Optional[IPlanner] = None,
    config: Optional[Dict[str, Any]] = None,
    recorder: Optional[CoTDataRecorder] = None,
    use_sandbox: bool = True  # 默认启用沙盒
) -> CoTDataGeneratorWithRecorder:
    """创建带数据记录器的CoT数据生成器实例（默认使用沙盒）"""
    return CoTDataGeneratorWithRecorder(llm, planner, config, recorder, use_sandbox)


# 简化的集成版本（直接修改关键方法）
class IntegratedCoTDataGenerator(BaseCoTDataGenerator):
    """完全集成的CoT数据生成器（直接修改关键方法）"""
    
    def __init__(
        self,
        llm: ILLM,
        planner: Optional[IPlanner] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, planner, config)
        
        # 初始化数据记录器
        self.recorder = create_cot_data_recorder(
            output_dir=config.get("output_dir") if config else None
        )
        self.current_mission_id: Optional[str] = None
    
    def generate(self, user_task: str) -> Dict[str, Any]:
        """重写generate方法，集成数据记录"""
        # 开始新的数据记录
        self.current_mission_id = self.recorder.start_new_recording(
            mission=user_task,
            domain=self.config.get("domain", "file-manager-extended")
        )
        
        # 调用父类方法（但需要拦截关键事件）
        # 由于父类方法复杂，这里采用简化实现：先运行，后记录
        result = super().generate(user_task)
        
        # 添加记录器信息
        result["mission_id"] = self.current_mission_id
        
        # 尝试从结果中提取数据并记录
        self._enhance_result_with_recording(result)
        
        return result
    
    def _enhance_result_with_recording(self, result: Dict[str, Any]):
        """用记录器数据增强结果"""
        if not self.recorder or not self.current_mission_id:
            return
        
        # 获取当前数据点
        data_point = self.recorder.get_current_data()
        if data_point:
            result["cot_data_point"] = data_point.to_dict()
            
            # 添加训练数据切分信息
            training_data = data_point.get_training_data()
            result["training_data_available"] = {
                "brain_steps": len(training_data["brain_data"]["steps"]),
                "nerves_steps": len(training_data["nerves_data"]["steps"]),
                "brain_errors": len(training_data["analysis_data"]["brain_errors"]),
                "nerves_errors": len(training_data["analysis_data"]["nerves_errors"])
            }
        
        # 保存数据到文件
        try:
            filepath = self.recorder.save_and_reset()
            result["saved_filepath"] = filepath
            self.current_mission_id = None
        except Exception as e:
            result["save_error"] = str(e)
    
    # 重写关键方法以插入记录器调用
    def _process_brain_nerves(self, user_task: str) -> Dict[str, Any]:
        """重写Brain+Nerves处理流程，插入记录器调用"""
        # 这里需要重写父类的整个方法以插入记录点
        # 由于实现复杂，这里返回简化版本
        result = super()._process_brain_nerves(user_task)
        
        # 在适当位置插入记录器调用
        # 实际实现需要更精细的拦截
        
        return result


# 测试代码
if __name__ == "__main__":
    print("测试CoTDataGeneratorWithRecorder...")
    
    # 模拟LLM（测试用）
    class MockLLM:
        def chat(self, messages, temperature=0.1):
            # 返回模拟响应
            return "(scan root)\n(move file1 root backup)"
    
    mock_llm = MockLLM()
    
    # 创建带记录器的生成器
    generator = CoTDataGeneratorWithRecorder(mock_llm)
    
    # 测试生成数据并记录
    test_task = "扫描root文件夹并将file1移动到backup"
    result = generator.generate_with_recording(test_task)
    
    print("生成结果:")
    print(f"任务: {test_task}")
    print(f"任务ID: {result.get('recorder_info', {}).get('mission_id', 'N/A')}")
    
    if "recorder_info" in result and result["recorder_info"].get("saved_filepath"):
        print(f"数据已保存到: {result['recorder_info']['saved_filepath']}")
    
    # 获取数据点
    data_point = generator.get_current_data_point()
    if data_point:
        print(f"数据点统计:")
        print(f"  Brain步骤: {len(data_point.brain_steps)}")
        print(f"  Nerves步骤: {len(data_point.nerves_steps)}")
        print(f"  Brain错误: {len(data_point.brain_errors)}")
        print(f"  Nerves错误: {len(data_point.nerves_errors)}")
    
    print("\n测试完成!")