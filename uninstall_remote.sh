#!/bin/bash
# 远程安装卸载脚本
# 安全地卸载通过远程安装脚本安装的android-docker-cli

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

# 检查是否在Termux环境中
check_termux() {
    if [ -d "/data/data/com.termux/files/usr" ]; then
        PREFIX="/data/data/com.termux/files/usr"
        return 0
    else
        print_warning "未检测到Termux环境，将使用标准路径"
        PREFIX="/usr/local"
        return 1
    fi
}

# 检查远程安装
check_remote_installation() {
    REMOTE_DIR="$HOME/.android-docker-cli"
    
    if [ -d "$REMOTE_DIR" ]; then
        print_info "发现远程安装: $REMOTE_DIR"
        return 0
    else
        print_warning "未发现远程安装目录: $REMOTE_DIR"
        return 1
    fi
}

# 检查命令包装器
check_command_wrappers() {
    DOCKER_CMD="$PREFIX/bin/docker"
    DOCKER_COMPOSE_CMD="$PREFIX/bin/docker-compose"
    
    has_docker=false
    has_compose=false
    
    if [ -f "$DOCKER_CMD" ]; then
        print_info "发现docker命令包装器: $DOCKER_CMD"
        
        # 检查是否是android-docker-cli包装器
        if grep -q "android-docker-cli" "$DOCKER_CMD" 2>/dev/null; then
            print_info "确认是android-docker-cli包装器"
            has_docker=true
        else
            print_warning "可能是其他docker包装器，请手动确认"
        fi
    else
        print_info "未发现docker命令包装器"
    fi
    
    if [ -f "$DOCKER_COMPOSE_CMD" ]; then
        print_info "发现docker-compose命令包装器: $DOCKER_COMPOSE_CMD"
        has_compose=true
    else
        print_info "未发现docker-compose命令包装器"
    fi
    
    echo "$has_docker:$has_compose"
}

# 备份重要数据
backup_data() {
    REMOTE_DIR="$HOME/.android-docker-cli"
    BACKUP_DIR="$HOME/.android-docker-cli-backup-$(date +%Y%m%d-%H%M%S)"
    
    if [ -d "$REMOTE_DIR" ]; then
        print_info "创建备份: $BACKUP_DIR"
        cp -r "$REMOTE_DIR" "$BACKUP_DIR"
        print_success "备份完成: $BACKUP_DIR"
    fi
}

# 卸载命令包装器
uninstall_wrappers() {
    DOCKER_CMD="$PREFIX/bin/docker"
    DOCKER_COMPOSE_CMD="$PREFIX/bin/docker-compose"
    
    if [ "$1" = "true" ] && [ -f "$DOCKER_CMD" ]; then
        print_info "删除docker命令包装器..."
        rm -f "$DOCKER_CMD"
        print_success "docker命令包装器已删除"
    fi
    
    if [ "$2" = "true" ] && [ -f "$DOCKER_COMPOSE_CMD" ]; then
        print_info "删除docker-compose命令包装器..."
        rm -f "$DOCKER_COMPOSE_CMD"
        print_success "docker-compose命令包装器已删除"
    fi
}

# 卸载远程安装
uninstall_remote() {
    REMOTE_DIR="$HOME/.android-docker-cli"
    
    if [ -d "$REMOTE_DIR" ]; then
        print_info "删除远程安装目录..."
        rm -rf "$REMOTE_DIR"
        print_success "远程安装目录已删除"
    fi
}

# 清理缓存和配置
cleanup_cache() {
    print_warning "发现缓存目录: $HOME/.docker_proot_cache"
    if [ -d "$HOME/.docker_proot_cache" ]; then
        read -p "是否删除此缓存目录？(y/N): " -n 1 -r
        echo
        if [ "$REPLY" = "y" ] || [ "$REPLY" = "Y" ]; then
            print_info "删除缓存目录: $HOME/.docker_proot_cache"
            rm -rf "$HOME/.docker_proot_cache"
            print_success "缓存目录已删除"
        else
            print_info "保留缓存目录: $HOME/.docker_proot_cache"
        fi
    fi
    
    print_warning "发现缓存目录: $HOME/.docker"
    if [ -d "$HOME/.docker" ]; then
        read -p "是否删除此缓存目录？(y/N): " -n 1 -r
        echo
        if [ "$REPLY" = "y" ] || [ "$REPLY" = "Y" ]; then
            print_info "删除缓存目录: $HOME/.docker"
            rm -rf "$HOME/.docker"
            print_success "缓存目录已删除"
        else
            print_info "保留缓存目录: $HOME/.docker"
        fi
    fi
}

# 验证卸载结果
verify_uninstallation() {
    print_info "验证卸载结果..."
    
    # 检查命令是否还存在
    if command -v docker >/dev/null 2>&1; then
        print_warning "docker命令仍然存在，可能不是通过远程安装脚本安装的"
    else
        print_success "docker命令已成功删除"
    fi
    
    if command -v docker-compose >/dev/null 2>&1; then
        print_warning "docker-compose命令仍然存在，可能不是通过远程安装脚本安装的"
    else
        print_success "docker-compose命令已成功删除"
    fi
    
    # 检查目录是否还存在
    if [ -d "$HOME/.android-docker-cli" ]; then
        print_error "远程安装目录仍然存在，卸载可能失败"
        return 1
    else
        print_success "远程安装目录已成功删除"
    fi
    
    return 0
}

# 显示卸载摘要
show_summary() {
    print_success "卸载完成！"
    echo
    echo "已删除的内容:"
    echo "- 远程安装目录: $HOME/.android-docker-cli"
    echo "- 命令包装器: docker, docker-compose"
    echo
    echo "保留的内容:"
    echo "- 备份目录: $HOME/.android-docker-cli-backup-*"
    echo "- 当前项目文件"
    echo
    echo "如需恢复，可以从备份目录恢复:"
    echo "cp -r $HOME/.android-docker-cli-backup-* $HOME/.android-docker-cli"
}

# 主函数
main() {
    echo "=========================================="
    echo "    Android Docker CLI 远程安装卸载脚本"
    echo "=========================================="
    echo
    
    # 检查环境
    check_termux
    
    # 检查远程安装
    if ! check_remote_installation; then
        print_warning "未发现远程安装，无需卸载"
        exit 0
    fi
    
    # 检查命令包装器
    wrapper_status=$(check_command_wrappers)
    has_docker=$(echo "$wrapper_status" | cut -d: -f1)
    has_compose=$(echo "$wrapper_status" | cut -d: -f2)
    
    # 确认卸载
    echo
    print_warning "即将卸载以下内容:"
    echo "- 远程安装目录: $HOME/.android-docker-cli"
    if [ "$has_docker" = "true" ]; then
        echo "- docker命令包装器: $PREFIX/bin/docker"
    fi
    if [ "$has_compose" = "true" ]; then
        echo "- docker-compose命令包装器: $PREFIX/bin/docker-compose"
    fi
    echo
    read -p "确认继续卸载？(y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_info "取消卸载"
        exit 0
    fi
    
    # 备份数据
    backup_data
    
    # 卸载命令包装器
    uninstall_wrappers "$has_docker" "$has_compose"
    
    # 卸载远程安装
    uninstall_remote
    
    # 清理缓存（可选）
    cleanup_cache
    
    # 验证卸载结果
    if verify_uninstallation; then
        show_summary
    else
        print_error "卸载验证失败，请检查上述错误信息"
        exit 1
    fi
}

# 运行主函数
main "$@"
