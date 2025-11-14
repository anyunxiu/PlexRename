# PlexRename

一个强大的媒体文件重命名工具，专为Plex媒体服务器设计，支持文件名解析、元数据获取、文件重命名和硬链接创建，帮助您自动整理媒体库。

## 功能特性

- **智能文件名解析**：自动从文件名中提取电影/剧集信息
- **媒体元数据获取**：支持从TMDB和豆瓣获取详细元数据
- **批量重命名**：支持批量处理多个媒体文件
- **硬链接创建**：可以创建硬链接而不复制文件内容，节省存储空间
- **文件监控**：监控文件夹变化，自动处理新增文件
- **Web UI**：提供直观的Web界面进行操作
- **命令行支持**：支持通过命令行批量处理文件
- **配置管理**：灵活的配置系统，支持自定义规则和路径

## 快速开始

### 方法一：直接运行

1. 确保已安装Python 3.8或更高版本
2. 克隆项目并进入目录：
   ```bash
   git clone https://github.com/yourusername/plexrename.git
   cd plexrename
   ```
3. 运行启动脚本：
   - Linux/macOS:
     ```bash
     chmod +x start.sh
     ./start.sh
     ```
   - Windows:
     ```cmd
     start.bat
     ```

### 方法二：使用Docker

1. 确保已安装Docker和docker-compose
2. 克隆项目并进入目录：
   ```bash
   git clone https://github.com/yourusername/plexrename.git
   cd plexrename
   ```
3. 运行启动脚本（指定Docker模式）：
   - Linux/macOS:
     ```bash
     chmod +x start.sh
     ./start.sh --docker
     ```
   - Windows:
     ```cmd
     start.bat --docker
     ```

## 配置说明

1. 复制`.env.example`为`.env`并根据需要修改配置：
   ```bash
   cp .env.example .env
   # 编辑.env文件
   ```

2. 主要配置项：
   - `PORT`: Web UI端口
   - `TMDB_API_KEY`: TMDB API密钥（可选，但强烈建议配置以获得更好的元数据）
   - `DEFAULT_LIBRARY_PATH`: 默认媒体库路径
   - `USE_HARDLINKS`: 是否使用硬链接模式

## 使用指南

### Web UI

启动应用后，可以通过浏览器访问`http://localhost:5000`打开Web界面：

1. **文件重命名**：上传文件或选择文件夹，设置规则后批量重命名
2. **硬链接创建**：选择源文件和目标文件夹，创建硬链接
3. **监控配置**：设置监控文件夹，自动处理新增文件
4. **元数据查询**：手动查询和编辑媒体元数据

### 命令行使用

```bash
# 基本用法
python -m app.cli --input /path/to/media --output /path/to/library

# 使用硬链接模式
python -m app.cli --input /path/to/media --output /path/to/library --hardlink

# 批量重命名模式
python -m app.cli --input /path/to/media --rename --pattern "{title} ({year})"

# 监控模式
python -m app.cli --watch /path/to/watch --output /path/to/library
```

## 目录结构

```
├── app/                   # 应用主目录
│   ├── main.py            # 应用入口
│   ├── cli.py             # 命令行接口
│   ├── core/              # 核心功能模块
│   ├── web/               # Web UI相关代码
│   ├── metadata/          # 元数据获取模块
│   ├── config/            # 配置管理
│   └── utils/             # 工具函数
├── config/                # 配置文件目录
├── data/                  # 数据和缓存目录
├── redo/                  # 重做命令记录
├── tests/                 # 测试代码
├── .env.example           # 环境变量示例
├── requirements.txt       # 依赖列表
├── Dockerfile             # Docker构建文件
├── docker-compose.yml     # Docker Compose配置
├── start.sh               # Linux启动脚本
└── start.bat              # Windows启动脚本
```

## 依赖说明

主要依赖项在`requirements.txt`文件中定义，包括：

- Flask：Web框架
- Flask-SocketIO：WebSocket支持
- requests：HTTP请求
- watchdog：文件监控
- pydantic：数据验证
- python-dotenv：环境变量管理

## 注意事项

1. **硬链接限制**：硬链接只能在同一文件系统内创建，请确保源文件和目标目录位于同一磁盘分区
2. **API限制**：使用TMDB API时请注意调用频率限制
3. **权限问题**：确保应用程序有足够的权限读写相关目录
4. **Docker卷挂载**：使用Docker时，请正确配置卷挂载以确保数据持久化

## 故障排除

### 常见问题

1. **无法创建硬链接**：
   - 检查源文件和目标目录是否在同一文件系统
   - 检查权限是否足够

2. **元数据获取失败**：
   - 确保网络连接正常
   - 检查TMDB API密钥是否正确
   - 尝试提供更准确的文件名

3. **Docker容器无法访问文件**：
   - 检查卷挂载配置是否正确
   - 检查文件权限

## 开发说明

### 运行测试

```bash
# 运行单元测试
python -m unittest discover tests

# 运行集成测试
python -m tests.test_integration
```

### 贡献代码

欢迎提交Issue和Pull Request！

## 许可证

[MIT License](LICENSE)