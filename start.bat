echo off

REM PlexRename Windows启动脚本
REM 支持直接运行或通过Docker运行

cls
echo ========================================
echo          PlexRename 启动脚本           
echo ========================================

REM 检查Python环境
:check_python
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查Python版本
for /f "tokens=2 delims=." %%i in ('python --version 2^>^&1') do (
    set PYTHON_VERSION=%%i
)
if %PYTHON_VERSION% lss 8 (
    echo 警告: Python版本过低(3.%PYTHON_VERSION%)，建议使用Python 3.8或更高版本
)

goto :end_check_python

:end_check_python

REM 检查并安装依赖
:install_deps
echo 正在检查依赖...
if exist "requirements.txt" (
    echo 正在安装依赖包...
    python -m pip install -r requirements.txt --upgrade
    if %errorlevel% neq 0 (
        echo 警告: 依赖安装失败，可能会影响部分功能
    )
) else (
    echo 警告: 未找到requirements.txt文件
)

goto :end_install_deps

:end_install_deps

REM 直接运行模式
:run_directly
echo 正在以直接运行模式启动...

REM 检查.env文件
if not exist ".env" (
    echo 警告: 未找到.env文件，将使用默认配置
    if exist ".env.example" (
        echo 正在从.env.example创建.env文件...
        copy .env.example .env
    )
)

echo 正在启动应用...
python -m app.main
goto :end_run_directly

:end_run_directly

REM Docker运行模式
:run_docker
echo 正在以Docker模式启动...

REM 检查Docker是否安装
docker --version >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Docker，请先安装Docker
    pause
    exit /b 1
)

REM 检查docker-compose是否安装
docker-compose --version >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到docker-compose，请先安装docker-compose
    pause
    exit /b 1
)

REM 检查.env文件
if not exist ".env" (
    echo 警告: 未找到.env文件，将使用默认配置
    if exist ".env.example" (
        echo 正在从.env.example创建.env文件...
        copy .env.example .env
    )
)

echo 正在构建并启动Docker容器...
docker-compose up --build
goto :end_run_docker

:end_run_docker

REM 显示帮助信息
:show_help
echo 使用方法: %0 [选项]
echo 选项:
echo   -d, --direct     直接在本地运行（默认）
echo   -c, --docker     使用Docker运行
echo   -h, --help       显示此帮助信息
echo.
echo 示例:
echo   %0               # 直接运行
echo   %0 --docker      # 使用Docker运行
goto :end_show_help

:end_show_help

REM 主函数
:main
REM 默认模式
set MODE=direct

REM 解析命令行参数
:parse_args
if "%1" equ "" goto :end_parse_args

if "%1" equ "-d" (set MODE=direct) else if "%1" equ "--direct" (set MODE=direct) else if "%1" equ "-c" (set MODE=docker) else if "%1" equ "--docker" (set MODE=docker) else if "%1" equ "-h" (set MODE=help) else if "%1" equ "--help" (set MODE=help) else (
    echo 错误: 未知选项 '%1'
    call :show_help
    pause
    exit /b 1
)

shift
goto :parse_args

:end_parse_args

REM 根据模式运行
if "%MODE%" equ "direct" (
    call :check_python
    if %errorlevel% equ 0 (
        call :install_deps
        call :run_directly
    )
) else if "%MODE%" equ "docker" (
    call :run_docker
) else if "%MODE%" equ "help" (
    call :show_help
)

:end_main
pause