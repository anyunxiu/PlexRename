import os
import json
import logging
import requests
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DoubanClient:
    """豆瓣API客户端"""
    
    SEARCH_URL = 'https://movie.douban.com/j/subject_suggest?q='
    DETAIL_URL = 'https://movie.douban.com/subject/'
    
    def __init__(self, cookies: str = None, cache_dir: str = './data/douban_cache'):
        """初始化豆瓣客户端"""
        self.cookies = cookies or os.environ.get('DOUBAN_COOKIES')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://movie.douban.com/'
        })
        
        # 设置cookies
        if self.cookies:
            self._set_cookies(self.cookies)
    
    def _set_cookies(self, cookies_str: str):
        """设置cookies"""
        try:
            # 解析cookies字符串
            cookies = {}
            for cookie in cookies_str.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
            
            # 设置到session
            for key, value in cookies.items():
                self.session.cookies.set(key, value, domain='.douban.com')
                
        except Exception as e:
            logger.error(f"设置Cookies失败: {str(e)}")
    
    def search(self, title: str, media_type: str = None) -> Optional[Dict]:
        """搜索电影或电视剧"""
        # 检查缓存
        cache_key = f"{media_type or 'all'}_{title}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"从缓存获取豆瓣信息: {title}")
            return cached
        
        try:
            # 发送搜索请求
            response = self.session.get(f"{self.SEARCH_URL}{requests.utils.quote(title)}", timeout=10)
            response.raise_for_status()
            
            results = response.json()
            if not results:
                logger.info(f"豆瓣未找到: {title}")
                return None
            
            # 选择最匹配的结果
            # 优先匹配类型
            if media_type == 'movie':
                target = next((r for r in results if r.get('type') == 'movie'), None)
            elif media_type == 'tv':
                target = next((r for r in results if r.get('type') == 'tv'), None)
            else:
                target = results[0]
            
            if target:
                # 获取详细信息（简化版）
                # 注意：完整的豆瓣API需要认证，这里只返回搜索结果中的信息
                metadata = {
                    'title': target.get('title', title),
                    'original_title': target.get('original_title', ''),
                    'year': target.get('year', ''),
                    'type': target.get('type', 'unknown'),
                    'id': target.get('id', ''),
                    'cover': target.get('img', '')
                }
                
                # 保存到缓存
                self._save_to_cache(cache_key, metadata)
                return metadata
            
        except requests.RequestException as e:
            logger.error(f"豆瓣搜索失败: {title}, 错误: {str(e)}")
        except Exception as e:
            logger.error(f"豆瓣搜索处理失败: {title}, 错误: {str(e)}")
        
        return None
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        try:
            cache_file = self.cache_dir / f"{key.replace('/', '_')}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"读取豆瓣缓存失败: {key}, 错误: {str(e)}")
        return None
    
    def _save_to_cache(self, key: str, data: Dict):
        """保存数据到缓存"""
        try:
            cache_file = self.cache_dir / f"{key.replace('/', '_')}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存豆瓣缓存失败: {key}, 错误: {str(e)}")
    
    def close(self):
        """关闭会话"""
        self.session.close()