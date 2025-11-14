import os
import sys
import logging
import threading
import time
from pathlib import Path

# 尝试导入python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found, skipping environment variables loading")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('plexrename')

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入必要的模块
try:
    from app.config import ConfigManager, MessageCenter
    from app.core import FileProcessor
    from app.metadata import MetadataManager
    from app.monitor import FileMonitor
    from app.web import create_app, socketio
    logger.info("成功导入所有模块")
except ImportError as e:
    logger.error(f"导入模块失败: {str(e)}")
    sys.exit(1)


class PlexRenameApp:
    """Plex重命名应用主类"""
    
    def __init__(self):
        """初始化应用"""
        logger.info("初始化Plex重命名应用")
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化消息中心
        self.message_center = MessageCenter(
            redo_dir='/redo',
            message_file='/data/messages.json'
        )
        
        # 初始化元数据管理器
        config = self.config_manager.get_config()
        self.metadata_manager = MetadataManager(config)
        
        # 初始化文件处理器
        self.file_processor = FileProcessor(config)
        self.file_processor.set_metadata_client(self.metadata_manager)
        
        # 初始化文件监控器
        self.file_monitor = None
        self.monitor_thread = None
        self._stop_event = threading.Event()
        
        # 初始化Flask应用
        self.app = create_app(
            config_manager=self.config_manager,
            message_center=self.message_center
        )
        
        # 存储监控器到app配置中，供路由使用
        self.app.config['file_monitor'] = self._get_file_monitor
    
    def _get_file_monitor(self):
        """获取文件监控器实例"""
        if not self.file_monitor:
            self._init_file_monitor()
        return self.file_monitor
    
    def _init_file_monitor(self):
        """初始化文件监控器"""
        config = self.config_manager.get_config()
        directories = config.get('directories', [])
        
        # 准备监控目录
        watch_dirs = []
        for dir_config in directories:
            source_dir = dir_config.get('source')
            target_dir = dir_config.get('target')
            if source_dir and target_dir:
                watch_dirs.append({
                    'source': source_dir,
                    'target': target_dir,
                    'name': dir_config.get('name', 'Unnamed')
                })
        
        # 创建监控器
        if watch_dirs:
            self.file_monitor = FileMonitor(
                directories=watch_dirs,
                file_processor=self.file_processor,
                message_center=self.message_center
            )
            logger.info(f"初始化文件监控器，监控目录数: {len(watch_dirs)}")
    
    def start_monitor(self):
        """启动文件监控"""
        config = self.config_manager.get_config()
        
        if not config.get('monitor_enabled', False):
            logger.info("监控未启用")
            return
        
        if not self.file_monitor:
            self._init_file_monitor()
        
        if self.file_monitor and not self.monitor_thread:
            self._stop_event.clear()
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
            logger.info("文件监控已启动")
    
    def stop_monitor(self):
        """停止文件监控"""
        if self._stop_event:
            self._stop_event.set()
        
        if self.file_monitor:
            self.file_monitor.stop()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3.0)
            self.monitor_thread = None
        
        logger.info("文件监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        try:
            # 启动监控器
            if self.file_monitor:
                self.file_monitor.start()
                
                # 发送监控状态通知
                self.message_center.add_system_message(
                    '文件监控已启动', 'info'
                )
            
            # 持续运行直到收到停止信号
            while not self._stop_event.is_set():
                time.sleep(1)
                
                # 检查配置是否有变化
                if self.file_monitor and self.config_manager.has_changed():
                    logger.info("配置已更改，重启监控器")
                    self.file_monitor.stop()
                    self._init_file_monitor()
                    if self.file_monitor:
                        self.file_monitor.start()
                    self.config_manager.reset_changed_flag()
                    
        except Exception as e:
            logger.error(f"监控循环出错: {str(e)}")
            self.message_center.add_error_message(
                f'监控服务异常: {str(e)}'
            )
        finally:
            if self.file_monitor:
                self.file_monitor.stop()
    
    def run_web_server(self):
        """运行Web服务器"""
        try:
            logger.info("启动Web服务器")
            
            # 启动文件监控
            self.start_monitor()
            
            # 运行Socket.IO服务器
            socketio.run(
                self.app,
                host='0.0.0.0',
                port=int(os.getenv('PORT', 5000)),
                debug=False
            )
            
        except KeyboardInterrupt:
            logger.info("接收到停止信号，正在关闭...")
        except Exception as e:
            logger.error(f"Web服务器异常: {str(e)}")
        finally:
            # 停止监控
            self.stop_monitor()
            logger.info("应用已关闭")
    
    def run_once(self, source_dir=None, target_dir=None, mode='all'):
        """运行一次批量处理"""
        try:
            # 如果未指定目录，使用配置中的第一个目录
            if not source_dir or not target_dir:
                config = self.config_manager.get_config()
                directories = config.get('directories', [])
                if directories:
                    source_dir = directories[0].get('source')
                    target_dir = directories[0].get('target')
            
            if not source_dir or not target_dir:
                logger.error("源目录或目标目录未指定")
                return []
            
            logger.info(f"开始批量处理: {source_dir} -> {target_dir}, 模式: {mode}")
            
            # 执行批量处理
            if mode == 'compare':
                results = self.file_processor.compare_and_process(source_dir, target_dir)
            else:
                results = self.file_processor.batch_process(source_dir, target_dir)
            
            # 统计结果
            success_count = sum(1 for r in results if r.get('success'))
            error_count = len(results) - success_count
            
            logger.info(f"批量处理完成: 成功 {success_count}, 失败 {error_count}")
            
            # 发送系统消息
            self.message_center.add_system_message(
                f'批量处理完成: 成功 {success_count}, 失败 {error_count}',
                'info'
            )
            
            return results
            
        except Exception as e:
            logger.error(f"批量处理出错: {str(e)}")
            self.message_center.add_error_message(
                f'批量处理失败: {str(e)}'
            )
            return []


def main():
    """主入口函数"""
    # 创建应用实例
    app = PlexRenameApp()
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == 'run':
            app.run_once()
        else:
            logger.error("未知命令")
            sys.exit(1)
    else:
        # 默认运行Web服务器
        app.run_web_server()


if __name__ == '__main__':
    main()