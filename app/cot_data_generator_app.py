"""CoT数据批量生成工具

自动化批量生成CoT数据，支持任务队列、并行处理、进度监控和数据验证。
"""
import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import concurrent.futures
import threading
from queue import Queue

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from algorithm.cot_data_generator_with_recorder import create_cot_data_generator_with_recorder
from infrastructure.storage.cot_data_recorder import BatchCoTDataRecorder, create_batch_cot_data_recorder
from infrastructure.llm.deepseek_client import DeepSeekClient
from infrastructure.planner.lama_planner import LAMAPlanner
from config.settings import Settings
from config.data_schema import CoTDataPoint, validate_cot_data


class CoTDataBatchGenerator:
    """CoT数据批量生成器"""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None,
        max_workers: int = 3,
        use_sandbox: bool = True  # 默认启用沙盒
    ):
        """
        初始化批量生成器
        
        :param config: 配置字典
        :param output_dir: 输出目录（默认使用cot_data目录）
        :param max_workers: 最大工作线程数（默认3）
        :param use_sandbox: 是否使用沙盒模式（默认True）
        """
        self.config = config or {}
        self.max_workers = max_workers
        self.use_sandbox = use_sandbox  # 默认启用沙盒
        
        # 设置输出目录 - 默认使用cot_data目录
        if output_dir is None:
            # 默认输出到项目根目录/cot_data/时间戳/
            output_dir = os.path.join(
                project_root,
                "cot_data",
                datetime.now().strftime("%Y%m%d_%H%M%S")
            )
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"🚀 CoT数据批量生成器初始化完成")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"🔒 沙盒模式: {'✅ 启用' if use_sandbox else '❌ 禁用'}")
        print(f"👷 工作线程: {max_workers}")
        
        # 初始化批量记录器
        self.batch_recorder = create_batch_cot_data_recorder(self.output_dir)
        
        # 任务队列
        self.task_queue = Queue()
        self.results = []
        self.lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_steps": 0,
            "total_errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def load_tasks_from_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        从文件加载任务列表
        
        :param filepath: 任务文件路径（JSON格式）
        :return: 任务列表
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        
        tasks = []
        if isinstance(tasks_data, list):
            for i, task_item in enumerate(tasks_data):
                if isinstance(task_item, str):
                    tasks.append({
                        "task_id": f"task_{i:04d}",
                        "mission": task_item,
                        "domain": "file-manager-extended"
                    })
                elif isinstance(task_item, dict):
                    task_id = task_item.get("task_id", f"task_{i:04d}")
                    mission = task_item.get("mission", "")
                    domain = task_item.get("domain", "file-manager-extended")
                    tasks.append({
                        "task_id": task_id,
                        "mission": mission,
                        "domain": domain
                    })
        elif isinstance(tasks_data, dict):
            # 单个任务
            tasks.append({
                "task_id": tasks_data.get("task_id", "task_0001"),
                "mission": tasks_data.get("mission", ""),
                "domain": tasks_data.get("domain", "file-manager-extended")
            })
        
        return tasks
    
    def load_default_tasks(self) -> List[Dict[str, Any]]:
        """加载默认测试任务"""
        default_tasks = [
            "扫描当前文件夹",
            "创建一个名为test的文件夹",
            "在test文件夹中创建README.md文件",
            "将README.md文件重命名为README.txt",
            "复制README.txt到backup文件夹",
            "删除test文件夹",
            "压缩backup文件夹中的所有文件",
            "解压archive.zip文件到extracted文件夹",
            "获取管理员权限",
            "连接两个文件夹",
            "扫描workspace文件夹并创建备份",
            "先创建项目结构，然后备份重要文件",
            "如果文件存在则移动它，否则创建新文件",
            "除了txt文件外，移动所有文件到archive文件夹"
        ]
        
        tasks = []
        for i, mission in enumerate(default_tasks):
            tasks.append({
                "task_id": f"default_{i:04d}",
                "mission": mission,
                "domain": "file-manager-extended"
            })
        
        return tasks
    
    def add_task(self, task_id: str, mission: str, domain: str = "file-manager-extended"):
        """添加单个任务到队列"""
        self.task_queue.put({
            "task_id": task_id,
            "mission": mission,
            "domain": domain
        })
        with self.lock:
            self.stats["total_tasks"] += 1
    
    def add_tasks(self, tasks: List[Dict[str, Any]]):
        """添加多个任务到队列"""
        for task in tasks:
            self.task_queue.put(task)
        with self.lock:
            self.stats["total_tasks"] += len(tasks)
    
    def _process_single_task(self, task_info: Dict[str, Any], llm_client, planner) -> Dict[str, Any]:
        """
        处理单个任务
        
        :param task_info: 任务信息
        :param llm_client: LLM客户端
        :param planner: 规划器
        :return: 处理结果
        """
        task_id = task_info["task_id"]
        mission = task_info["mission"]
        domain = task_info.get("domain", "file-manager-extended")
        
        print(f"  [{task_id}] 开始处理: {mission}")
        
        try:
            # 创建带记录器的生成器
            generator = create_cot_data_generator_with_recorder(
                llm=llm_client,
                planner=planner,
                config={
                    "domain": domain,
                    "output_dir": os.path.join(self.output_dir, task_id)
                }
            )
            
            # 开始任务记录
            batch_recorder = self.batch_recorder.start_task(task_id, mission, domain)
            
            # 生成数据并记录
            result = generator.generate_with_recording(mission, save_to_file=False)
            
            # 完成任务并保存数据
            filename = f"cot_{task_id}_{int(time.time())}.json"
            filepath = self.batch_recorder.complete_task(task_id, filename)
            
            # 收集统计信息
            task_stats = batch_recorder.get_statistics() if hasattr(batch_recorder, 'get_statistics') else {}
            
            with self.lock:
                self.stats["completed_tasks"] += 1
                self.stats["successful_tasks"] += 1
                self.stats["total_steps"] += task_stats.get("total_steps", 0)
                self.stats["total_errors"] += task_stats.get("total_errors", 0)
            
            print(f"  [{task_id}] ✅ 处理成功: {task_stats.get('total_steps', 0)} 步骤, "
                  f"{task_stats.get('total_errors', 0)} 错误")
            
            return {
                "task_id": task_id,
                "success": True,
                "mission": mission,
                "filepath": filepath,
                "statistics": task_stats,
                "error": None
            }
            
        except Exception as e:
            with self.lock:
                self.stats["completed_tasks"] += 1
                self.stats["failed_tasks"] += 1
            
            print(f"  [{task_id}] ❌ 处理失败: {e}")
            
            return {
                "task_id": task_id,
                "success": False,
                "mission": mission,
                "filepath": None,
                "statistics": {},
                "error": str(e)
            }
    
    def run(self, use_mock_llm: bool = True, llm_api_key: Optional[str] = None):
        """
        运行批量生成
        
        :param use_mock_llm: 是否使用模拟LLM（用于测试）
        :param llm_api_key: LLM API密钥（如果不使用模拟LLM）
        """
        print("=" * 60)
        print("🚀 CoT数据批量生成器启动")
        print("=" * 60)
        print(f"输出目录: {self.output_dir}")
        print(f"最大工作线程: {self.max_workers}")
        print(f"总任务数: {self.stats['total_tasks']}")
        print("-" * 60)
        
        self.stats["start_time"] = datetime.now()
        
        # 初始化LLM客户端
        if use_mock_llm:
            print("使用模拟LLM（测试模式）")
            
            class MockLLM:
                def chat(self, messages, temperature=0.1):
                    # 根据消息内容返回不同的模拟响应
                    content = messages[-1]["content"] if messages else ""
                    
                    if "扫描" in content or "scan" in content.lower():
                        return "(scan workspace)"
                    elif "创建" in content or "create" in content.lower():
                        return "(create_folder test)\n(create_file README.md)"
                    elif "移动" in content or "move" in content.lower():
                        return "(move file1 workspace backup)"
                    elif "重命名" in content or "rename" in content.lower():
                        return "(rename file1 file2)"
                    elif "复制" in content or "copy" in content.lower():
                        return "(copy file1 workspace backup)"
                    elif "删除" in content or "delete" in content.lower():
                        return "(remove file1)"
                    elif "压缩" in content or "compress" in content.lower():
                        return "(compress file1 archive.zip)"
                    elif "解压" in content or "uncompress" in content.lower():
                        return "(uncompress archive.zip extracted)"
                    else:
                        return "(scan workspace)\n(create_folder backup)\n(move file1 workspace backup)"
            
            llm_client = MockLLM()
            planner = None
            
        else:
            print("使用真实LLM（生产模式）")
            if not llm_api_key:
                raise ValueError("生产模式需要提供LLM API密钥")
            
            # 加载配置
            settings = Settings.load_from_env()
            settings.llm_api_key = llm_api_key
            
            # 创建真实LLM客户端
            llm_client = DeepSeekClient(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model
            )
            
            # 创建规划器
            planner = LAMAPlanner(config=settings)
        
        # 使用线程池处理任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            # 提交所有任务
            while not self.task_queue.empty():
                task_info = self.task_queue.get()
                future = executor.submit(self._process_single_task, task_info, llm_client, planner)
                futures.append(future)
            
            # 收集结果
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    print(f"任务执行异常: {e}")
        
        # 更新结束时间
        self.stats["end_time"] = datetime.now()
        
        # 生成报告
        self._generate_report()
    
    def _generate_report(self):
        """生成处理报告"""
        print("\n" + "=" * 60)
        print("📊 批量处理报告")
        print("=" * 60)
        
        # 计算耗时
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = self.stats["end_time"] - self.stats["start_time"]
            print(f"总耗时: {duration}")
        
        print(f"总任务数: {self.stats['total_tasks']}")
        print(f"已完成任务: {self.stats['completed_tasks']}")
        print(f"成功任务: {self.stats['successful_tasks']}")
        print(f"失败任务: {self.stats['failed_tasks']}")
        
        if self.stats['completed_tasks'] > 0:
            success_rate = (self.stats['successful_tasks'] / self.stats['completed_tasks']) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        print(f"总步骤数: {self.stats['total_steps']}")
        print(f"总错误数: {self.stats['total_errors']}")
        
        if self.stats['total_steps'] > 0:
            error_rate = (self.stats['total_errors'] / (self.stats['total_steps'] + self.stats['total_errors'])) * 100
            print(f"错误率: {error_rate:.1f}%")
        
        # 批量记录器摘要
        batch_summary = self.batch_recorder.get_summary()
        print(f"\n📦 数据记录摘要:")
        print(f"  总数据点: {batch_summary.get('total_tasks', 0)}")
        print(f"  总步骤: {batch_summary.get('total_steps', 0)}")
        print(f"  总错误: {batch_summary.get('total_errors', 0)}")
        print(f"  成功率: {batch_summary.get('success_rate', 0):.1f}%")
        
        # 保存报告到文件
        report_file = os.path.join(self.output_dir, "batch_report.json")
        
        # 准备报告数据，确保所有datetime对象都被转换为字符串
        stats_copy = self.stats.copy()
        if stats_copy.get("start_time") and isinstance(stats_copy["start_time"], datetime):
            stats_copy["start_time"] = stats_copy["start_time"].isoformat()
        if stats_copy.get("end_time") and isinstance(stats_copy["end_time"], datetime):
            stats_copy["end_time"] = stats_copy["end_time"].isoformat()
        
        report_data = {
            "stats": stats_copy,
            "batch_summary": batch_summary,
            "results_summary": [
                {
                    "task_id": r["task_id"],
                    "success": r["success"],
                    "mission": r["mission"],
                    "filepath": r["filepath"]
                }
                for r in self.results
            ],
            "output_dir": self.output_dir,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        # 导出所有训练数据
        try:
            exported = self.batch_recorder.export_all_training_data()
            print(f"\n🎯 训练数据已导出:")
            print(f"  BrainLLM数据: {len(exported.get('brain_files', []))} 个文件")
            print(f"  NervesLLM数据: {len(exported.get('nerves_files', []))} 个文件")
            print(f"  AnalysisLLM数据: {len(exported.get('analysis_files', []))} 个文件")
        except Exception as e:
            print(f"\n⚠️  训练数据导出失败: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 批量生成完成!")
        print("=" * 60)
    
    def get_results(self) -> List[Dict[str, Any]]:
        """获取处理结果"""
        return self.results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description="CoT数据批量生成工具")
    parser.add_argument("--tasks-file", type=str, help="任务文件路径（JSON格式）")
    parser.add_argument("--output-dir", type=str, help="输出目录")
    parser.add_argument("--workers", type=int, default=3, help="工作线程数")
    parser.add_argument("--use-real-llm", action="store_true", help="使用真实LLM（需要API密钥）")
    parser.add_argument("--api-key", type=str, help="LLM API密钥")
    parser.add_argument("--default-tasks", action="store_true", help="使用默认测试任务")
    
    args = parser.parse_args()
    
    # 创建批量生成器
    generator = CoTDataBatchGenerator(
        output_dir=args.output_dir,
        max_workers=args.workers
    )
    
    # 加载任务
    if args.tasks_file:
        print(f"从文件加载任务: {args.tasks_file}")
        tasks = generator.load_tasks_from_file(args.tasks_file)
        generator.add_tasks(tasks)
    elif args.default_tasks:
        print("使用默认测试任务")
        tasks = generator.load_default_tasks()
        generator.add_tasks(tasks)
    else:
        print("错误: 必须提供任务源（--tasks-file 或 --default-tasks）")
        parser.print_help()
        return
    
    # 运行批量生成
    use_mock_llm = not args.use_real_llm
    llm_api_key = args.api_key
    
    try:
        generator.run(use_mock_llm=use_mock_llm, llm_api_key=llm_api_key)
    except Exception as e:
        print(f"批量生成失败: {e}")
        import traceback
        traceback.print_exc()


