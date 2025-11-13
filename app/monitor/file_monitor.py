import os
import logging
import time
from threading import Thread
from typing import Dict, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class NewFileHandler(FileSystemEventHandler):
    """文件系统事件处理器"""
    
    def __init__(self, callback: Callable, ignore_patterns: List[str] = None):
        """初始化事件处理器"""
        self.callback = callback
        self.ignore_patterns = ignore_patterns or []
        self.processing_delay = 1.0  # 处理延迟，确保文件完全写入
    
    def on_created(self, event: FileSystemEvent):
        """处理文件创建事件"""
        if event.is_directory:
            return
        
        # 检查是否需要忽略
        if self._should_ignore(event.src_path):
            return
        
        # 等待文件完全写入
        time.sleep(self.processing_delay)
        
        try:
            # 检查文件是否存在且大小合理
            if os.path.exists(event.src_path) and os.path.getsize(event.src_path) > 0:
                logger.info(f"检测到新文件: {event.src_path}")
                self.callback(event.src_path)
        except Exception as e:
            logger.error(f"处理新文件事件失败: {event.src_path}, 错误: {str(e)}")
    
    def on_modified(self, event: FileSystemEvent):
        """处理文件修改事件（用于捕获复制完成）"""
        if event.is_directory:
            return
        
        # 检查是否需要忽略
        if self._should_ignore(event.src_path):
            return
        
        # 对于大文件，可能需要多次修改事件
        # 我们使用简单的策略：如果文件在短时间内没有再次修改，则处理
        try:
            # 检查文件是否存在
            if not os.path.exists(event.src_path):
                return
            
            # 记录当前修改时间
            current_mtime = os.path.getmtime(event.src_path)
            time.sleep(2.0)  # 等待2秒
            
            # 检查是否再次被修改
            if os.path.exists(event.src_path) and os.path.getmtime(event.src_path) == current_mtime:
                logger.info(f"文件修改完成: {event.src_path}")
                self.callback(event.src_path)
        except Exception as e:
            logger.error(f"处理文件修改事件失败: {event.src_path}, 错误: {str(e)}")
    
    def _should_ignore(self, path: str) -> bool:
        """检查是否应该忽略文件"""
        filename = os.path.basename(path)
        
        # 忽略临时文件和隐藏文件
        if filename.startswith('.') or filename.endswith('.tmp') or filename.endswith('.part'):
            return True
        
        # 忽略指定模式
        for pattern in self.ignore_patterns:
            if pattern in filename:
                return True
        
        return False


class FileMonitor:
    """文件监控器"""
    
    def __init__(self, config: Dict):
        """初始化文件监控器"""
        self.config = config
        self.observer = None
        self.event_handler = None
        self.monitor_thread = None
        self.is_running = False
        
        # 文件处理器回调（稍后设置）
        self.file_processor = None
        self.message_callback = None
    
    def set_file_processor(self, processor):
        """设置文件处理器"""
        self.file_processor = processor
    
    def set_message_callback(self, callback: Callable):
        """设置消息回调"""
        self.message_callback = callback
    
    def _on_new_file(self, file_path: str):
        """处理新文件"""
        if not self.file_processor:
            logger.error("文件处理器未设置")
            return
        
        # 获取对应的目标目录配置
        target_dir = self._get_target_dir(file_path)
        if not target_dir:
            logger.warning(f"未找到匹配的目标目录: {file_path}")
            return
        
        # 处理文件
        result = self.file_processor.process_file(file_path, target_dir)
        
        # 发送消息
        if self.message_callback:
            self.message_callback({
                'type': 'file_processed',
                'result': result
            })
    
    def _get_target_dir(self, file_path: str) -> Optional[str]:
        """根据配置获取目标目录"""
        # 从配置中获取目录配置列表
        dir_configs = self.config.get('directory_configs', [])
        
        # 按顺序匹配源目录
        for config in dir_configs:
            source_dir = config.get('source_dir', '').strip()
            if source_dir and file_path.startswith(source_dir):
                return config.get('dest_dir', '')
        
        # 如果没有匹配，返回默认目标目录
        return self.config.get('default_dest_dir', '')
    
    def start(self):
        """启动监控"""
        if self.is_running:
            logger.warning("监控已经在运行")
            return
        
        try:
            # 获取监控目录列表
            monitor_dirs = []
            dir_configs = self.config.get('directory_configs', [])
            for config in dir_configs:
                source_dir = config.get('source_dir', '').strip()
                if source_dir and os.path.exists(source_dir):
                    monitor_dirs.append(source_dir)
            
            if not monitor_dirs:
                logger.error("没有有效的监控目录")
                return
            
            # 创建事件处理器
            self.event_handler = NewFileHandler(
                callback=self._on_new_file,
                ignore_patterns=self.config.get('ignore_patterns', [])
            )
            
            # 创建观察者
            self.observer = Observer()
            
            # 添加监控目录
            for dir_path in monitor_dirs:
                logger.info(f"开始监控目录: {dir_path}")
                self.observer.schedule(
                    self.event_handler,
                    dir_path,
                    recursive=True
                )
            
            # 启动观察者
            self.observer.start()
            self.is_running = True
            
            # 启动监控线程（用于保持运行）
            self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            logger.info("文件监控已启动")
            
            # 发送启动消息
            if self.message_callback:
                self.message_callback({
                    'type': 'monitor_started',
                    'directories': monitor_dirs
                })
            
        except Exception as e:
            logger.error(f"启动文件监控失败: {str(e)}")
            self.stop()
    
    def stop(self):
        """停止监控"""
        if not self.is_running:
            return
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
            
            self.is_running = False
            self.event_handler = None
            
            logger.info("文件监控已停止")
            
            # 发送停止消息
            if self.message_callback:
                self.message_callback({
                    'type': 'monitor_stopped'
                })
                
        except Exception as e:
            logger.error(f"停止文件监控失败: {str(e)}")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                time.sleep(1)
                # 检查观察者是否还在运行
                if self.observer and not self.observer.is_alive():
                    logger.error("观察者意外停止，尝试重启")
                    self.stop()
                    self.start()
            except Exception as e:
                logger.error(f"监控循环错误: {str(e)}")
                time.sleep(5)
    
    def update_config(self, config: Dict):
        """更新配置"""
        # 保存新配置
        self.config = config
        
        # 如果监控正在运行，重启以应用新配置
        if self.is_running:
            logger.info("更新配置，重启监控")
            self.stop()
            self.start()
    
    def is_active(self) -> bool:
        """检查监控是否正在运行"""
        return self.is_running and self.observer and self.observer.is_alive()
    
    def __del__(self):
        """析构函数，确保停止监控"""
        self.stop()