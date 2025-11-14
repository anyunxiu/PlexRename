# 🚀 快速部署到GitHub

## 方法1：一键部署（推荐）

### Windows用户

#### 选项A：使用PowerShell脚本（功能最全）
```powershell
# 以管理员身份运行PowerShell
# 执行策略可能需要临时修改
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 运行部署脚本
.\deploy_to_github.ps1
```

#### 选项B：使用批处理脚本
```cmd
# 双击运行或命令行执行
deploy_to_github.bat
```

### 方法2：手动部署（4步完成）

#### 第1步：准备工作
1. **安装Git**（如果尚未安装）
   - 访问：https://git-scm.com/download/win
   - 下载并安装，安装时选择"Git Bash"和"Git GUI"

2. **创建GitHub仓库**
   - 登录：https://github.com
   - 点击右上角 "+" → "New repository"
   - 仓库名：`plexrename`
   - 描述：`Media file renaming tool for Plex`
   - 选择：Public（公开）或Private（私有）
   - **不要**勾选 "Initialize this repository with a README"
   - 点击 "Create repository"

#### 第2步：配置Git
打开命令提示符或Git Bash：
```bash
# 配置用户信息（替换为你的信息）
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

#### 第3步：初始化本地仓库
```bash
# 进入项目目录
cd h:/python/plexrename

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Initial commit: PlexRename - Media file renaming tool"

# 关联远程仓库（替换为你的用户名）
git remote add origin https://github.com/你的用户名/plexrename.git
```

#### 第4步：推送到GitHub
```bash
# 推送到GitHub
git push -u origin master

# 如果提示认证，输入GitHub用户名和密码
# 建议使用Personal Access Token代替密码
```

## 🎯 验证部署成功

1. 访问你的GitHub仓库页面
2. 应该能看到所有项目文件
3. README.md会自动显示在项目首页

## 🔧 后续更新

每次修改项目后，运行以下命令更新GitHub：

```bash
git add .
git commit -m "描述你的更改"
git push
```

## 📋 常见问题快速解决

### 问题1：git命令未找到
**解决**：重启命令提示符或安装Git后重启电脑

### 问题2：认证失败
**解决**：
1. 使用Personal Access Token代替密码
2. 或使用SSH方式（需要配置SSH密钥）

### 问题3：推送被拒绝
**解决**：
```bash
# 强制推送（谨慎使用）
git push -f origin master
```

### 问题4：大文件错误
**解决**：
```bash
# 安装Git LFS
git lfs install
# 跟踪大文件
git lfs track "*.zip"
git add .gitattributes
```

## 🎨 美化你的仓库

### 添加徽章
在README.md顶部添加：
```markdown
![GitHub release (latest by date)](https://img.shields.io/github/v/release/你的用户名/plexrename)
![GitHub](https://img.shields.io/github/license/你的用户名/plexrename)
![GitHub stars](https://img.shields.io/github/stars/你的用户名/plexrename?style=social)
```

### 添加项目主题
在GitHub仓库页面：
1. 点击 "Settings"
2. 滚动到 "Topics"
3. 添加主题标签：`python`, `plex`, `media`, `renaming`, `automation`

## 🚀 高级功能（可选）

### 启用GitHub Pages
1. 进入仓库Settings
2. 滚动到 "Pages"
3. Source选择 "Deploy from a branch"
4. Branch选择 "master" 和 "/ (root)"
5. 点击Save

### 添加工作流（GitHub Actions）
创建 `.github/workflows/python-app.yml` 文件，添加CI/CD流程。

## 📞 获取帮助

- GitHub官方文档：https://docs.github.com/
- Git官方文档：https://git-scm.com/doc
- 项目Issues：在你的仓库中创建Issue

---

**🎉 恭喜！你的PlexRename项目现在已经在GitHub上了！**

现在你可以：
- ✅ 分享项目链接给朋友
- ✅ 在简历中展示
- ✅ 接受其他人的贡献
- ✅ 使用GitHub的Issue跟踪功能
- ✅ 使用GitHub Projects管理开发进度