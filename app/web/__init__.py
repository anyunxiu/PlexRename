from flask import Flask
from .routes import setup_routes
from .socketio import socketio

__all__ = ['create_app', 'socketio']

def create_app(config_manager=None, message_center=None):
    """创建Flask应用"""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = 'plexrename_secret_key'
    
    # 存储配置管理器和消息中心实例
    app.config['config_manager'] = config_manager
    app.config['message_center'] = message_center
    
    # 设置路由
    setup_routes(app)
    
    # 初始化Socket.IO
    socketio.init_app(app)
    
    return app