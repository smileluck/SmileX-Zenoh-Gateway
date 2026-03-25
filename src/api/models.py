"""
API 数据模型
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class DeviceInfoResponse(BaseModel):
    """
    设备信息响应模型
    """
    device_id: str
    device_name: str
    device_type: str
    status: str
    last_heartbeat: float
    ip_address: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    registered_at: float


class CommandRequest(BaseModel):
    """
    指令请求模型
    """
    device_id: str
    command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: float = 10.0


class CommandResponse(BaseModel):
    """
    指令响应模型
    """
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None


class SystemStatusResponse(BaseModel):
    """
    系统状态响应模型
    """
    app_name: str
    app_version: str
    total_devices: int
    online_devices: int
    uptime: float
    timestamp: float


class AuthRequest(BaseModel):
    """
    认证请求模型
    """
    device_id: str
    device_secret: str


class AuthResponse(BaseModel):
    """
    认证响应模型
    """
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    message: str = ""


class ApiResponse(BaseModel):
    """
    通用 API 响应模型
    """
    success: bool
    message: str
    data: Optional[Any] = None
