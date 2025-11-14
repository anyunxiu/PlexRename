@echo off
echo ========================================
echo        PlexRename GitHub 部署工具     
echo ========================================

REM 检查Git是否安装
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Git，请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM 获取用户输入
set /p GITHUB_USERNAME="请输入GitHub用户名: "
set /p REPO_NAME="请输入仓库名称(默认: plexrename): "
if "%REPO_NAME%"=="" set REPO_NAME=plexrename
set /p REPO_DESC="请输入仓库描述: "

REM 设置远程仓库地址
set REMOTE_URL=https://github.com/anyunxiu/PlexRename/%REPO_NAME%.git

echo.
echo 正在初始化Git仓库...
git init

echo.
echo 正在添加文件到Git...
git add .

echo.
echo 正在提交更改...
git commit -m "Initial commit: PlexRename - Media file renaming tool"

echo.
echo 正在关联远程仓库...
git remote add origin %REMOTE_URL%

echo.
echo 正在推送到GitHub...
git push -u origin master

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo     部署成功！🎉
    echo ========================================
    echo 仓库地址: %REMOTE_URL%
    echo 请访问GitHub查看你的项目
) else (
    echo.
    echo ========================================
    echo     部署失败！❌
    echo ========================================
    echo 可能的原因：
    echo 1. GitHub仓库尚未创建
    echo 2. 网络连接问题
    echo 3. 认证失败
    echo.
    echo 请手动创建仓库后重试，或使用以下命令：
    echo git push -u origin master
)

pause