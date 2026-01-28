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

@server.list_tools()
async def handle_list_tools() -> list:
    """返回工具列表"""
    return [
        Tool(
            name="scan",
            description="扫描文件夹并生成PDDL事实。\nPDDL作用: 生成(at ?file ?folder)和(connected ?folder ?subfolder)事实，标记文件夹为已扫描(scanned ?folder)",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "description": "要扫描的文件夹名称"}
                },
                "required": ["folder"]
            }
        ),
        Tool(
            name="move",
            description="移动文件到另一个文件夹。\nPDDL作用: 删除源位置事实(at ?file ?from_folder)，添加目标位置事实(at ?file ?to_folder)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "文件名（PDDL格式，可能包含 _dot_）"},
                    "from_folder": {"type": "string", "description": "源文件夹名称"},
                    "to_folder": {"type": "string", "description": "目标文件夹名称"}
                },
                "required": ["file_name", "from_folder", "to_folder"]
            }
        ),
        Tool(
            name="get_admin",
            description="获取管理员权限。\nPDDL作用: 添加(has_admin_rights)事实，使后续需要权限的操作成为可能",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="compress",
            description="压缩文件。\nPDDL作用: 创建新文件事实(is_created ?archive)，添加位置事实(at ?archive ?folder)，标记压缩关系(is_compressed ?file ?archive)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "要压缩的文件名"},
                    "folder": {"type": "string", "description": "文件所在文件夹"},
                    "archive_name": {"type": "string", "description": "压缩包名称"}
                },
                "required": ["file_name", "folder", "archive_name"]
            }
        ),
        Tool(
            name="remove_file",
            description="删除文件。\nPDDL作用: 删除文件存在事实(at ?file ?folder)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "要删除的文件名"},
                    "folder_name": {"type": "string", "description": "文件所在文件夹"}
                },
                "required": ["file_name", "folder_name"]
            }
        )
    ]

def create_success_response(message: str, pddl_delta: str) -> List[Dict[str, Any]]:
    """创建成功的结构化响应"""
    metadata = {
        "pddl_delta": pddl_delta,
        "status": "success",
        "message": message
    }
    
    # 返回包含metadata的JSON文本
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

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list:
    """处理工具调用 - 返回结构化结果"""
    try:
        if name == "scan":
            folder = arguments["folder"]
            # 确定基础路径：假设 workspace 目录位于当前工作目录下
            base_path = os.path.join(os.getcwd(), "workspace")
            target_path = os.path.join(base_path, folder)
            logger.info(f"扫描: folder={folder}, cwd={os.getcwd()}, base_path={base_path}, target_path={target_path}")
            
            if not os.path.exists(target_path):
                logger.warning(f"目录不存在: {target_path}")
                return create_error_response(f"目录 {folder} 不存在")
            
            try:
                files = os.listdir(target_path)
                logger.info(f"扫描到文件列表: {files}")
            except Exception as e:
                logger.error(f"扫描目录失败: {e}")
                return create_error_response(f"无法扫描目录: {str(e)}")
            
            # 生成PDDL事实
            found_facts = []
            for f in files:
                # 忽略系统文件
                if f.startswith("."):
                    continue
                
                # 转换文件名：将 '.' 替换为 '_dot_'
                safe_name = f.replace(".", "_dot_")
                
                full_path = os.path.join(target_path, f)
                if os.path.isfile(full_path):
                    found_facts.append(f"(at {safe_name} {folder})")
                elif os.path.isdir(full_path):
                    # 双向连接性
                    found_facts.append(f"(connected {folder} {safe_name})")
                    found_facts.append(f"(connected {safe_name} {folder})")
            
            found_facts.append(f"(scanned {folder})")
            
            # 构建PDDL delta字符串，用空格分隔多个事实
            pddl_delta = " ".join(found_facts)
            message = f"扫描文件夹 {folder} 完成，发现 {len(files)} 个项目"
            logger.info(f"扫描完成: {message}, pddl_delta={pddl_delta}")
            return create_success_response(message, pddl_delta)
            
        elif name == "move":
            file_name = arguments["file_name"]
            from_folder = arguments["from_folder"]
            to_folder = arguments["to_folder"]
            message = f"移动 {file_name} 从 {from_folder} 到 {to_folder}"
            # PDDL delta: 删除(at file from_folder)，添加(at file to_folder)
            pddl_delta = f"-(at {file_name} {from_folder}) +(at {file_name} {to_folder})"
            return create_success_response(message, pddl_delta)
            
        elif name == "get_admin":
            message = "已获取管理员权限"
            # PDDL delta: 添加(has_admin_rights)事实
            pddl_delta = "(has_admin_rights)"
            return create_success_response(message, pddl_delta)
            
        elif name == "compress":
            file_name = arguments["file_name"]
            folder = arguments["folder"]
            archive_name = arguments["archive_name"]
            message = f"压缩 {file_name} 为 {archive_name}"
            # PDDL delta: 添加多个事实
            pddl_delta = f"(is_created {archive_name}) (at {archive_name} {folder}) (is_compressed {file_name} {archive_name})"
            return create_success_response(message, pddl_delta)
            
        elif name == "remove_file":
            file_name = arguments["file_name"]
            folder_name = arguments["folder_name"]
            message = f"删除 {file_name} 从 {folder_name}"
            # PDDL delta: 删除(at file folder)事实
            pddl_delta = f"-(at {file_name} {folder_name})"
            return create_success_response(message, pddl_delta)
            
        else:
            return create_error_response(f"未知工具: {name}")
            
    except KeyError as e:
        return create_error_response(f"缺少必要参数: {e}")
    except Exception as e:
        return create_error_response(f"工具执行错误: {str(e)}")


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