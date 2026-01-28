#!/usr/bin/env python3
"""
AxiomLabs MCP 服务器 (结构化返回版)

所有Tool返回结果都包含metadata字典，其中包含pddl_delta字段。
格式严格化，便于PDDL规划系统处理。
标准输出仅用于MCP协议，调试信息使用logging输出到stderr。
"""

import os
import sys
import json
import logging
import importlib
import pkgutil
from typing import Dict, Any, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool
from mcp.server import NotificationOptions
import mcp.server.stdio
import asyncio

# 配置logging，输出到stderr，级别为INFO（增加调试信息）
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("AxiomLabs_mcp_server")


# 创建服务器实例
server = Server("AxiomLabs-skills")

# 动态加载MCP技能
def load_mcp_skills():
    """
    动态加载 infrastructure.mcp_skills 模块下的所有技能类
    返回技能实例列表
    """
    skills = []
    skill_module = "infrastructure.mcp_skills"
    
    try:
        module = importlib.import_module(skill_module)
    except ImportError as e:
        logger.error(f"无法导入MCP技能模块 {skill_module}: {e}")
        return skills
    
    # 遍历模块中的所有属性
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        # 检查是否为类，且是MCPBaseSkill的子类（排除MCPBaseSkill自身）
        if isinstance(attr, type) and attr_name != "MCPBaseSkill":
            try:
                # 检查是否为MCPBaseSkill的子类
                from infrastructure.mcp_skills.mcp_base_skill import MCPBaseSkill as Base
                if issubclass(attr, Base) and attr is not Base:
                    skills.append(attr())
                    logger.info(f"加载MCP技能: {attr().name}")
            except ImportError:
                continue
    
    # 如果动态加载失败，回退到硬编码列表
    if not skills:
        logger.warning("动态加载技能失败，使用硬编码技能列表")
        from infrastructure.mcp_skills.scan_skill import ScanSkill
        from infrastructure.mcp_skills.move_skill import MoveSkill
        from infrastructure.mcp_skills.get_admin_skill import GetAdminSkill
        from infrastructure.mcp_skills.compress_skill import CompressSkill
        from infrastructure.mcp_skills.remove_file_skill import RemoveFileSkill
        skills = [
            ScanSkill(),
            MoveSkill(),
            GetAdminSkill(),
            CompressSkill(),
            RemoveFileSkill()
        ]
    
    return skills

# 加载技能实例
skill_instances = load_mcp_skills()
skill_map = {skill.name: skill for skill in skill_instances}

@server.list_tools()
async def handle_list_tools() -> list:
    """返回工具列表"""
    tools = []
    for skill in skill_instances:
        tools.append(
            Tool(
                name=skill.name,
                description=skill.description,
                inputSchema=skill.input_schema
            )
        )
    logger.info(f"列出工具: {[tool.name for tool in tools]}")
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list:
    """处理工具调用 - 返回结构化结果"""
    try:
        if name not in skill_map:
            return create_error_response(f"未知工具: {name}")
        
        skill = skill_map[name]
        return await skill.execute(arguments)
        
    except KeyError as e:
        return create_error_response(f"缺少必要参数: {e}")
    except Exception as e:
        return create_error_response(f"工具执行错误: {str(e)}")


# 保留原有的响应创建函数（技能类内部已实现，但这里仍保留作为备用）
def create_success_response(message: str, pddl_delta: str) -> List[Dict[str, Any]]:
    """创建成功的结构化响应"""
    metadata = {
        "pddl_delta": pddl_delta,
        "status": "success",
        "message": message
    }
    
    response_text = json.dumps({
        "human_readable": message,
        "metadata": metadata
    }, ensure_ascii=False)
    
    return [{"type": "text", "text": response_text}]

def create_error_response(error_message: str) -> List[Dict[str, Any]]:
    """创建错误的结构化响应"""
    metadata = {
        "status": "error",
        "error": error_message
    }
    
    response_text = json.dumps({
        "human_readable": f"错误: {error_message}",
        "metadata": metadata
    }, ensure_ascii=False)
    
    return [{"type": "text", "text": response_text}]


async def main():
    """主函数"""
    # 使用stdio传输
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="AxiomLabs-skills",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    # 启动服务器
    asyncio.run(main())