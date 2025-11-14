# GitHub 部署指南

## 准备工作

### 1. 安装Git
如果尚未安装Git，请先安装：
- Windows: 下载并安装 [Git for Windows](https://git-scm.com/download/win)
- macOS: `brew install git`
- Linux: `sudo apt-get install git`

### 2. 创建GitHub账号
如果还没有GitHub账号，请先注册：[https://github.com/join](https://github.com/join)

### 3. 创建新仓库
1. 登录GitHub
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 输入仓库名称，例如 "plexrename"
4. 选择公开(Public)或私有(Private)
5. 不要初始化仓库(不要勾选 "Initialize this repository with a README")
6. 点击 "Create repository"

## 本地Git配置

### 1. 配置Git用户信息
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

### 2. 生成SSH密钥（推荐）
```bash
ssh-keygen -t ed25519 -C "你的邮箱@example.com"
```
按提示操作，将生成的公钥添加到GitHub账户。

## 项目初始化

### 1. 在项目目录初始化Git
```bash
cd h:/python/plexrename
git init
```

### 2. 添加所有文件到Git
```bash
git add .
```

### 3. 提交初始版本
```bash
git commit -m "Initial commit: PlexRename - Media file renaming tool"
```

### 4. 关联远程仓库
```bash
git remote add origin https://github.com/你的用户名/plexrename.git
```

### 5. 推送到GitHub
```bash
git push -u origin master
```

## 快速部署命令汇总

以下是完整的部署命令序列：

```bash
# 1. 进入项目目录
cd h:/python/plexrename

# 2. 初始化Git仓库
git init

# 3. 添加文件（.gitignore会自动生效）
git add .

# 4. 提交更改
git commit -m "Initial commit: PlexRename - Media file renaming tool"

# 5. 关联远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/plexrename.git

# 6. 推送到GitHub
git push -u origin master
```

## 后续更新

每次更新项目后，使用以下命令推送到GitHub：

```bash
# 查看状态
git status

# 添加修改的文件
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到GitHub
git push
```

## 常见问题

### 1. 认证失败
如果使用HTTPS方式推送失败，可以尝试：
- 使用SSH方式：将远程地址改为SSH格式
- 使用GitHub Token：在GitHub设置中生成Personal Access Token

### 2. 大文件问题
GitHub对文件大小有限制（100MB），大文件需要使用Git LFS：
```bash
# 安装Git LFS
git lfs install

# 跟踪大文件类型
git lfs track "*.zip"
git lfs track "*.exe"

# 添加.gitattributes文件
git add .gitattributes
```

### 3. 分支管理
创建新分支进行开发：
```bash
# 创建并切换到新分支
git checkout -b feature/new-feature

# 开发完成后合并到主分支
git checkout master
git merge feature/new-feature
```

## 项目展示优化

### 1. 添加项目描述
在GitHub仓库页面：
- 点击 "About" 部分的齿轮图标
- 添加项目描述、网站链接、主题标签

### 2. 启用GitHub Pages（可选）
如果想创建项目文档网站：
- 进入仓库设置
- 滚动到 "Pages" 部分
- 选择源分支（通常是master）
- 点击保存

### 3. 添加徽章
在README.md中添加徽章：
```markdown
![GitHub release (latest by date)](https://img.shields.io/github/v/release/你的用户名/plexrename)
![GitHub](https://img.shields.io/github/license/你的用户名/plexrename)
![GitHub stars](https://img.shields.io/github/stars/你的用户名/plexrename?style=social)
```

## 安全注意事项

1. **不要提交敏感信息**：
   - API密钥
   - 密码
   - 个人配置文件
   
2. **使用.gitignore**：确保敏感文件被忽略

3. **环境变量**：使用.env文件存储敏感信息（已包含在.gitignore中）

## 获取更多帮助

- [Git官方文档](https://git-scm.com/doc)
- [GitHub帮助文档](https://help.github.com/)
- [GitHub学习实验室](https://lab.github.com/)

祝你部署顺利！🚀