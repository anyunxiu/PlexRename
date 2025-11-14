# PlexRename GitHub 部署脚本 (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "        PlexRename GitHub 部署工具     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查Git是否安装
function Test-Git {
    try {
        git --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

# 检查GitHub CLI是否安装
function Test-GitHubCLI {
    try {
        gh --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

# 创建GitHub仓库
function New-GitHubRepository {
    param(
        [string]$RepoName,
        [string]$Description,
        [bool]$Private = $false
    )
    
    $privateFlag = if ($Private) { "--private" } else { "--public" }
    $descriptionFlag = if ($Description) { "--description `"$Description`"" } else { "" }
    
    try {
        $command = "gh repo create $RepoName $privateFlag $descriptionFlag --confirm"
        Invoke-Expression $command
        return $true
    } catch {
        Write-Host "创建仓库失败: $_" -ForegroundColor Red
        return $false
    }
}

# 主函数
function Main {
    # 检查Git
    if (-not (Test-Git)) {
        Write-Host "错误: 未找到Git，请先安装Git" -ForegroundColor Red
        Write-Host "下载地址: https://git-scm.com/download/win" -ForegroundColor Yellow
        return
    }
    
    Write-Host "✓ Git 已安装" -ForegroundColor Green
    
    # 获取用户信息
    $GitHubUsername = Read-Host "请输入GitHub用户名"
    $RepoName = Read-Host "请输入仓库名称(默认: plexrename)"
    if ([string]::IsNullOrEmpty($RepoName)) {
        $RepoName = "plexrename"
    }
    
    $RepoDesc = Read-Host "请输入仓库描述(可选)"
    $IsPrivate = Read-Host "是否创建私有仓库? (y/N)"
    $CreateRepo = Read-Host "是否自动创建GitHub仓库? (需要GitHub CLI) (y/N)"
    
    # 创建仓库
    if ($CreateRepo -eq "y" -or $CreateRepo -eq "Y") {
        if (Test-GitHubCLI) {
            Write-Host "正在创建GitHub仓库..." -ForegroundColor Yellow
            $private = $IsPrivate -eq "y" -or $IsPrivate -eq "Y"
            if (New-GitHubRepository -RepoName $RepoName -Description $RepoDesc -Private $private) {
                Write-Host "✓ GitHub仓库创建成功" -ForegroundColor Green
            }
        } else {
            Write-Host "警告: 未找到GitHub CLI，请手动创建仓库" -ForegroundColor Yellow
            Write-Host "访问: https://github.com/new" -ForegroundColor Cyan
            Read-Host "创建完成后按Enter继续"
        }
    }
    
    Write-Host "`n正在初始化Git仓库..." -ForegroundColor Yellow
    git init
    
    Write-Host "`n正在添加文件到Git..." -ForegroundColor Yellow
    git add .
    
    Write-Host "`n正在提交更改..." -ForegroundColor Yellow
    git commit -m "Initial commit: PlexRename - Media file renaming tool"
    
    $RemoteUrl = "https://github.com/anyunxiu/PlexRename/$RepoName.git"
    Write-Host "`n正在关联远程仓库: $RemoteUrl" -ForegroundColor Yellow
    git remote add origin $RemoteUrl
    
    Write-Host "`n正在推送到GitHub..." -ForegroundColor Yellow
    
    try {
        git push -u origin master
        Write-Host "`n========================================" -ForegroundColor Green
        Write-Host "        部署成功！🎉" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "仓库地址: $RemoteUrl" -ForegroundColor Cyan
        Write-Host "请访问GitHub查看你的项目" -ForegroundColor Cyan
    } catch {
        Write-Host "`n========================================" -ForegroundColor Red
        Write-Host "        部署失败！❌" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "可能的原因：" -ForegroundColor Yellow
        Write-Host "1. GitHub仓库尚未创建" -ForegroundColor Yellow
        Write-Host "2. 网络连接问题" -ForegroundColor Yellow
        Write-Host "3. 认证失败" -ForegroundColor Yellow
        Write-Host "`n请手动执行以下命令：" -ForegroundColor Cyan
        Write-Host "git push -u origin master" -ForegroundColor Cyan
    }
}

# 运行主函数
Main

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")