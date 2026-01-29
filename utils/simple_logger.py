#!/usr/bin/env python3
"""
AIOS-PDDL 轻量级日志工具
快速迭代期使用的简单、高效的日志系统
"""

import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class QuickLogger:
    """
    快速日志器 - 为快速迭代期设计
    
    特点:
    - 极简API，一行代码即可记录日志
    - 彩色输出，易于区分
    - 无复杂配置，开箱即用
    - 支持上下文信息自动记录
    """
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[90m',      # 灰色
        'INFO': '\033[94m',       # 蓝色
        'SUCCESS': '\033[92m',    # 绿色
        'WARNING': '\033[93m',    # 黄色
        'ERROR': '\033[91m',      # 红色
        'CRITICAL': '\033[41m',   # 红底白字
        'RESET': '\033[0m',       # 重置
    }
    
    # 图标
    ICONS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '💥',
    }
    
    def __init__(self, name: str = "AIOS", level: LogLevel = LogLevel.INFO):
        """
        初始化日志器
        
        :param name: 日志器名称，会显示在日志中
        :param level: 日志级别，低于此级别的日志不会被记录
        """
        self.name = name
        self.level = level
        self._context: Dict[str, Any] = {}
        
    def set_context(self, **kwargs):
        """设置上下文信息"""
        self._context.update(kwargs)
        return self
        
    def clear_context(self):
        """清空上下文信息"""
        self._context.clear()
        return self
        
    def _should_log(self, level: LogLevel) -> bool:
        """检查是否应该记录此级别的日志"""
        return level.value >= self.level.value
        
    def _format_message(self, level: LogLevel, message: str) -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_name = level.name
        icon = self.ICONS.get(level_name, '')
        color = self.COLORS.get(level_name, self.COLORS['RESET'])
        
        # 基础格式
        parts = [f"[{timestamp}]", f"[{self.name}]", f"{icon} {message}"]
        
        # 添加上下文信息
        if self._context:
            context_str = " ".join([f"{k}={v}" for k, v in self._context.items()])
            parts.append(f"({context_str})")
        
        # 添加颜色
        formatted = " ".join(parts)
        if color and sys.stdout.isatty():  # 只在终端中显示颜色
            return f"{color}{formatted}{self.COLORS['RESET']}"
        return formatted
        
    def _log(self, level: LogLevel, message: str, **kwargs):
        """记录日志的内部方法"""
        if not self._should_log(level):
            return
            
        # 如果有额外的上下文，临时合并
        if kwargs:
            original_context = self._context.copy()
            self._context.update(kwargs)
            formatted = self._format_message(level, message)
            self._context = original_context
        else:
            formatted = self._format_message(level, message)
            
        # 输出到对应的流
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            print(formatted, file=sys.stderr)
        else:
            print(formatted, file=sys.stdout)
            
        # 立即刷新，确保在管道中也能看到
        sys.stdout.flush()
        sys.stderr.flush()
        
    # 便捷方法
    def debug(self, message: str, **kwargs):
        """记录调试信息"""
        self._log(LogLevel.DEBUG, message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """记录一般信息"""
        self._log(LogLevel.INFO, message, **kwargs)
        
    def success(self, message: str, **kwargs):
        """记录成功信息"""
        self._log(LogLevel.SUCCESS, message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """记录警告信息"""
        self._log(LogLevel.WARNING, message, **kwargs)
        
    def error(self, message: str, **kwargs):
        """记录错误信息"""
        self._log(LogLevel.ERROR, message, **kwargs)
        
    def critical(self, message: str, **kwargs):
        """记录严重错误信息"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
        
    def section(self, title: str):
        """记录一个章节标题"""
        if self._should_log(LogLevel.INFO):
            print("\n" + "="*60)
            print(f"📋 {title}")
            print("="*60)
            
    def step(self, step_num: int, total_steps: int, message: str):
        """记录步骤信息"""
        if self._should_log(LogLevel.INFO):
            progress = f"[{step_num}/{total_steps}]"
            self.info(f"{progress} {message}")
            
    def progress(self, current: int, total: int, message: str = ""):
        """记录进度信息"""
        if self._should_log(LogLevel.INFO):
            percentage = (current / total) * 100
            bar_length = 20
            filled = int(bar_length * current / total)
            bar = "█" * filled + "░" * (bar_length - filled)
            progress_msg = f"{bar} {percentage:.1f}% ({current}/{total})"
            if message:
                progress_msg = f"{message} {progress_msg}"
            self.info(progress_msg)


# 全局日志器实例
_default_logger = QuickLogger("AIOS")

# 全局便捷函数
def debug(message: str, **kwargs):
    _default_logger.debug(message, **kwargs)
    
def info(message: str, **kwargs):
    _default_logger.info(message, **kwargs)
    
def success(message: str, **kwargs):
    _default_logger.success(message, **kwargs)
    
def warning(message: str, **kwargs):
    _default_logger.warning(message, **kwargs)
    
def error(message: str, **kwargs):
    _default_logger.error(message, **kwargs)
    
def critical(message: str, **kwargs):
    _default_logger.critical(message, **kwargs)
    
def section(title: str):
    _default_logger.section(title)
    
def step(step_num: int, total_steps: int, message: str):
    _default_logger.step(step_num, total_steps, message)
    
def progress(current: int, total: int, message: str = ""):
    _default_logger.progress(current, total, message)


# 模块特定的日志器工厂
def get_logger(name: str) -> QuickLogger:
    """获取指定名称的日志器"""
    return QuickLogger(name)


# 测试函数
def test_logger():
    """测试日志器功能"""
    print("测试 QuickLogger 功能:")
    print("="*60)
    
    logger = QuickLogger("Test", level=LogLevel.DEBUG)
    
    logger.section("基本日志测试")
    logger.debug("这是一条调试信息")
    logger.info("这是一条信息")
    logger.success("操作成功完成")
    logger.warning("这是一个警告")
    logger.error("发生了一个错误")
    logger.critical("发生严重错误！")
    
    logger.section("上下文日志测试")
    logger.set_context(user="alice", task_id=123).info("开始处理任务")
    logger.set_context(progress=50).info("任务处理中")
    logger.set_context(result="success").success("任务完成")
    logger.clear_context()
    
    logger.section("步骤和进度测试")
    logger.step(1, 3, "初始化系统")
    logger.step(2, 3, "加载配置")
    logger.step(3, 3, "启动服务")
    
    logger.info("模拟进度:")
    for i in range(1, 11):
        logger.progress(i, 10, "处理数据")
        import time
        time.sleep(0.1)
    
    logger.section("全局函数测试")
    info("使用全局info函数")
    success("使用全局success函数")
    error("使用全局error函数")
    
    print("\n✅ 日志器测试完成")


if __name__ == "__main__":
    test_logger()