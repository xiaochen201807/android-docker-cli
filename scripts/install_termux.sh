#!/bin/sh
# Android Docker CLI Termux安装脚本
# 专门为Termux环境优化

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
        print_info "发现Python3: $(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
        print_info "发现Python: $(command -v python)"
    else
        print_error "未找到Python，请先安装Python 3.6+"
        exit 1
    fi
    
    # 检查proot
    if command -v proot >/dev/null 2>&1; then
        print_info "发现proot: $(command -v proot)"
    else
        print_warning "未找到proot，请先安装proot"
        print_info "运行: pkg install proot"
        exit 1
    fi
    
    # 检查curl
    if command -v curl >/dev/null 2>&1; then
        print_info "发现curl: $(command -v curl)"
    else
        print_warning "未找到curl，请先安装curl"
        print_info "运行: pkg install curl"
        exit 1
    fi
    
    # 检查tar
    if command -v tar >/dev/null 2>&1; then
        print_info "发现tar: $(command -v tar)"
    else
        print_warning "未找到tar，请先安装tar"
        print_info "运行: pkg install tar"
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
    
    # 获取当前工作目录
    CURRENT_DIR="$(pwd)"
    DOCKER_CLI_PATH="$CURRENT_DIR/android_docker/docker_cli.py"
    
    if [ ! -f "$DOCKER_CLI_PATH" ]; then
        print_error "未找到docker_cli.py文件: $DOCKER_CLI_PATH"
        print_info "请确保在项目根目录运行此脚本"
        exit 1
    fi
    
    # 创建可执行权限
    chmod +x "$DOCKER_CLI_PATH"
    
    # 在Termux中创建命令链接
    TERMUX_BIN="$PREFIX/bin"
    DOCKER_LINK="$TERMUX_BIN/docker"
    
    if [ -w "$TERMUX_BIN" ]; then
        ln -sf "$DOCKER_CLI_PATH" "$DOCKER_LINK"
        print_success "已创建docker命令链接: $DOCKER_LINK"
    else
        print_warning "无法写入 $TERMUX_BIN，尝试创建用户级链接"
        
        # 创建用户级链接
        USER_BIN="$HOME/.local/bin"
        mkdir -p "$USER_BIN"
        ln -sf "$DOCKER_CLI_PATH" "$USER_BIN/docker"
        
        # 添加到PATH
        if ! echo "$PATH" | grep -q "$USER_BIN"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            print_info "已将 ~/.local/bin 添加到PATH环境变量"
            print_warning "请运行 'source ~/.bashrc' 使PATH生效"
        fi
        
        print_success "已创建用户级docker命令链接: $USER_BIN/docker"
    fi
}

# 测试安装
test_installation() {
    print_info "测试安装..."
    
    if command -v docker >/dev/null 2>&1; then
        if docker --help >/dev/null 2>&1; then
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
    echo "    Android Docker CLI Termux安装脚本"
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