def quick_test():
    """快速测试函数"""
    print("运行快速测试...")
    
    # 创建批量生成器
    generator = CoTDataBatchGenerator(
        output_dir=os.path.join(project_root, "workspace", "test_batch"),
        max_workers=2
    )
    
    # 添加几个测试任务
    test_tasks = [
        {"task_id": "test_001", "mission": "扫描workspace文件夹", "domain": "file-manager-extended"},
        {"task_id": "test_002", "mission": "创建test文件夹", "domain": "file-manager-extended"},
        {"task_id": "test_003", "mission": "移动文件到backup", "domain": "file-manager-extended"},
    ]
    
    generator.add_tasks(test_tasks)
    
    # 运行测试（使用模拟LLM）
    print("使用模拟LLM运行测试...")
    generator.run(use_mock_llm=True)
    
    # 显示结果
    results = generator.get_results()
    print(f"\n测试完成，处理了 {len(results)} 个任务")
    
    for result in results:
        status = "✅ 成功" if result["success"] else "❌ 失败"
        print(f"  {result['task_id']}: {status} - {result['mission']}")
    
    return generator


if __name__ == "__main__":
    # 如果没有命令行参数，运行快速测试
    if len(sys.argv) == 1:
        print("未提供命令行参数，运行快速测试...")
        quick_test()
    else:
        main()