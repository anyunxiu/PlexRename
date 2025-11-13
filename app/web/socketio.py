from flask_socketio import SocketIO
import logging
import threading
import time

logger = logging.getLogger(__name__)

# 创建Socket.IO实例
socketio = SocketIO(cors_allowed_origins="*")

# 消息队列
_message_queue = []
_message_lock = threading.Lock()

def add_to_queue(message):
    """添加消息到队列"""
    with _message_lock:
        _message_queue.append(message)


def broadcast_messages():
    """广播队列中的消息"""
    messages_to_send = []
    
    with _message_lock:
        if _message_queue:
            messages_to_send = _message_queue.copy()
            _message_queue.clear()
    
    for message in messages_to_send:
        try:
            message_type = message.get('type', 'info')
            socketio.emit('new_message', message, namespace='/api/messages')
        except Exception as e:
            logger.error(f"广播消息失败: {str(e)}")


# Socket.IO事件处理
@socketio.on('connect', namespace='/api/messages')
async def handle_connect():
    """处理客户端连接"""
    logger.info("客户端连接到消息命名空间")
    await socketio.emit('connected', {'message': '已连接到消息中心'}, namespace='/api/messages')


@socketio.on('disconnect', namespace='/api/messages')
def handle_disconnect():
    """处理客户端断开连接"""
    logger.info("客户端从消息命名空间断开")


@socketio.on('ping', namespace='/api/messages')
async def handle_ping():
    """处理ping事件"""
    await socketio.emit('pong', {'timestamp': time.time()}, namespace='/api/messages')


@socketio.on('get_status', namespace='/api/messages')
async def handle_get_status():
    """获取服务状态"""
    await socketio.emit('status', {
        'status': 'running',
        'timestamp': time.time()
    }, namespace='/api/messages')


# 消息类型通知函数
def notify_system_message(message, level='info'):
    """通知系统消息"""
    msg = {
        'type': 'system',
        'level': level,
        'message': message,
        'timestamp': time.time()
    }
    add_to_queue(msg)
    broadcast_messages()


def notify_error_message(message):
    """通知错误消息"""
    notify_system_message(message, 'error')


def notify_success_message(message):
    """通知成功消息"""
    notify_system_message(message, 'success')


def notify_file_process(result):
    """通知文件处理结果"""
    msg = {
        'type': 'file_process',
        'source': result.get('source', ''),
        'destination': result.get('destination', ''),
        'success': result.get('success', False),
        'message': result.get('message', ''),
        'timestamp': time.time()
    }
    add_to_queue(msg)
    broadcast_messages()


def notify_task_progress(task_id, progress, total, status='processing'):
    """通知任务进度"""
    msg = {
        'type': 'task_progress',
        'task_id': task_id,
        'progress': progress,
        'total': total,
        'percentage': int((progress / total) * 100) if total > 0 else 0,
        'status': status,
        'timestamp': time.time()
    }
    add_to_queue(msg)
    broadcast_messages()


def notify_monitor_status(enabled, watching_dirs=None):
    """通知监控状态"""
    msg = {
        'type': 'monitor_status',
        'enabled': enabled,
        'watching_dirs': watching_dirs or [],
        'timestamp': time.time()
    }
    add_to_queue(msg)
    broadcast_messages()


# 启动消息广播线程
_message_thread = None
_stop_thread = False

def start_message_thread():
    """启动消息广播线程"""
    global _message_thread, _stop_thread
    
    _stop_thread = False
    
    def message_loop():
        while not _stop_thread:
            broadcast_messages()
            time.sleep(0.5)  # 每500ms检查一次队列
    
    _message_thread = threading.Thread(target=message_loop, daemon=True)
    _message_thread.start()
    logger.info("消息广播线程已启动")


def stop_message_thread():
    """停止消息广播线程"""
    global _stop_thread
    
    _stop_thread = True
    if _message_thread:
        _message_thread.join(timeout=1.0)
        logger.info("消息广播线程已停止")