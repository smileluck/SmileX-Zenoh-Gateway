"""
RESTful API 主模块
"""

import time
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from common.config.settings import settings
from common.utils.logger import logger
from common.core import ZenohSession, DeviceManager, DeviceInfo, Message, MessageType
from common.security import AuthManager, TokenType
from .models import (
    DeviceInfoResponse,
    CommandRequest,
    CommandResponse,
    SystemStatusResponse,
    AuthRequest,
    AuthResponse,
    ApiResponse
)


# 全局变量
_zenoh_session: Optional[ZenohSession] = None
_device_manager: Optional[DeviceManager] = None
_auth_manager: Optional[AuthManager] = None
_start_time: float = 0.0
_valid_device_secrets: Dict[str, str] = {}

# HTTP Bearer 安全方案
security = HTTPBearer()


def get_zenoh_session() -> ZenohSession:
    """
    获取 Zenoh 会话
    
    Returns:
        Zenoh 会话实例
    """
    if _zenoh_session is None:
        raise RuntimeError("Zenoh 会话未初始化")
    return _zenoh_session


def get_device_manager() -> DeviceManager:
    """
    获取设备管理器
    
    Returns:
        设备管理器实例
    """
    if _device_manager is None:
        raise RuntimeError("设备管理器未初始化")
    return _device_manager


def get_auth_manager() -> AuthManager:
    """
    获取认证管理器
    
    Returns:
        认证管理器实例
    """
    if _auth_manager is None:
        raise RuntimeError("认证管理器未初始化")
    return _auth_manager


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    验证访问令牌
    
    Args:
        credentials: HTTP Bearer 凭证
    
    Returns:
        设备ID
    
    Raises:
        HTTPException: 令牌验证失败
    """
    auth_mgr = get_auth_manager()
    token_info = auth_mgr.verify_token(credentials.credentials)
    
    if token_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的访问令牌"
        )
    
    if token_info.token_type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要访问令牌"
        )
    
    return token_info.device_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理
    
    Args:
        app: FastAPI 应用实例
    """
    global _zenoh_session, _device_manager, _auth_manager, _start_time, _valid_device_secrets
    
    logger.info("启动 API 服务...")
    
    try:
        _start_time = time.time()
        
        _zenoh_session = ZenohSession(node_id="cloud-controller", node_type="api")
        if not _zenoh_session.connect():
            raise RuntimeError("无法连接到 Zenoh 网络")
        
        _device_manager = DeviceManager(_zenoh_session)
        _device_manager.register_self("云端控制平台", "cloud")
        _device_manager.start()
        
        _auth_manager = AuthManager()
        
        _valid_device_secrets = {
            "robot-001": "secret123",
            "robot-002": "secret456",
            "robot-003": "secret789"
        }
        
        logger.info("API 服务启动成功")
        yield
        
    except Exception as e:
        logger.error(f"API 服务启动失败: {e}", exc_info=True)
        raise
    finally:
        logger.info("停止 API 服务...")
        
        if _device_manager:
            _device_manager.stop()
        
        if _zenoh_session:
            _zenoh_session.disconnect()
        
        logger.info("API 服务已停止")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于 Zenoh 技术的机器人通信与云端控制平台 API",
    lifespan=lifespan
)


@app.get("/", tags=["系统"])
async def root() -> ApiResponse:
    """
    根路径
    """
    return ApiResponse(
        success=True,
        message="欢迎使用 SmileX Zenoh Gateway API",
        data={
            "app_name": settings.app_name,
            "version": settings.app_version
        }
    )


@app.get("/api/v1/system/status", tags=["系统"], response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """
    获取系统状态
    """
    device_mgr = get_device_manager()
    all_devices = device_mgr.get_all_devices()
    online_devices = device_mgr.get_online_devices()
    
    return SystemStatusResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        total_devices=len(all_devices),
        online_devices=len(online_devices),
        uptime=time.time() - _start_time,
        timestamp=time.time()
    )


@app.post("/api/v1/auth/login", tags=["认证"], response_model=AuthResponse)
async def auth_login(request: AuthRequest) -> AuthResponse:
    """
    设备认证登录
    """
    auth_mgr = get_auth_manager()
    
    token_info = auth_mgr.authenticate_device(
        request.device_id,
        request.device_secret,
        _valid_device_secrets
    )
    
    if token_info is None:
        return AuthResponse(
            success=False,
            message="设备认证失败"
        )
    
    refresh_token = auth_mgr.generate_token(
        request.device_id,
        TokenType.REFRESH
    )
    
    return AuthResponse(
        success=True,
        access_token=token_info.token,
        refresh_token=refresh_token.token,
        expires_in=int(token_info.expires_at - token_info.issued_at),
        message="认证成功"
    )


@app.get("/api/v1/devices", tags=["设备管理"])
async def list_devices(
    _: str = Depends(verify_token)
) -> ApiResponse:
    """
    获取所有设备列表
    """
    device_mgr = get_device_manager()
    devices = device_mgr.get_all_devices()
    
    device_responses = [
        DeviceInfoResponse(
            device_id=d.device_id,
            device_name=d.device_name,
            device_type=d.device_type,
            status=d.status.value,
            last_heartbeat=d.last_heartbeat,
            ip_address=d.ip_address,
            metadata=d.metadata,
            registered_at=d.registered_at
        )
        for d in devices
    ]
    
    return ApiResponse(
        success=True,
        message="获取设备列表成功",
        data=device_responses
    )


@app.get("/api/v1/devices/{device_id}", tags=["设备管理"])
async def get_device(
    device_id: str,
    _: str = Depends(verify_token)
) -> ApiResponse:
    """
    获取指定设备信息
    """
    device_mgr = get_device_manager()
    device = device_mgr.get_device(device_id)
    
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备不存在: {device_id}"
        )
    
    device_response = DeviceInfoResponse(
        device_id=device.device_id,
        device_name=device.device_name,
        device_type=device.device_type,
        status=device.status.value,
        last_heartbeat=device.last_heartbeat,
        ip_address=device.ip_address,
        metadata=device.metadata,
        registered_at=device.registered_at
    )
    
    return ApiResponse(
        success=True,
        message="获取设备信息成功",
        data=device_response
    )


@app.post("/api/v1/commands", tags=["指令控制"])
async def send_command(
    request: CommandRequest,
    _: str = Depends(verify_token)
) -> CommandResponse:
    """
    发送指令到设备
    """
    device_mgr = get_device_manager()
    zenoh_session = get_zenoh_session()
    
    device = device_mgr.get_device(request.device_id)
    if device is None:
        return CommandResponse(
            success=False,
            message=f"设备不存在: {request.device_id}"
        )
    
    if device.status.value != "online":
        return CommandResponse(
            success=False,
            message=f"设备不在线: {request.device_id}"
        )
    

    
    msg = Message(
        msg_type=MessageType.COMMAND,
        source_id="cloud-controller",
        payload={
            "command": request.command,
            "parameters": request.parameters
        },
        timestamp=time.time()
    )
    
    key_expr = f"smilex/device/{request.device_id}/command"
    reply = zenoh_session.query(key_expr, msg, timeout=request.timeout)
    
    if reply is None:
        return CommandResponse(
            success=False,
            message=f"指令发送超时: {request.device_id}"
        )
    
    return CommandResponse(
        success=True,
        message="指令执行成功",
        result=reply.payload
    )


def run_server():
    """
    运行 API 服务器
    """
    import uvicorn
    
    logger.info(f"启动 API 服务器: {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
