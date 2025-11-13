import re
from typing import Dict, Optional, Tuple


class PatternParser:
    """文件名模式解析器"""
    
    # 定义各种模式的正则表达式
    PATTERNS = {
        # SxxExx 格式 (S01E02)
        'sxxexx': re.compile(r'(?:^|\\W)S(\\d{1,4})E(\\d{1,4})(?:-E(\\d{1,4}))?(?:\\W|$)', re.IGNORECASE),
        # 第x季第x集 中文格式
        'chinese': re.compile(r'(?:^|\\W)第(\\d{1,4})季.*?第(\\d{1,4})集(?:.*?第(\\d{1,4})集)?(?:\\W|$)', re.IGNORECASE),
        # E01-E03 无季数格式 (默认第1季)
        'ep_only': re.compile(r'(?:^|\\W)E(\\d{1,4})(?:-E(\\d{1,4}))?(?:\\W|$)', re.IGNORECASE),
        # 电影年份格式
        'movie_year': re.compile(r'(?:^|\\W)(?:19|20)\\d{2}(?:\\W|$)'),
    }
    
    @classmethod
    def parse(cls, filename: str) -> Dict:
        """解析文件名，提取媒体信息"""
        result = {
            'type': None,  # 'tv', 'movie', 'unknown'
            'season': None,
            'episode': None,
            'end_episode': None,
            'year': None,
            'title': None
        }
        
        # 尝试解析电视剧模式
        if cls._parse_tv_pattern(filename, result):
            result['type'] = 'tv'
        # 检查电影模式（有年份但没有剧集信息）
        elif result['type'] is None and cls.PATTERNS['movie_year'].search(filename):
            result['type'] = 'movie'
            # 提取年份
            year_match = cls.PATTERNS['movie_year'].search(filename)
            if year_match:
                result['year'] = year_match.group(0).strip()
        else:
            result['type'] = 'unknown'
        
        # 尝试提取标题
        result['title'] = cls._extract_title(filename, result)
        
        return result
    
    @classmethod
    def _parse_tv_pattern(cls, filename: str, result: Dict) -> bool:
        """解析电视剧相关模式"""
        # 尝试SxxExx格式
        match = cls.PATTERNS['sxxexx'].search(filename)
        if match:
            result['season'] = int(match.group(1))
            result['episode'] = int(match.group(2))
            if match.group(3):
                result['end_episode'] = int(match.group(3))
            return True
        
        # 尝试中文格式
        match = cls.PATTERNS['chinese'].search(filename)
        if match:
            result['season'] = int(match.group(1))
            result['episode'] = int(match.group(2))
            if match.group(3):
                result['end_episode'] = int(match.group(3))
            return True
        
        # 尝试仅集数格式（默认第1季）
        match = cls.PATTERNS['ep_only'].search(filename)
        if match:
            result['season'] = 1
            result['episode'] = int(match.group(1))
            if match.group(2):
                result['end_episode'] = int(match.group(2))
            return True
        
        return False
    
    @classmethod
    def _extract_title(cls, filename: str, parsed_info: Dict) -> str:
        """从文件名中提取标题"""
        # 移除非标题部分
        title = filename
        
        # 移除文件扩展名
        if '.' in title:
            title = title.rsplit('.', 1)[0]
        
        # 移除已知的模式
        if parsed_info['type'] == 'tv':
            # 移除SxxExx模式
            title = cls.PATTERNS['sxxexx'].sub('', title, re.IGNORECASE)
            # 移除中文格式
            title = cls.PATTERNS['chinese'].sub('', title, re.IGNORECASE)
            # 移除仅集数格式
            title = cls.PATTERNS['ep_only'].sub('', title, re.IGNORECASE)
        elif parsed_info['type'] == 'movie':
            # 移除年份
            title = cls.PATTERNS['movie_year'].sub('', title)
        
        # 清理多余字符
        title = re.sub(r'[._-]', ' ', title)
        title = re.sub(r'\\s+', ' ', title)
        title = title.strip()
        
        return title
    
    @staticmethod
    def format_plex_name(media_info: Dict, original_name: str) -> str:
        """根据Plex命名规范格式化文件名"""
        base_name = media_info.get('title', 'Unknown')
        ext = original_name.rsplit('.', 1)[1] if '.' in original_name else ''
        
        if media_info['type'] == 'tv' and media_info['season'] and media_info['episode']:
            season_str = f"Season {media_info['season']:02d}"
            if media_info['end_episode'] and media_info['end_episode'] != media_info['episode']:
                episode_str = f"E{media_info['episode']:02d}-E{media_info['end_episode']:02d}"
            else:
                episode_str = f"E{media_info['episode']:02d}"
            return f"{base_name} - {season_str} {episode_str}.{ext}"
        elif media_info['type'] == 'movie' and media_info['year']:
            return f"{base_name} ({media_info['year']}).{ext}"
        else:
            # 未知类型，返回清理后的文件名
            return f"{base_name}.{ext}"