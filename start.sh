#!/bin/bash

# PlexRename 启动脚本
# 支持直接运行或通过Docker运行

echo "========================================"
echo "         PlexRename 启动脚本           "
echo "========================================"

# 检查Python环境
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        echo "错误: 未找到Python环境，请先安装Python 3.8+"
        return 1
    fi
    
    # 检查Python版本
    VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$VERSION < 3.8" | bc -l) -eq 1 ]]; then
        echo "警告: Python版本过低($VERSION)，建议使用Python 3.8或更高版本"
    fi
    
    return 0
}

# 检查并安装依赖
install_deps() {
    echo "正在检查依赖..."
    if [ -f "requirements.txt" ]; then
        echo "正在安装依赖包..."
        $PYTHON -m pip install -r requirements.txt --upgrade
        if [ $? -ne 0 ]; then
            echo "警告: 依赖安装失败，可能会影响部分功能"
        fi
    else
        echo "警告: 未找到requirements.txt文件"
    fi
}

# 直接运行模式
run_directly() {
    echo "正在以直接运行模式启动..."
    if check_python; then
        install_deps
        
        # 检查.env文件
        if [ ! -f ".env" ]; then
            echo "警告: 未找到.env文件，将使用默认配置"
            if [ -f ".env.example" ]; then
                echo "正在从.env.example创建.env文件..."
                cp .env.example .env
            fi
        fi
        
        echo "正在启动应用..."
        $PYTHON -m app.main
    fi
}

# Docker运行模式
run_docker() {
    echo "正在以Docker模式启动..."
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        echo "错误: 未找到Docker，请先安装Docker"
        return 1
    fi
    
    # 检查docker-compose是否安装
    if ! command -v docker-compose &> /dev/null; then
        echo "错误: 未找到docker-compose，请先安装docker-compose"
        return 1
    fi
    
    # 检查.env文件
    if [ ! -f ".env" ]; then
        echo "警告: 未找到.env文件，将使用默认配置"
        if [ -f ".env.example" ]; then
            echo "正在从.env.example创建.env文件..."
            cp .env.example .env
        fi
    fi
    
    echo "正在构建并启动Docker容器..."
    docker-compose up --build
}

# 显示帮助信息
show_help() {
    echo "使用方法: $0 [选项]"
    echo "选项:"
    echo "  -d, --direct     直接在本地运行（默认）"
    echo "  -c, --docker     使用Docker运行"
    echo "  -h, --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0               # 直接运行"
    echo "  $0 --docker      # 使用Docker运行"
}

# 主函数
main() {
    # 默认模式
    MODE="direct"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--direct)
                MODE="direct"
                shift
                ;;
            -c|--docker)
                MODE="docker"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo "错误: 未知选项 '$1'"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 根据模式运行
    if [ "$MODE" = "direct" ]; then
        run_directly
    elif [ "$MODE" = "docker" ]; then
        run_docker
    fi
}

# 执行主函数
main "$@"