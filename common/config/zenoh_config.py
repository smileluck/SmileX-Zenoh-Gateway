"""
Zenoh 配置管理模块
负责加载、合并和管理各端的 zenoh_config.json 配置文件
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from copy import deepcopy

from logging import getLogger

logger = getLogger(__name__)


class ZenohConfigManager:
    """
    Zenoh 配置管理器类
    负责加载各端独立的 zenoh_config.json 配置文件，并与 env 配置合并
    """

    def __init__(self, node_type: str, config_dir: Optional[str] = None):
        """
        初始化 Zenoh 配置管理器
        
        Args:
            node_type: 节点类型，可选值: "api", "cloud", "robot"
            config_dir: 配置文件目录，默认为项目根目录下的 config 文件夹
        """
        self.node_type = node_type.lower()
        
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            project_root = self._get_project_root()
            self.config_dir = project_root / "config"
        
        self.config_file = self.config_dir / f"zenoh_config_{self.node_type}.json"
        self._cached_config: Optional[Dict[str, Any]] = None
        
        logger.info(f"初始化 Zenoh 配置管理器，节点类型: {self.node_type}，配置文件: {self.config_file}")

    def _get_project_root(self) -> Path:
        """
        获取项目根目录
        
        Returns:
            项目根目录的 Path 对象
        """
        current_dir = Path(__file__).resolve()
        for _ in range(5):
            if (current_dir / "pyproject.toml").exists():
                return current_dir
            current_dir = current_dir.parent
        return Path.cwd()

    def _create_default_config(self) -> Dict[str, Any]:
        """
        创建默认的 Zenoh 配置
        
        Returns:
            默认配置字典
        """
        base_config = {
            "mode": "peer",
            "connect": {
                "endpoints": []
            },
            "listen": {
                "endpoints": ["tcp/0.0.0.0:7447"]
            },
            "scouting": {
                "multicast": {
                    "enabled": True,
                    "interface": "auto",
                    "address": "224.0.0.224:7446"
                },
                "gossip": {
                    "enabled": False,
                    "seed": []
                }
            },
            "transport": {
                "link": {
                    "tcp": {
                        "accept_timeout": "10s",
                        "accept_backlog": 100,
                        "max_sessions": 1000
                    },
                    "unix": {
                        "enabled": False
                    }
                }
            },
            "timestamping": {
                "enabled": False,
                "source": "local"
            }
        }
        
        if self.node_type == "cloud":
            base_config["mode"] = "router"
            base_config["listen"]["endpoints"] = ["tcp/0.0.0.0:7447"]
            base_config["scouting"]["multicast"]["enabled"] = True
        elif self.node_type == "robot":
            base_config["mode"] = "peer"
            base_config["listen"]["endpoints"] = ["tcp/0.0.0.0:0"]
        elif self.node_type == "api":
            base_config["mode"] = "peer"
            base_config["listen"]["endpoints"] = ["tcp/0.0.0.0:0"]
        
        return base_config

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            配置字典
        """
        if self._cached_config is not None and not force_reload:
            return deepcopy(self._cached_config)
        
        if not self.config_file.exists():
            logger.warning(f"配置文件不存在，将创建默认配置: {self.config_file}")
            self._save_default_config()
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"成功加载配置文件: {self.config_file}")
            
            self._cached_config = config
            return deepcopy(config)
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 JSON 解析失败: {e}")
            logger.warning("使用默认配置替代")
            return self._create_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}", exc_info=True)
            return self._create_default_config()

    def _save_default_config(self):
        """
        保存默认配置到文件
        """
        try:
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建配置目录: {self.config_dir}")
            
            default_config = self._create_default_config()
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"已创建默认配置文件: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存默认配置文件失败: {e}", exc_info=True)

    def merge_env_config(self, config: Dict[str, Any], env_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 env 配置合并到 zenoh 配置中
        
        Args:
            config: 原始 zenoh 配置
            env_config: env 中的 zenoh 相关配置
            
        Returns:
            合并后的配置
        """
        merged_config = deepcopy(config)
        
        if "zenoh_connect" in env_config and env_config["zenoh_connect"]:
            connect_endpoints = [ep.strip() for ep in env_config["zenoh_connect"].split(",") if ep.strip()]
            if connect_endpoints:
                if "connect" not in merged_config:
                    merged_config["connect"] = {}
                merged_config["connect"]["endpoints"] = connect_endpoints
                logger.info(f"从 env 配置合并连接端点: {connect_endpoints}")
        
        if "zenoh_listen" in env_config and env_config["zenoh_listen"]:
            listen_endpoints = [ep.strip() for ep in env_config["zenoh_listen"].split(",") if ep.strip()]
            if listen_endpoints:
                if "listen" not in merged_config:
                    merged_config["listen"] = {}
                merged_config["listen"]["endpoints"] = listen_endpoints
                logger.info(f"从 env 配置合并监听端点: {listen_endpoints}")
        
        return merged_config

    def get_zenoh_config(self, env_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取完整的 zenoh 配置（含 env 合并）
        
        Args:
            env_config: env 中的 zenoh 相关配置字典
            
        Returns:
            完整的 zenoh 配置字典
        """
        config = self.load_config()
                
        return config

    def save_config(self, config: Dict[str, Any]):
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置字典
        """
        try:
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self._cached_config = config
            logger.info(f"配置已保存到: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}", exc_info=True)
            raise


_managers: Dict[str, ZenohConfigManager] = {}


def get_zenoh_config_manager(node_type: str, config_dir: Optional[str] = None) -> ZenohConfigManager:
    """
    获取或创建 Zenoh 配置管理器单例
    
    Args:
        node_type: 节点类型
        config_dir: 配置文件目录
        
    Returns:
        ZenohConfigManager 实例
    """
    key = f"{node_type}_{config_dir or 'default'}"
    
    if key not in _managers:
        _managers[key] = ZenohConfigManager(node_type, config_dir)
    
    return _managers[key]
