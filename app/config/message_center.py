import os
import json
import logging
import time
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageCenter:
    """消息中心"""
    
    MAX_MESSAGES = 100  # 最大保存消息数
    
    def __init__(self, redo_dir: str = '/redo', message_file: str = '/data/messages.json'):
        """初始化消息中心"""
        self.redo_dir = Path(redo_dir)
        self.message_file = Path(message_file)
        self.messages: List[Dict] = []
        
        # 确保目录存在
        self.redo_dir.mkdir(parents=True, exist_ok=True)
        self.message_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载历史消息
        self.load_messages()
    
    def add_message(self, message: Dict):
        """添加消息"""
        # 添加时间戳
        message['timestamp'] = datetime.now().isoformat()
        message['id'] = int(time.time() * 1000)  # 毫秒级时间戳作为ID
        
        # 添加到消息列表
        self.messages.append(message)
        
        # 如果有重做命令，保存到文件
        if 'redo_command' in message and message['redo_command']:
            self._save_redo_command(message['redo_command'], message)
        
        # 限制消息数量
        if len(self.messages) > self.MAX_MESSAGES:
            self.messages = self.messages[-self.MAX_MESSAGES:]
        
        # 保存消息
        self.save_messages()
        
        logger.debug(f"添加消息: {message.get('type', 'unknown')} - {message.get('message', '')}")
    
    def add_system_message(self, message: str, level: str = 'info'):
        """添加系统消息"""
        self.add_message({
            'type': 'system',
            'level': level,
            'message': message
        })
    
    def add_error_message(self, message: str):
        """添加错误消息"""
        self.add_message({
            'type': 'error',
            'level': 'error',
            'message': message
        })
    
    def add_success_message(self, message: str):
        """添加成功消息"""
        self.add_message({
            'type': 'success',
            'level': 'success',
            'message': message
        })
    
    def add_file_process_message(self, result: Dict):
        """添加文件处理消息"""
        message = {
            'type': 'file_process',
            'source': result.get('source', ''),
            'destination': result.get('destination', ''),
            'success': result.get('success', False),
            'message': result.get('message', '')
        }
        
        # 添加重做命令
        if 'redo_command' in result and result['redo_command']:
            message['redo_command'] = result['redo_command']
        
        self.add_message(message)
    
    def get_messages(self, limit: int = None, message_type: str = None) -> List[Dict]:
        """获取消息列表"""
        messages = self.messages.copy()
        
        # 过滤类型
        if message_type:
            messages = [m for m in messages if m.get('type') == message_type]
        
        # 限制数量（返回最新的消息）
        if limit:
            messages = messages[-limit:]
        
        # 按时间倒序排列
        messages.reverse()
        
        return messages
    
    def get_redo_commands(self) -> List[Dict]:
        """获取所有重做命令"""
        redo_messages = [
            m for m in self.messages 
            if m.get('redo_command') and not m.get('redo_processed', False)
        ]
        return redo_messages
    
    def mark_redo_processed(self, redo_id: int):
        """标记重做命令为已处理"""
        for message in self.messages:
            if message.get('id') == redo_id:
                message['redo_processed'] = True
                message['processed_at'] = datetime.now().isoformat()
                break
        
        self.save_messages()
    
    def _save_redo_command(self, command: str, context: Dict):
        """保存重做命令到文件"""
        try:
            # 创建重做文件
            redo_file = self.redo_dir / f"redo_{context['id']}.txt"
            redo_content = {
                'command': command,
                'timestamp': context['timestamp'],
                'context': context
            }
            
            with open(redo_file, 'w', encoding='utf-8') as f:
                json.dump(redo_content, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"保存重做命令: {redo_file}")
            
        except Exception as e:
            logger.error(f"保存重做命令失败: {str(e)}")
    
    def load_redo_commands(self) -> List[Dict]:
        """从文件加载重做命令"""
        redo_commands = []
        
        try:
            if self.redo_dir.exists():
                for redo_file in self.redo_dir.glob('redo_*.txt'):
                    try:
                        with open(redo_file, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                            redo_commands.append(content)
                    except Exception as e:
                        logger.error(f"读取重做文件失败: {redo_file}, 错误: {str(e)}")
        
        except Exception as e:
            logger.error(f"加载重做命令失败: {str(e)}")
        
        return redo_commands
    
    def save_messages(self):
        """保存消息到文件"""
        try:
            # 只保存必要的字段
            save_data = []
            for msg in self.messages:
                # 过滤敏感信息
                filtered = {k: v for k, v in msg.items() if k != 'context' or 'password' not in str(v).lower()}
                save_data.append(filtered)
            
            with open(self.message_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"保存消息失败: {str(e)}")
    
    def load_messages(self):
        """从文件加载消息"""
        try:
            if self.message_file.exists():
                with open(self.message_file, 'r', encoding='utf-8') as f:
                    self.messages = json.load(f)
                logger.info(f"加载了 {len(self.messages)} 条历史消息")
        
        except Exception as e:
            logger.error(f"加载消息失败: {str(e)}")
            self.messages = []
    
    def clear_messages(self, message_type: str = None):
        """清空消息"""
        if message_type:
            self.messages = [m for m in self.messages if m.get('type') != message_type]
        else:
            self.messages = []
        
        self.save_messages()
        logger.info(f"清空消息: {message_type or '全部'}")
    
    def clear_old_messages(self, days: int = 7):
        """清理旧消息"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # 转换时间戳并过滤
        filtered_messages = []
        for message in self.messages:
            try:
                # 解析时间戳
                if isinstance(message.get('timestamp'), str):
                    msg_time = datetime.fromisoformat(message['timestamp']).timestamp()
                else:
                    msg_time = message.get('timestamp', 0)
                
                if msg_time > cutoff_time:
                    filtered_messages.append(message)
            except Exception:
                # 保留无法解析时间的消息
                filtered_messages.append(message)
        
        removed_count = len(self.messages) - len(filtered_messages)
        self.messages = filtered_messages
        
        if removed_count > 0:
            self.save_messages()
            logger.info(f"清理了 {removed_count} 条旧消息")
    
    def get_stats(self) -> Dict:
        """获取消息统计信息"""
        stats = {
            'total_messages': len(self.messages),
            'pending_redo': len(self.get_redo_commands()),
            'type_count': {}
        }
        
        # 统计各类型消息数量
        for message in self.messages:
            msg_type = message.get('type', 'unknown')
            stats['type_count'][msg_type] = stats['type_count'].get(msg_type, 0) + 1
        
        return stats