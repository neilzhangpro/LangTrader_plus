
from typing import Dict, Callable, List, Optional
from collections import defaultdict
from utils.logger import logger

import websockets
import asyncio
import json

class WSClient:
    """统一的WebSocket客户端 - 用于实时数据流推送"""
    
    def __init__(self, base_url: str = "wss://fstream.binance.com/ws") -> None:
        # 改为使用 /ws 端点，支持动态订阅
        self.base_url = base_url
        self.conn: Optional[websockets.WebSocketClientProtocol] = None
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.reconnect = True
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._subscribed_streams: List[str] = []
        self._reconnect_delay = 5  # 重连延迟（秒）
        self._max_reconnect_delay = 60
        self._request_id = 0  # 请求ID计数器
        
    def _get_next_id(self) -> int:
        """获取下一个请求ID"""
        self._request_id += 1
        return self._request_id
        
    async def connect(self):
        """建立WebSocket连接"""
        if self.conn is not None:
            return
            
        try:
            self.conn = await websockets.connect(self.base_url)
            logger.info(f"✅ WebSocket连接已建立: {self.base_url}")
            
            # 重新订阅之前的流
            if self._subscribed_streams:
                await self._resubscribe()
                
        except Exception as e:
            logger.error(f"❌ WebSocket连接失败: {e}", exc_info=True)
            raise
    
    async def _resubscribe(self):
        """重新订阅之前的流"""
        if not self._subscribed_streams:
            return
            
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": self._subscribed_streams,
            "id": self._get_next_id()
        }
        await self.conn.send(json.dumps(subscribe_msg))
        logger.info(f"重新订阅流: {self._subscribed_streams}")
    
    async def subscribe(self, stream: str, callback: Callable):
        """订阅数据流"""
        if stream not in self._subscribed_streams:
            self._subscribed_streams.append(stream)
            
        self.subscribers[stream].append(callback)
        
        if self.conn is not None:
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [stream],
                "id": self._get_next_id()
            }
            await self.conn.send(json.dumps(subscribe_msg))
            logger.info(f"订阅流: {stream}")
    
    async def unsubscribe(self, stream: str, callback: Optional[Callable] = None):
        """取消订阅数据流"""
        if callback:
            if stream in self.subscribers:
                self.subscribers[stream].remove(callback)
        else:
            self.subscribers.pop(stream, None)
        
        if stream in self._subscribed_streams:
            self._subscribed_streams.remove(stream)
            
        if self.conn is not None:
            unsubscribe_msg = {
                "method": "UNSUBSCRIBE",
                "params": [stream],
                "id": self._get_next_id()
            }
            await self.conn.send(json.dumps(unsubscribe_msg))
            logger.info(f"取消订阅流: {stream}")
    
    async def _handle_message(self, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            
            # 处理订阅确认消息
            if "result" in data and "id" in data:
                if data["result"] is None:
                    logger.debug(f"订阅确认: {data}")
                else:
                    logger.warning(f"订阅响应: {data}")
                return
            
            # Binance WebSocket 数据消息格式（使用 /ws 端点时的格式）
            # 格式1: 直接的数据对象（单一流）
            if "e" in data:  # 事件类型字段
                # 这是单一流的数据格式
                stream_name = f"{data.get('s', '').lower()}@{data.get('e', '').lower()}"
                # 根据事件类型构建流名称
                if data.get("e") == "kline":
                    stream_name = f"{data.get('s', '').lower()}@kline_{data.get('k', {}).get('i', '')}"
                elif data.get("e") == "24hrTicker":
                    stream_name = f"{data.get('s', '').lower()}@ticker"
                
                if stream_name in self.subscribers:
                    for callback in self.subscribers[stream_name]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(data)
                            else:
                                callback(data)
                        except Exception as e:
                            logger.error(f"回调函数执行失败: {e}", exc_info=True)
                return
            
            # 格式2: 组合流格式 {"stream": "...", "data": {...}}
            if "stream" in data and "data" in data:
                stream = data["stream"]
                payload = data["data"]
                
                # 通知所有订阅者
                if stream in self.subscribers:
                    for callback in self.subscribers[stream]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(payload)
                            else:
                                callback(payload)
                        except Exception as e:
                            logger.error(f"回调函数执行失败: {e}", exc_info=True)
                return
            
            # 未知格式，记录日志
            logger.debug(f"收到未知格式消息: {data}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 消息: {message}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
    
    async def _listen(self):
        """监听WebSocket消息"""
        while self._running:
            try:
                if self.conn is None:
                    await self.connect()
                
                message = await self.conn.recv()
                await self._handle_message(message)
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket连接已关闭")
                self.conn = None
                if self.reconnect:
                    await self._reconnect()
                else:
                    break
                    
            except Exception as e:
                logger.error(f"监听消息时出错: {e}", exc_info=True)
                self.conn = None
                if self.reconnect:
                    await self._reconnect()
                else:
                    break
    
    async def _reconnect(self):
        """自动重连"""
        delay = self._reconnect_delay
        while self._running and self.reconnect:
            try:
                logger.info(f"等待 {delay} 秒后重连...")
                await asyncio.sleep(delay)
                await self.connect()
                break
            except Exception as e:
                logger.error(f"重连失败: {e}")
                delay = min(delay * 2, self._max_reconnect_delay)
    
    async def start(self):
        """启动WebSocket客户端"""
        if self._running:
            return
            
        self._running = True
        await self.connect()
        self._task = asyncio.create_task(self._listen())
        logger.info("WebSocket客户端已启动")
    
    async def stop(self):
        """停止WebSocket客户端"""
        self._running = False
        self.reconnect = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self.conn:
            await self.conn.close()
            self.conn = None
            
        logger.info("WebSocket客户端已停止")
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()