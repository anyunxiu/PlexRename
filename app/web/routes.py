from flask import render_template, request, jsonify, current_app
import json
import logging

logger = logging.getLogger(__name__)

def setup_routes(app):
    """设置所有路由"""
    
    @app.route('/')
    def index():
        """首页"""
        config_manager = current_app.config.get('config_manager')
        message_center = current_app.config.get('message_center')
        
        # 获取配置
        config = config_manager.get_config() if config_manager else {}
        
        # 获取消息统计
        stats = message_center.get_stats() if message_center else {}
        
        return render_template('index.html', config=config, stats=stats)
    
    @app.route('/api/config', methods=['GET', 'POST'])
    def api_config():
        """配置管理API"""
        config_manager = current_app.config.get('config_manager')
        
        if request.method == 'GET':
            # 获取配置
            config = config_manager.get_config() if config_manager else {}
            return jsonify(config)
        
        elif request.method == 'POST':
            # 更新配置
            try:
                data = request.get_json()
                if config_manager:
                    config_manager.update_config(data)
                    config_manager.save_config()
                    
                    # 通知消息中心
                    message_center = current_app.config.get('message_center')
                    if message_center:
                        message_center.add_system_message('配置已更新', 'info')
                
                return jsonify({'success': True, 'message': '配置已更新'})
            
            except Exception as e:
                logger.error(f"更新配置失败: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/messages', methods=['GET'])
    def api_messages():
        """获取消息列表"""
        message_center = current_app.config.get('message_center')
        
        if not message_center:
            return jsonify([])
        
        # 获取参数
        limit = request.args.get('limit', type=int)
        message_type = request.args.get('type')
        
        # 获取消息
        messages = message_center.get_messages(limit=limit, message_type=message_type)
        
        return jsonify(messages)
    
    @app.route('/api/clear_messages', methods=['POST'])
    def api_clear_messages():
        """清空消息"""
        message_center = current_app.config.get('message_center')
        
        if message_center:
            data = request.get_json() or {}
            message_type = data.get('type')
            message_center.clear_messages(message_type=message_type)
        
        return jsonify({'success': True})
    
    @app.route('/api/run_batch_process', methods=['POST'])
    def api_run_batch_process():
        """运行批量处理"""
        try:
            # 导入处理器
            from app.core.file_processor import FileProcessor
            from app.metadata.metadata_manager import MetadataManager
            
            config_manager = current_app.config.get('config_manager')
            message_center = current_app.config.get('message_center')
            
            if not config_manager:
                return jsonify({'success': False, 'error': '配置管理器未初始化'}), 500
            
            config = config_manager.get_config()
            
            # 获取请求数据
            data = request.get_json() or {}
            source_dir = data.get('source_dir')
            target_dir = data.get('target_dir')
            mode = data.get('mode', 'all')  # 'all' 或 'compare'
            
            # 验证参数
            if not source_dir or not target_dir:
                return jsonify({'success': False, 'error': '源目录和目标目录不能为空'}), 400
            
            # 创建元数据管理器
            metadata_manager = MetadataManager(config.get('tmdb_api_key', ''), config.get('douban_cookies', ''))
            
            # 创建文件处理器
            file_processor = FileProcessor(metadata_manager, message_center)
            
            # 异步处理，返回任务ID
            # 这里简单实现，实际应该使用线程池
            if mode == 'compare':
                results = file_processor.compare_and_process(source_dir, target_dir)
            else:
                results = file_processor.batch_process(source_dir, target_dir)
            
            # 统计结果
            success_count = sum(1 for r in results if r.get('success'))
            error_count = len(results) - success_count
            
            return jsonify({
                'success': True,
                'total': len(results),
                'success_count': success_count,
                'error_count': error_count
            })
        
        except Exception as e:
            logger.error(f"批量处理失败: {str(e)}")
            
            # 添加错误消息
            message_center = current_app.config.get('message_center')
            if message_center:
                message_center.add_error_message(f'批量处理失败: {str(e)}')
            
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/toggle_monitor', methods=['POST'])
    def api_toggle_monitor():
        """切换监控状态"""
        try:
            # 导入监控器
            from app.monitor.file_monitor import FileMonitor
            
            # 获取监控器实例（实际应该从app配置中获取）
            # 这里需要一个单例或者全局实例管理
            monitor = request.environ.get('file_monitor') or current_app.config.get('file_monitor')
            
            data = request.get_json() or {}
            enabled = data.get('enabled', False)
            
            if enabled:
                if monitor and not monitor.is_running():
                    monitor.start()
            else:
                if monitor and monitor.is_running():
                    monitor.stop()
            
            return jsonify({'success': True, 'enabled': enabled})
        
        except Exception as e:
            logger.error(f"切换监控状态失败: {str(e)}")
            
            message_center = current_app.config.get('message_center')
            if message_center:
                message_center.add_error_message(f'切换监控状态失败: {str(e)}')
            
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/redo_commands', methods=['GET'])
    def api_redo_commands():
        """获取重做命令"""
        message_center = current_app.config.get('message_center')
        
        if not message_center:
            return jsonify([])
        
        commands = message_center.get_redo_commands()
        return jsonify(commands)
    
    @app.route('/api/execute_redo/<int:redo_id>', methods=['POST'])
    def api_execute_redo(redo_id):
        """执行重做命令"""
        try:
            message_center = current_app.config.get('message_center')
            
            if not message_center:
                return jsonify({'success': False, 'error': '消息中心未初始化'}), 500
            
            # 查找重做命令
            commands = message_center.get_redo_commands()
            redo_command = next((c for c in commands if c.get('id') == redo_id), None)
            
            if not redo_command:
                return jsonify({'success': False, 'error': '重做命令不存在'}), 404
            
            # 执行重做命令
            # 这里简单实现，实际应该根据命令内容执行相应操作
            command = redo_command.get('redo_command', '')
            
            # 解析命令（假设格式为 'process_file source target'）
            if command.startswith('process_file'):
                parts = command.split(' ', 2)
                if len(parts) == 3:
                    source, target = parts[1], parts[2]
                    
                    # 导入处理器
                    from app.core.file_processor import FileProcessor
                    from app.metadata.metadata_manager import MetadataManager
                    
                    config_manager = current_app.config.get('config_manager')
                    if config_manager:
                        config = config_manager.get_config()
                        metadata_manager = MetadataManager(config.get('tmdb_api_key', ''), config.get('douban_cookies', ''))
                        file_processor = FileProcessor(metadata_manager, message_center)
                        
                        # 处理单个文件
                        result = file_processor.process_file(source, target)
                        
                        if result.get('success'):
                            message_center.mark_redo_processed(redo_id)
                        
                        return jsonify({'success': True, 'result': result})
            
            return jsonify({'success': False, 'error': '无法执行重做命令'}), 400
            
        except Exception as e:
            logger.error(f"执行重做命令失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """健康检查"""
        return jsonify({
            'status': 'healthy',
            'service': 'plexrename'
        })