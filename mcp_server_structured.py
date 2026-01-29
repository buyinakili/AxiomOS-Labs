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
    动态加载多个目录下的MCP技能类
    
    扫描以下目录：
    1. infrastructure/mcp_skills/ (核心技能)
    2. 环境变量 SANDBOX_MCP_SKILLS_DIR 指定的目录（沙盒技能）
    
    返回技能实例列表
    """
    skills = []
    skill_module = "infrastructure.mcp_skills"
    
    # 目录列表
    skill_dirs = []
    
    # 1. 核心技能目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    core_skill_dir = os.path.join(current_dir, "infrastructure", "mcp_skills")
    skill_dirs.append(("core", core_skill_dir))
    
    # 2. 沙盒技能目录（通过环境变量）
    sandbox_skill_dir = os.environ.get("SANDBOX_MCP_SKILLS_DIR")
    if sandbox_skill_dir and os.path.exists(sandbox_skill_dir):
        skill_dirs.append(("sandbox", sandbox_skill_dir))
    
    # 导入MCPBaseSkill用于类型检查
    try:
        from infrastructure.mcp_skills.mcp_base_skill import MCPBaseSkill as Base
    except ImportError as e:
        logger.error(f"无法导入MCPBaseSkill: {e}")
        return skills
    
    # 扫描每个目录
    for dir_type, skill_dir in skill_dirs:
        if not os.path.exists(skill_dir):
            logger.debug(f"技能目录不存在 ({dir_type}): {skill_dir}")
            continue
        
        logger.info(f"扫描{dir_type}技能目录: {skill_dir}")
        
        # 扫描目录下的所有.py文件
        for filename in os.listdir(skill_dir):
            # 加载所有.py文件，除了mcp_base_skill.py
            # 包括：1) 以_skill.py结尾的文件（核心技能） 2) generated_skill_v*.py文件（生成的技能）
            if filename.endswith(".py") and filename != "mcp_base_skill.py":
                # 检查是否是技能文件
                is_core_skill = filename.endswith("_skill.py")
                is_generated_skill = filename.startswith("generated_skill_")
                
                if not (is_core_skill or is_generated_skill):
                    continue
                    
                module_name = filename[:-3]  # 移除.py
                try:
                    # 动态导入模块
                    # 对于沙盒目录，需要特殊处理导入路径
                    if dir_type == "sandbox":
                        # 将沙盒目录添加到 Python 路径
                        import sys
                        if skill_dir not in sys.path:
                            sys.path.insert(0, skill_dir)
                        
                        # 直接导入文件
                        spec = importlib.util.spec_from_file_location(module_name, os.path.join(skill_dir, filename))
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                    else:
                        # 核心技能使用标准导入
                        full_module_name = f"{skill_module}.{module_name}"
                        module = importlib.import_module(full_module_name)
                    
                    # 查找模块中所有MCPBaseSkill的子类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, Base) and attr is not Base:
                            try:
                                skill_instance = attr()
                                skills.append(skill_instance)
                                logger.info(f"加载MCP技能 ({dir_type}): {skill_instance.name}")
                            except Exception as e:
                                logger.error(f"实例化技能 {attr_name} 失败: {e}")
                except ImportError as e:
                    logger.error(f"导入模块 {filename} 失败: {e}")
                except Exception as e:
                    logger.error(f"处理文件 {filename} 时出错: {e}")
    
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
    
    # 去重（按技能名称）
    unique_skills = {}
    for skill in skills:
        if skill.name not in unique_skills:
            unique_skills[skill.name] = skill
        else:
            logger.warning(f"重复技能名称: {skill.name}，跳过")
    
    return list(unique_skills.values())

# 缓存技能实例和环境变量状态
_skill_instances_cache = None
_skill_map_cache = None
_last_sandbox_dir = None

def _reload_skills_if_needed():
    """检查是否需要重新加载技能（环境变量变化时）"""
    global _skill_instances_cache, _skill_map_cache, _last_sandbox_dir
    
    current_sandbox_dir = os.environ.get("SANDBOX_MCP_SKILLS_DIR")
    
    # 如果缓存为空或环境变量变化，重新加载
    if (_skill_instances_cache is None or
        _last_sandbox_dir != current_sandbox_dir):
        
        _last_sandbox_dir = current_sandbox_dir
        _skill_instances_cache = load_mcp_skills()
        _skill_map_cache = {skill.name: skill for skill in _skill_instances_cache}
        logger.info(f"技能重新加载完成，共 {len(_skill_instances_cache)} 个技能")
        return True
    return False

# 初始加载
_reload_skills_if_needed()

@server.list_tools()
async def handle_list_tools() -> list:
    """返回工具列表 - 只在需要时重新加载技能"""
    # 检查是否需要重新加载
    _reload_skills_if_needed()
    
    tools = []
    for skill in _skill_instances_cache:
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
        # 确保使用最新的技能映射
        if name not in _skill_map_cache:
            return create_error_response(f"未知工具: {name}")
        
        skill = _skill_map_cache[name]
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
    # 记录启动时的环境变量状态
    sandbox_storage_path = os.environ.get("SANDBOX_STORAGE_PATH")
    sandbox_skills_dir = os.environ.get("SANDBOX_MCP_SKILLS_DIR")
    
    logger.info(f"MCP服务器启动 - 环境变量检查:")
    logger.info(f"  SANDBOX_STORAGE_PATH: {sandbox_storage_path}")
    logger.info(f"  SANDBOX_MCP_SKILLS_DIR: {sandbox_skills_dir}")
    logger.info(f"  当前工作目录: {os.getcwd()}")
    
    # 检查是否为沙盒模式，如果是则改变工作目录到沙盒存储路径
    target_working_dir = None
    
    # 优先使用SANDBOX_STORAGE_PATH
    if sandbox_storage_path and os.path.exists(sandbox_storage_path):
        target_working_dir = sandbox_storage_path
        logger.info(f"使用沙盒存储路径作为工作目录: {target_working_dir}")
    else:
        # 生产模式：尝试使用默认的workspace目录
        # 检查当前工作目录下是否有workspace目录
        current_cwd = os.getcwd()
        workspace_dir = os.path.join(current_cwd, "workspace")
        if os.path.exists(workspace_dir):
            target_working_dir = workspace_dir
            logger.info(f"使用默认workspace目录作为工作目录: {target_working_dir}")
        else:
            # 如果当前目录没有workspace，尝试在项目根目录下查找
            # 假设MCP服务器是从项目根目录运行的
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace_dir = os.path.join(project_root, "workspace")
            if os.path.exists(workspace_dir):
                target_working_dir = workspace_dir
                logger.info(f"使用项目根目录下的workspace目录作为工作目录: {target_working_dir}")
            else:
                logger.info("未找到workspace目录，保持原工作目录")
    
    # 切换到目标工作目录
    if target_working_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(target_working_dir)
            logger.info(f"切换到工作目录: {target_working_dir}")
            logger.info(f"当前工作目录: {os.getcwd()}")
        except Exception as e:
            logger.error(f"切换工作目录失败: {e}")
    
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