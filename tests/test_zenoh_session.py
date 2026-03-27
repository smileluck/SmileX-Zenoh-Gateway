"""
测试 Zenoh Session 模块
"""

import time
import threading

from smilex_zenoh_gateway.core import ZenohSession, Message, MessageType
from logging import getLogger

logger = getLogger(__name__)


def test_basic_connect():
    """测试基本连接功能"""
    logger.info("=" * 50)
    logger.info("测试基本连接功能")
    
    session = ZenohSession(node_id="test-node-1")
    
    try:
        connected = session.connect()
        assert connected, "连接应该成功"
        assert session.is_connected, "连接状态应该为 True"
        logger.info("✓ 基本连接测试通过")
        return session
    except Exception as e:
        logger.error(f"✗ 基本连接测试失败: {e}")
        raise


def test_publish_subscribe():
    """测试发布订阅功能"""
    logger.info("=" * 50)
    logger.info("测试发布订阅功能")
    
    session1 = ZenohSession(node_id="test-pub-1")
    session2 = ZenohSession(node_id="test-sub-1")
    
    received_message = None
    event = threading.Event()
    
    def callback(msg: Message):
        nonlocal received_message
        received_message = msg
        logger.info(f"收到消息: {msg.payload}")
        event.set()
    
    try:
        session1.connect()
        session2.connect()
        
        subscribed = session2.subscribe("test/topic", callback)
        assert subscribed, "订阅应该成功"
        
        time.sleep(0.5)
        
        test_msg = Message(
            msg_type=MessageType.DATA,
            source_id="test-pub-1",
            payload={"data": "hello world"},
            timestamp=time.time()
        )
        
        published = session1.publish("test/topic", test_msg)
        assert published, "发布应该成功"
        
        event.wait(timeout=2.0)
        
        assert received_message is not None, "应该收到消息"
        assert received_message.payload["data"] == "hello world", "消息内容应该匹配"
        
        logger.info("✓ 发布订阅测试通过")
        
    finally:
        session1.disconnect()
        session2.disconnect()


def test_query_reply():
    """测试查询回复功能"""
    logger.info("=" * 50)
    logger.info("测试查询回复功能")
    
    session1 = ZenohSession(node_id="test-query-1")
    session2 = ZenohSession(node_id="test-reply-1")
    
    def query_handler(msg: Message) -> Message:
        logger.info(f"收到查询: {msg.payload}")
        return Message(
            msg_type=MessageType.DATA,
            source_id="test-reply-1",
            payload={"response": "got it!", "query": msg.payload},
            timestamp=time.time()
        )
    
    try:
        session1.connect()
        session2.connect()
        
        declared = session2.declare_queryable("test/query", query_handler)
        assert declared, "声明查询服务应该成功"
        
        time.sleep(0.5)
        
        query_msg = Message(
            msg_type=MessageType.COMMAND,
            source_id="test-query-1",
            payload={"action": "get_status"},
            timestamp=time.time()
        )
        
        reply = session1.query("test/query", query_msg, timeout=2.0)
        
        assert reply is not None, "应该收到回复"
        assert reply.payload["response"] == "got it!", "回复内容应该匹配"
        logger.info("✓ 查询回复测试通过")
        
    finally:
        session1.disconnect()
        session2.disconnect()


def main():
    """运行所有测试"""
    logger.info("开始 Zenoh Session 模块测试")
    
    try:
        test_publish_subscribe()
        test_query_reply()
        logger.info("\n所有测试通过！✓")
    except Exception as e:
        logger.error(f"\n测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
