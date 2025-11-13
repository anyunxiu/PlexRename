import os
import json
import logging
import requests
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class TMDBClient:
    """TMDB API客户端"""
    
    BASE_URL = 'https://api.themoviedb.org/3'
    
    def __init__(self, api_key: str = None, cache_dir: str = './data/tmdb_cache'):
        """初始化TMDB客户端"""
        self.api_key = api_key or os.environ.get('TMDB_API_KEY')
        if not self.api_key:
            logger.warning("TMDB API Key 未配置")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发送API请求"""
        if not self.api_key:
            logger.error("无法发送请求：TMDB API Key 未配置")
            return None
        
        url = f"{self.BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        params['language'] = 'zh-CN'  # 默认使用中文
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"TMDB API请求失败: {url}, 错误: {str(e)}")
            return None
    
    def search_movie(self, title: str, year: str = None) -> Optional[Dict]:
        """搜索电影"""
        # 检查缓存
        cache_key = f"movie_{title}_{year}" if year else f"movie_{title}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"从缓存获取电影信息: {title}")
            return cached
        
        params = {'query': title}
        if year:
            params['year'] = year
        
        results = self._make_request('/search/movie', params)
        if results and results.get('results'):
            # 返回第一个结果
            movie = results['results'][0]
            # 获取详细信息
            movie_detail = self._make_request(f"/movie/{movie['id']}")
            if movie_detail:
                # 保存到缓存
                self._save_to_cache(cache_key, movie_detail)
                # 保存TMDB ID到单独的缓存
                self._save_tmdb_id(title, 'movie', movie_detail['id'])
                return movie_detail
        
        return None
    
    def search_tv(self, title: str, year: str = None) -> Optional[Dict]:
        """搜索电视剧"""
        # 检查缓存
        cache_key = f"tv_{title}_{year}" if year else f"tv_{title}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"从缓存获取电视剧信息: {title}")
            return cached
        
        params = {'query': title}
        if year:
            params['first_air_date_year'] = year
        
        results = self._make_request('/search/tv', params)
        if results and results.get('results'):
            # 返回第一个结果
            tv = results['results'][0]
            # 获取详细信息
            tv_detail = self._make_request(f"/tv/{tv['id']}")
            if tv_detail:
                # 保存到缓存
                self._save_to_cache(cache_key, tv_detail)
                # 保存TMDB ID到单独的缓存
                self._save_tmdb_id(title, 'tv', tv_detail['id'])
                return tv_detail
        
        return None
    
    def get_episode_info(self, tv_id: int, season: int, episode: int) -> Optional[Dict]:
        """获取剧集信息"""
        # 检查缓存
        cache_key = f"episode_{tv_id}_S{season:02d}E{episode:02d}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"从缓存获取剧集信息: S{season:02d}E{episode:02d}")
            return cached
        
        episode_info = self._make_request(f"/tv/{tv_id}/season/{season}/episode/{episode}")
        if episode_info:
            self._save_to_cache(cache_key, episode_info)
        return episode_info
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        try:
            cache_file = self.cache_dir / f"{key.replace('/', '_')}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"读取缓存失败: {key}, 错误: {str(e)}")
        return None
    
    def _save_to_cache(self, key: str, data: Dict):
        """保存数据到缓存"""
        try:
            cache_file = self.cache_dir / f"{key.replace('/', '_')}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存失败: {key}, 错误: {str(e)}")
    
    def _save_tmdb_id(self, title: str, media_type: str, tmdb_id: int):
        """保存TMDB ID到本地JSON"""
        try:
            id_file = self.cache_dir / 'tmdb_ids.json'
            
            # 读取现有数据
            ids = {}
            if id_file.exists():
                with open(id_file, 'r', encoding='utf-8') as f:
                    ids = json.load(f)
            
            # 更新或添加ID
            if media_type not in ids:
                ids[media_type] = {}
            ids[media_type][title] = tmdb_id
            
            # 保存回文件
            with open(id_file, 'w', encoding='utf-8') as f:
                json.dump(ids, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存TMDB ID失败: {title}, 错误: {str(e)}")
    
    def get_tmdb_id(self, title: str, media_type: str) -> Optional[int]:
        """从本地JSON获取TMDB ID"""
        try:
            id_file = self.cache_dir / 'tmdb_ids.json'
            if id_file.exists():
                with open(id_file, 'r', encoding='utf-8') as f:
                    ids = json.load(f)
                    if media_type in ids and title in ids[media_type]:
                        return ids[media_type][title]
        except Exception as e:
            logger.error(f"读取TMDB ID失败: {title}, 错误: {str(e)}")
        return None
    
    def close(self):
        """关闭会话"""
        self.session.close()