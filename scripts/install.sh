#!/bin/bash

# Android Docker CLI 安装脚本
# 基于proot的Docker风格容器管理工具

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "未找到Python，请先安装Python 3.6+"
        exit 1
    fi
    
    # 检查proot
    if command -v proot >/dev/null 2>&1; then
        print_info "发现proot: $(command -v proot)"
    else
        print_warning "未找到proot，请先安装proot"
        print_info "Android Termux: pkg install proot"
        print_info "Ubuntu/Debian: sudo apt install proot"
        exit 1
    fi
    
    # 检查curl
    if command -v curl >/dev/null 2>&1; then
        print_info "发现curl: $(command -v curl)"
    else
        print_warning "未找到curl，请先安装curl"
        print_info "Android Termux: pkg install curl"
        print_info "Ubuntu/Debian: sudo apt install curl"
        exit 1
    fi
    
    # 检查tar
    if command -v tar >/dev/null 2>&1; then
        print_info "发现tar: $(command -v tar)"
    else
        print_warning "未找到tar，请先安装tar"
        print_info "Android Termux: pkg install tar"
        exit 1
    fi
    
    print_success "系统依赖检查完成"
}

# 安装Python依赖
install_python_deps() {
    print_info "安装Python依赖..."
    
    if [ -f "requirements.txt" ]; then
        $PYTHON_CMD -m pip install -r requirements.txt
        print_success "Python依赖安装完成"
    else
        print_warning "未找到requirements.txt，跳过Python依赖安装"
    fi
}

# 创建docker命令链接
create_docker_symlink() {
    print_info "创建docker命令链接..."
    
    # 获取脚本所在目录的绝对路径
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    DOCKER_CLI_PATH="$PROJECT_DIR/android_docker/docker_cli.py"
    
    if [ ! -f "$DOCKER_CLI_PATH" ]; then
        print_error "未找到docker_cli.py文件: $DOCKER_CLI_PATH"
        exit 1
    fi
    
    # 创建可执行权限
    chmod +x "$DOCKER_CLI_PATH"
    
    # 尝试创建系统级链接
    if command -v sudo &> /dev/null; then
        sudo ln -sf "$DOCKER_CLI_PATH" /usr/local/bin/docker
        print_success "已创建系统级docker命令链接"
    else
        # 如果没有sudo权限，创建用户级链接
        USER_BIN="$HOME/.local/bin"
        mkdir -p "$USER_BIN"
        ln -sf "$DOCKER_CLI_PATH" "$USER_BIN/docker"
        
        # 添加到PATH
        if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
            print_info "已将 ~/.local/bin 添加到PATH环境变量"
            print_warning "请重新登录或运行 'source ~/.bashrc' 使PATH生效"
        fi
        
        print_success "已创建用户级docker命令链接: $USER_BIN/docker"
    fi
}

# 测试安装
test_installation() {
    print_info "测试安装..."
    
    if command -v docker &> /dev/null; then
        docker --help > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_success "安装测试成功！"
            print_info "现在可以使用 'docker --help' 查看帮助信息"
        else
            print_error "安装测试失败"
            exit 1
        fi
    else
        print_error "docker命令未找到，安装可能失败"
        exit 1
    fi
}

# 显示使用说明
show_usage() {
    print_info "安装完成！使用说明："
    echo
    echo "1. 查看帮助信息："
    echo "   docker --help"
    echo
    echo "2. 拉取镜像："
    echo "   docker pull alpine:latest"
    echo
    echo "3. 运行容器："
    echo "   docker run alpine:latest echo 'Hello World'"
    echo
    echo "4. 查看容器："
    echo "   docker ps"
    echo
    echo "5. 登录镜像仓库："
    echo "   docker login"
    echo
    print_info "更多功能请查看项目文档"
}

# 主函数
main() {
    echo "=========================================="
    echo "    Android Docker CLI 安装脚本"
    echo "=========================================="
    echo
    
    check_dependencies
    install_python_deps
    create_docker_symlink
    test_installation
    show_usage
    
    echo
    print_success "安装完成！🎉"
}

# 运行主函数
main "$@"
