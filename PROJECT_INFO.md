# 📋 PlexRename 项目信息

## 🎯 项目状态
- ✅ **开发完成**：所有核心功能已实现
- ✅ **测试通过**：集成测试运行正常
- ✅ **文档齐全**：包含完整的使用说明
- ✅ **部署就绪**：支持多种部署方式

## 📦 核心功能
1. **智能文件重命名**：基于元数据自动重命名媒体文件
2. **硬链接创建**：节省存储空间的文件链接方式
3. **元数据获取**：集成TMDB和豆瓣API
4. **Web界面**：直观的浏览器操作界面
5. **文件监控**：自动监控文件夹变化
6. **批量处理**：支持大规模文件处理

## 🚀 快速启动
```bash
# Windows用户
start.bat

# Linux/macOS用户
./start.sh

# Docker用户
docker-compose up
```

## 📁 项目结构
```
├── app/                    # 核心应用代码
│   ├── core/              # 文件处理核心
│   ├── metadata/          # 元数据获取
│   ├── web/               # Web界面
│   └── config/            # 配置管理
├── tests/                  # 测试代码
├── config/                 # 配置文件
├── data/                   # 数据缓存
├── start.sh & start.bat    # 启动脚本
├── Dockerfile              # Docker配置
└── README.md              # 完整文档
```

## 🔧 技术栈
- **后端**：Python 3.8+
- **Web框架**：Flask + Socket.IO
- **前端**：HTML5 + JavaScript + Bootstrap
- **API**：TMDB API, 豆瓣API
- **部署**：Docker, Docker Compose

## 📋 部署检查清单
- [ ] 安装Python 3.8+
- [ ] 配置环境变量(.env)
- [ ] 安装依赖(pip install -r requirements.txt)
- [ ] 运行测试(python -m tests.test_integration)
- [ ] 启动应用(start.bat/start.sh)

## 🌐 GitHub部署
查看以下文件获取详细部署指南：
- `QUICK_DEPLOY.md` - 快速部署指南
- `GITHUB_DEPLOY_GUIDE.md` - 完整GitHub部署说明
- `deploy_to_github.bat/.ps1` - 一键部署脚本

## 📞 支持
- 查看README.md获取完整使用说明
- 运行集成测试验证功能
- 通过GitHub Issues获取帮助

---
**🎉 项目已准备就绪，可以部署到GitHub了！**