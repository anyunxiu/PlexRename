import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

try:
    from .tmdb_client import TMDBClient
    from .douban_client import DoubanClient
except ImportError as e:
    logging.warning(f"Warning: Failed to import metadata clients: {str(e)}")
    # 创建空的类以避免导入错误
    class TMDBClient:
        def __init__(self, api_key='', cache_dir=None):
            self.api_key = api_key
            self.cache_dir = cache_dir
        def search_movie(self, *args, **kwargs):
            return None
        def search_tv(self, *args, **kwargs):
            return None
        def close(self):
            pass
    
    class DoubanClient:
        def __init__(self, cookies='', cache_dir=None):
            self.cookies = cookies
            self.cache_dir = cache_dir
        def search(self, *args, **kwargs):
            return None
        def close(self):
            pass

logger = logging.getLogger(__name__)


class MetadataManager:
    """元数据管理器，整合多个元数据源"""
    
    def __init__(self, config: Dict):
        """初始化元数据管理器"""
        # 初始化TMDB客户端
        tmdb_api_key = config.get('tmdb_api_key') or config.get('TMDB_API_KEY')
        self.tmdb_client = TMDBClient(
            api_key=tmdb_api_key,
            cache_dir=config.get('cache_dir', './data/tmdb_cache')
        )
        
        # 初始化豆瓣客户端
        douban_cookies = config.get('douban_cookies') or config.get('DOUBAN_COOKIES')
        self.douban_client = DoubanClient(
            cookies=douban_cookies,
            cache_dir=config.get('cache_dir', './data/douban_cache')
        )
        
        # 配置回退策略
        self.fallback_enabled = config.get('fallback_enabled', True)
    
    def get_metadata(self, title: str, media_type: str = None, year: str = None) -> Optional[Dict]:
        """获取元数据，支持回退机制"""
        if not title:
            return None
        
        # 标准化媒体类型
        if media_type == 'tv' or media_type == '电视剧':
            media_type = 'tv'
        elif media_type == 'movie' or media_type == '电影':
            media_type = 'movie'
        else:
            # 未知类型，先尝试电影再尝试电视剧
            metadata = self._try_get_metadata(title, 'movie', year)
            if not metadata and self.fallback_enabled:
                metadata = self._try_get_metadata(title, 'tv', year)
            return metadata
        
        # 已知类型
        return self._try_get_metadata(title, media_type, year)
    
    def _try_get_metadata(self, title: str, media_type: str, year: str = None) -> Optional[Dict]:
        """尝试从多个源获取元数据"""
        logger.info(f"获取元数据: {title} ({media_type}, {year})")
        
        # 首先尝试TMDB
        metadata = self._get_from_tmdb(title, media_type, year)
        
        # 如果TMDB失败且启用了回退，尝试豆瓣
        if not metadata and self.fallback_enabled:
            logger.info(f"TMDB失败，尝试豆瓣: {title}")
            metadata = self._get_from_douban(title, media_type)
            
            # 如果从豆瓣获取到数据，尝试映射到标准格式
            if metadata:
                metadata = self._map_douban_to_standard(metadata)
        
        if metadata:
            logger.info(f"成功获取元数据: {title}")
        else:
            logger.warning(f"所有源都无法获取元数据: {title}")
        
        return metadata
    
    def _get_from_tmdb(self, title: str, media_type: str, year: str = None) -> Optional[Dict]:
        """从TMDB获取元数据"""
        try:
            if media_type == 'movie':
                result = self.tmdb_client.search_movie(title, year)
                if result:
                    return {
                        'title': result.get('title') or result.get('original_title', title),
                        'original_title': result.get('original_title', ''),
                        'year': str(result.get('release_date', '')).split('-')[0] if result.get('release_date') else year,
                        'type': 'movie',
                        'tmdb_id': result.get('id'),
                        'overview': result.get('overview', ''),
                        'poster': f"https://image.tmdb.org/t/p/w500{result.get('poster_path', '')}" if result.get('poster_path') else ''
                    }
            
            elif media_type == 'tv':
                result = self.tmdb_client.search_tv(title, year)
                if result:
                    return {
                        'title': result.get('name') or result.get('original_name', title),
                        'original_title': result.get('original_name', ''),
                        'year': str(result.get('first_air_date', '')).split('-')[0] if result.get('first_air_date') else year,
                        'type': 'tv',
                        'tmdb_id': result.get('id'),
                        'overview': result.get('overview', ''),
                        'poster': f"https://image.tmdb.org/t/p/w500{result.get('poster_path', '')}" if result.get('poster_path') else ''
                    }
        
        except Exception as e:
            logger.error(f"TMDB获取元数据失败: {title}, 错误: {str(e)}")
        
        return None
    
    def _get_from_douban(self, title: str, media_type: str) -> Optional[Dict]:
        """从豆瓣获取元数据"""
        try:
            return self.douban_client.search(title, media_type)
        except Exception as e:
            logger.error(f"豆瓣获取元数据失败: {title}, 错误: {str(e)}")
        
        return None
    
    def _map_douban_to_standard(self, douban_data: Dict) -> Dict:
        """将豆瓣数据映射到标准格式"""
        return {
            'title': douban_data.get('title', ''),
            'original_title': douban_data.get('original_title', ''),
            'year': douban_data.get('year', ''),
            'type': 'movie' if douban_data.get('type') == 'movie' else 'tv',
            'douban_id': douban_data.get('id', ''),
            'poster': douban_data.get('cover', '')
        }
    
    def get_episode_metadata(self, tv_id: int, season: int, episode: int) -> Optional[Dict]:
        """获取剧集的详细信息"""
        try:
            result = self.tmdb_client.get_episode_info(tv_id, season, episode)
            if result:
                return {
                    'title': result.get('name', f"第{episode}集"),
                    'season': result.get('season_number', season),
                    'episode': result.get('episode_number', episode),
                    'overview': result.get('overview', ''),
                    'air_date': result.get('air_date', '')
                }
        except Exception as e:
            logger.error(f"获取剧集信息失败: S{season}E{episode}, 错误: {str(e)}")
        
        return None
    
    def get_tmdb_id(self, title: str, media_type: str) -> Optional[int]:
        """获取TMDB ID"""
        return self.tmdb_client.get_tmdb_id(title, media_type)
    
    def update_config(self, config: Dict):
        """更新配置"""
        # 更新TMDB API Key
        tmdb_api_key = config.get('tmdb_api_key') or config.get('TMDB_API_KEY')
        if tmdb_api_key and hasattr(self.tmdb_client, 'api_key'):
            self.tmdb_client.api_key = tmdb_api_key
        
        # 更新豆瓣Cookies
        douban_cookies = config.get('douban_cookies') or config.get('DOUBAN_COOKIES')
        if douban_cookies and hasattr(self.douban_client, '_set_cookies'):
            self.douban_client._set_cookies(douban_cookies)
        
        # 更新回退设置
        if 'fallback_enabled' in config:
            self.fallback_enabled = config['fallback_enabled']
    
    def close(self):
        """关闭所有客户端"""
        if self.tmdb_client:
            self.tmdb_client.close()
        if self.douban_client:
            self.douban_client.close()