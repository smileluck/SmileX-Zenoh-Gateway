"""
数据存储模块
负责设备数据的存储和查询
"""

import json
import time
import sqlite3
import threading
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from logging import getLogger

logger = getLogger(__name__)


@dataclass
class DeviceData:
    """
    设备数据类
    """
    device_id: str
    data_type: str
    data: Dict[str, Any]
    timestamp: float
    id: Optional[int] = None
    created_at: Optional[float] = None


class DataStorage:
    """
    数据存储类
    使用 SQLite 存储设备数据
    """

    def __init__(self, db_path: str = "data/device_data.db"):
        """
        初始化数据存储
        
        Args:
            db_path: 数据库文件路径
        """
        self._db_path = db_path
        self._lock = threading.Lock()
        
        self._init_database()
        logger.info(f"初始化数据存储: {db_path}")

    def _init_database(self):
        """初始化数据库表"""
        db_dir = Path(self._db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_device_id 
                ON device_data(device_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON device_data(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_device_type 
                ON device_data(device_id, data_type)
            """)
            
            conn.commit()
            conn.close()

    def save_data(self, device_id: str, data_type: str, data: Dict[str, Any], timestamp: Optional[float] = None) -> int:
        """
        保存设备数据
        
        Args:
            device_id: 设备ID
            data_type: 数据类型
            data: 数据内容
            timestamp: 时间戳，默认为当前时间
        
        Returns:
            数据记录ID
        """
        if timestamp is None:
            timestamp = time.time()
        
        created_at = time.time()
        
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO device_data (device_id, data_type, data, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                device_id,
                data_type,
                json.dumps(data),
                timestamp,
                created_at
            ))
            
            data_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.debug(f"保存数据成功: device_id={device_id}, type={data_type}, id={data_id}")
            return data_id

    def get_data(
        self,
        device_id: str,
        data_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[DeviceData]:
        """
        查询设备数据
        
        Args:
            device_id: 设备ID
            data_type: 数据类型（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 返回数量限制
        
        Returns:
            设备数据列表
        """
        query = "SELECT id, device_id, data_type, data, timestamp, created_at FROM device_data WHERE device_id = ?"
        params = [device_id]
        
        if data_type:
            query += " AND data_type = ?"
            params.append(data_type)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(DeviceData(
                    device_id=row[1],
                    data_type=row[2],
                    data=json.loads(row[3]),
                    timestamp=row[4],
                    id=row[0],
                    created_at=row[5]
                ))
            
            conn.close()
            return results

    def get_latest_data(
        self,
        device_id: str,
        data_type: Optional[str] = None
    ) -> Optional[DeviceData]:
        """
        获取设备最新数据
        
        Args:
            device_id: 设备ID
            data_type: 数据类型（可选）
        
        Returns:
            最新设备数据，不存在返回 None
        """
        results = self.get_data(
            device_id=device_id,
            data_type=data_type,
            limit=1
        )
        
        return results[0] if results else None

    def delete_old_data(self, older_than_days: int = 30) -> int:
        """
        删除旧数据
        
        Args:
            older_than_days: 保留天数
        
        Returns:
            删除的记录数
        """
        cutoff_time = time.time() - (older_than_days * 86400)
        
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM device_data WHERE timestamp < ?
            """, (cutoff_time,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"删除旧数据: {deleted_count} 条（保留 {older_than_days} 天）")
            return deleted_count

    def get_data_count(self, device_id: Optional[str] = None) -> int:
        """
        获取数据记录数
        
        Args:
            device_id: 设备ID（可选）
        
        Returns:
            记录数
        """
        query = "SELECT COUNT(*) FROM device_data"
        params = []
        
        if device_id:
            query += " WHERE device_id = ?"
            params.append(device_id)
        
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
