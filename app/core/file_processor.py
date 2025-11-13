import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
from .pattern_parser import PatternParser

logger = logging.getLogger(__name__)


class FileProcessor:
    """文件处理器，负责硬链接创建和文件重命名"""
    
    def __init__(self, config: Dict):
        """初始化文件处理器"""
        self.config = config
        self.metadata_client = None  # 稍后注入
        self.pattern_parser = PatternParser()
    
    def set_metadata_client(self, client):
        """设置元数据客户端"""
        self.metadata_client = client
    
    def create_hardlink(self, source_path: str, dest_path: str) -> bool:
        """创建硬链接"""
        try:
            # 确保目标目录存在
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # 如果目标文件已存在，先删除
            if os.path.exists(dest_path):
                os.unlink(dest_path)
            
            # 创建硬链接
            os.link(source_path, dest_path)
            logger.info(f"创建硬链接成功: {source_path} -> {dest_path}")
            return True
        except Exception as e:
            logger.error(f"创建硬链接失败: {source_path} -> {dest_path}, 错误: {str(e)}")
            return False
    
    def process_file(self, source_file: str, dest_dir: str) -> Dict:
        """处理单个文件：解析、获取元数据、重命名、创建硬链接"""
        result = {
            'success': False,
            'source': source_file,
            'destination': None,
            'message': None,
            'redo_command': None
        }
        
        try:
            # 解析文件名模式
            filename = os.path.basename(source_file)
            parsed_info = self.pattern_parser.parse(filename)
            
            # 获取元数据（如果有客户端）
            metadata = None
            if self.metadata_client:
                metadata = self.metadata_client.get_metadata(
                    parsed_info['title'],
                    parsed_info['type'],
                    year=parsed_info.get('year')
                )
            
            # 使用元数据增强信息（如果有）
            if metadata:
                if parsed_info['type'] == 'tv' and 'season' in metadata and 'episode' in metadata:
                    parsed_info['season'] = metadata['season']
                    parsed_info['episode'] = metadata['episode']
                if 'title' in metadata:
                    parsed_info['title'] = metadata['title']
                if 'year' in metadata:
                    parsed_info['year'] = metadata['year']
            
            # 生成Plex格式的新文件名
            new_filename = self.pattern_parser.format_plex_name(parsed_info, filename)
            
            # 确定目标路径
            if parsed_info['type'] == 'tv' and parsed_info['season']:
                season_dir = f"Season {parsed_info['season']:02d}"
                dest_path = os.path.join(dest_dir, parsed_info['title'], season_dir, new_filename)
            else:
                dest_path = os.path.join(dest_dir, parsed_info['title'], new_filename)
            
            # 创建硬链接
            if self.create_hardlink(source_file, dest_path):
                result['success'] = True
                result['destination'] = dest_path
                result['message'] = f"成功处理文件: {filename} -> {new_filename}"
            else:
                result['message'] = "创建硬链接失败"
                # 生成重做命令
                result['redo_command'] = f"/redo {source_file} {dest_dir}"
        
        except Exception as e:
            logger.error(f"处理文件失败: {source_file}, 错误: {str(e)}")
            result['message'] = f"处理失败: {str(e)}"
            result['redo_command'] = f"/redo {source_file} {dest_dir}"
        
        return result
    
    def batch_process(self, source_dir: str, dest_dir: str, extensions: List[str] = None) -> List[Dict]:
        """批量处理目录中的文件"""
        results = []
        
        # 默认处理视频文件
        if extensions is None:
            extensions = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        
        try:
            # 遍历源目录中的所有文件
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    # 检查文件扩展名
                    ext = os.path.splitext(file)[1].lower()
                    if ext in extensions:
                        source_file = os.path.join(root, file)
                        result = self.process_file(source_file, dest_dir)
                        results.append(result)
        
        except Exception as e:
            logger.error(f"批量处理失败: {str(e)}")
            results.append({
                'success': False,
                'source': source_dir,
                'destination': None,
                'message': f"批量处理异常: {str(e)}",
                'redo_command': None
            })
        
        return results
    
    def compare_and_process(self, source_dir: str, dest_dir: str) -> List[Dict]:
        """比较源目录和目标目录，处理缺失的文件"""
        results = []
        
        try:
            # 获取源目录中所有文件的相对路径
            source_files = {}
            for root, _, files in os.walk(source_dir):
                for file in files:
                    source_path = os.path.join(root, file)
                    relative_path = os.path.relpath(source_path, source_dir)
                    source_files[relative_path] = source_path
            
            # 获取目标目录中所有文件的相对路径
            dest_files = set()
            for root, _, files in os.walk(dest_dir):
                for file in files:
                    dest_path = os.path.join(root, file)
                    # 只考虑硬链接目标
                    if os.path.exists(dest_path):
                        dest_files.add(file)
            
            # 处理缺失的文件
            for relative_path, source_path in source_files.items():
                source_filename = os.path.basename(source_path)
                # 检查文件名（不包括路径）是否在目标中
                if source_filename not in dest_files:
                    result = self.process_file(source_path, dest_dir)
                    results.append(result)
        
        except Exception as e:
            logger.error(f"比较处理失败: {str(e)}")
            results.append({
                'success': False,
                'source': source_dir,
                'destination': dest_dir,
                'message': f"比较处理异常: {str(e)}",
                'redo_command': None
            })
        
        return results
    
    def process_redo_command(self, redo_command: str) -> Dict:
        """处理重做命令"""
        try:
            # 解析重做命令
            parts = redo_command.strip().split(' ')
            if len(parts) >= 3 and parts[0] == '/redo':
                source_file = parts[1]
                dest_dir = ' '.join(parts[2:])
                
                # 重新处理文件
                return self.process_file(source_file, dest_dir)
            else:
                return {
                    'success': False,
                    'message': '重做命令格式错误'
                }
        except Exception as e:
            logger.error(f"处理重做命令失败: {redo_command}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f"重做命令处理失败: {str(e)}"
            }