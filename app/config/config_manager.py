import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

# 尝试导入python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found, skipping environment variables loading")
    # 创建一个空的load_dotenv函数以避免错误
    def load_dotenv():
        pass

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        'tmdb_api_key': '',
        'douban_cookies': '',
        'fallback_enabled': True,
        'cache_dir': '/data',
        'redo_dir': '/redo',
        'default_dest_dir': '/dest',
        'ignore_patterns': ['.tmp', '.part', '.DS_Store', 'Thumbs.db'],
        'directory_configs': [
            # 示例配置
            {
                'name': '电影',
                'source_dir': '/source/movies',
                'dest_dir': '/dest/movies',
                'media_type': 'movie'
            },
            {
                'name': '电视剧',
                'source_dir': '/source/tv',
                'dest_dir': '/dest/tv',
                'media_type': 'tv'
            }
        ],
        'monitor_enabled': False,
        'log_level': 'INFO'
    }
    
    def __init__(self, config_file: str = '/config/config.json'):
        """初始化配置管理器"""
        self.config_file = Path(config_file)
        self.config = self.DEFAULT_CONFIG.copy()
        
        # 加载.env文件
        load_dotenv()
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果配置文件存在，加载它
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 合并配置
                    self._merge_config(file_config)
            else:
                # 创建默认配置文件
                self.save_config()
            
            # 从环境变量加载配置（优先级最高）
            self._load_from_env()
            
            # 验证必要的目录
            self._validate_directories()
            
            logger.info("配置加载成功")
            
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            # 使用默认配置
            self.config = self.DEFAULT_CONFIG.copy()
            self._load_from_env()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已保存到: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
    
    def update_config(self, new_config: Dict):
        """更新配置"""
        try:
            # 合并新配置
            self._merge_config(new_config)
            
            # 再次从环境变量加载（保持优先级）
            self._load_from_env()
            
            # 验证目录
            self._validate_directories()
            
            # 保存到文件
            self.save_config()
            
            logger.info("配置已更新")
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        return self.config.copy()
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置项"""
        self.config[key] = value
    
    def _merge_config(self, source: Dict):
        """合并配置字典"""
        for key, value in source.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                # 递归合并字典
                self._merge_config_dict(self.config[key], value)
            elif key in self.config and isinstance(self.config[key], list) and isinstance(value, list):
                # 替换列表
                self.config[key] = value
            else:
                # 直接替换
                self.config[key] = value
    
    def _merge_config_dict(self, target: Dict, source: Dict):
        """递归合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config_dict(target[key], value)
            else:
                target[key] = value
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mapping = {
            'TMDB_API_KEY': 'tmdb_api_key',
            'DOUBAN_COOKIES': 'douban_cookies',
            'LOG_LEVEL': 'log_level',
            'CACHE_DIR': 'cache_dir',
            'REDO_DIR': 'redo_dir',
            'DEFAULT_DEST_DIR': 'default_dest_dir'
        }
        
        for env_key, config_key in env_mapping.items():
            if env_key in os.environ:
                env_value = os.environ[env_key]
                # 特殊处理布尔值
                if config_key == 'fallback_enabled' or config_key == 'monitor_enabled':
                    env_value = env_value.lower() in ('true', '1', 'yes')
                self.config[config_key] = env_value
                logger.debug(f"从环境变量加载: {config_key} = {env_value}")
    
    def _validate_directories(self):
        """验证必要的目录存在"""
        directories = [
            self.config.get('cache_dir'),
            self.config.get('redo_dir'),
            self.config.get('default_dest_dir')
        ]
        
        # 添加配置的目录
        for dir_config in self.config.get('directory_configs', []):
            if 'source_dir' in dir_config:
                directories.append(dir_config['source_dir'])
            if 'dest_dir' in dir_config:
                directories.append(dir_config['dest_dir'])
        
        # 验证目录
        for dir_path in set(directories):
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get_directory_configs(self) -> List[Dict]:
        """获取目录配置列表"""
        return self.config.get('directory_configs', []).copy()
    
    def add_directory_config(self, config: Dict) -> bool:
        """添加目录配置"""
        try:
            dir_configs = self.config.get('directory_configs', [])
            dir_configs.append(config)
            self.config['directory_configs'] = dir_configs
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"添加目录配置失败: {str(e)}")
            return False
    
    def update_directory_config(self, index: int, config: Dict) -> bool:
        """更新目录配置"""
        try:
            dir_configs = self.config.get('directory_configs', [])
            if 0 <= index < len(dir_configs):
                dir_configs[index] = config
                self.config['directory_configs'] = dir_configs
                self.save_config()
                return True
            return False
        except Exception as e:
            logger.error(f"更新目录配置失败: {str(e)}")
            return False
    
    def delete_directory_config(self, index: int) -> bool:
        """删除目录配置"""
        try:
            dir_configs = self.config.get('directory_configs', [])
            if 0 <= index < len(dir_configs):
                del dir_configs[index]
                self.config['directory_configs'] = dir_configs
                self.save_config()
                return True
            return False
        except Exception as e:
            logger.error(f"删除目录配置失败: {str(e)}")
            return False