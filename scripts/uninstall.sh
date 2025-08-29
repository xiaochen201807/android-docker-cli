#!/bin/sh
# Android Docker CLI 卸载脚本
# 兼容性更好的版本，支持多种shell环境

# 颜色定义（如果支持的话）
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# 打印带颜色的消息
print_info() {
    echo "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo "${RED}[ERROR]${NC} $1"
}

# 检查是否在Termux环境中
check_termux() {
    if [ -d "/data/data/com.termux/files/usr" ]; then
        PREFIX="/data/data/com.termux/files/usr"
        print_info "检测到Termux环境"
        return 0
    else
        print_warning "未检测到Termux环境，将使用标准路径"
        PREFIX="/usr/local"
        return 1
    fi
}

# 检查安装
check_installation() {
    INSTALL_DIR="$HOME/.android-docker-cli"
    DOCKER_CMD="$PREFIX/bin/docker"
    DOCKER_COMPOSE_CMD="$PREFIX/bin/docker-compose"
    
    has_install_dir=false
    has_docker_cmd=false
    has_compose_cmd=false
    
    if [ -d "$INSTALL_DIR" ]; then
        print_info "发现安装目录: $INSTALL_DIR"
        has_install_dir=true
    fi
    
    if [ -f "$DOCKER_CMD" ]; then
        print_info "发现docker命令: $DOCKER_CMD"
        has_docker_cmd=true
    fi
    
    if [ -f "$DOCKER_COMPOSE_CMD" ]; then
        print_info "发现docker-compose命令: $DOCKER_COMPOSE_CMD"
        has_compose_cmd=true
    fi
    
    if [ "$has_install_dir" = "false" ] && [ "$has_docker_cmd" = "false" ] && [ "$has_compose_cmd" = "false" ]; then
        print_warning "未发现Android Docker CLI安装"
        return 1
    fi
    
    return 0
}

# 备份数据
backup_data() {
    INSTALL_DIR="$HOME/.android-docker-cli"
    if [ -d "$INSTALL_DIR" ]; then
        BACKUP_DIR="$HOME/.android-docker-cli-backup-$(date +%Y%m%d-%H%M%S)"
        print_info "创建备份: $BACKUP_DIR"
        if cp -r "$INSTALL_DIR" "$BACKUP_DIR"; then
            print_success "备份完成: $BACKUP_DIR"
        else
            print_warning "备份失败，继续卸载"
        fi
    fi
}

# 卸载命令
uninstall_commands() {
    DOCKER_CMD="$PREFIX/bin/docker"
    DOCKER_COMPOSE_CMD="$PREFIX/bin/docker-compose"
    
    if [ -f "$DOCKER_CMD" ]; then
        print_info "删除docker命令: $DOCKER_CMD"
        if rm -f "$DOCKER_CMD"; then
            print_success "docker命令已删除"
        else
            print_warning "删除docker命令失败，可能需要sudo权限"
        fi
    fi
    
    if [ -f "$DOCKER_COMPOSE_CMD" ]; then
        print_info "删除docker-compose命令: $DOCKER_COMPOSE_CMD"
        if rm -f "$DOCKER_COMPOSE_CMD"; then
            print_success "docker-compose命令已删除"
        else
            print_warning "删除docker-compose命令失败，可能需要sudo权限"
        fi
    fi
}

# 卸载安装目录
uninstall_directory() {
    INSTALL_DIR="$HOME/.android-docker-cli"
    if [ -d "$INSTALL_DIR" ]; then
        print_info "删除安装目录: $INSTALL_DIR"
        if rm -rf "$INSTALL_DIR"; then
            print_success "安装目录已删除"
        else
            print_warning "删除安装目录失败，可能需要手动删除"
        fi
    fi
}

# 清理缓存（可选）
cleanup_cache() {
    CACHE_DIR="$HOME/.docker_proot_cache"
    if [ -d "$CACHE_DIR" ]; then
        print_warning "发现缓存目录: $CACHE_DIR"
        echo "是否删除缓存目录？这将会删除所有下载的镜像和容器数据。"
        printf "输入 'yes' 确认删除: "
        read confirm
        if [ "$confirm" = "yes" ]; then
            if rm -rf "$CACHE_DIR"; then
                print_success "缓存目录已删除"
            else
                print_warning "删除缓存目录失败"
            fi
        else
            print_info "保留缓存目录"
        fi
    fi
}

# 显示卸载摘要
show_summary() {
    print_success "卸载完成！"
    echo
    echo "已删除的内容:"
    echo "- 安装目录: $HOME/.android-docker-cli"
    echo "- 命令: docker, docker-compose"
    echo
    echo "如需恢复，可以从备份目录恢复:"
    echo "cp -r $HOME/.android-docker-cli-backup-* $HOME/.android-docker-cli"
}

# 主函数
main() {
    echo "=========================================="
    echo "    Android Docker CLI 卸载脚本"
    echo "=========================================="
    echo
    
    # 检查环境
    check_termux
    
    # 检查安装
    if ! check_installation; then
        print_info "未发现需要卸载的内容"
        exit 0
    fi
    
    # 确认卸载
    echo
    print_warning "即将卸载Android Docker CLI"
    echo "这将删除以下内容:"
    echo "- 安装目录: $HOME/.android-docker-cli"
    echo "- 命令: docker, docker-compose"
    echo
    printf "确认继续卸载？(y/N): "
    read confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_info "取消卸载"
        exit 0
    fi
    
    # 备份数据
    backup_data
    
    # 卸载命令
    uninstall_commands
    
    # 卸载安装目录
    uninstall_directory
    
    # 清理缓存（可选）
    cleanup_cache
    
    # 显示摘要
    show_summary
    
    echo
    print_success "卸载完成！🎉"
}

# 运行主函数
main "$@"
