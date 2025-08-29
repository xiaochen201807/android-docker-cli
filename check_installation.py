#!/usr/bin/env python3
"""
安装状态检查脚本
检查是否有远程安装的android-docker-cli，以及潜在的冲突
"""

import os
import sys
import subprocess
from pathlib import Path

def check_termux_environment():
    """检查是否在Termux环境中"""
    termux_prefix = "/data/data/com.termux/files/usr"
    if os.path.exists(termux_prefix):
        return True, termux_prefix
    return False, None

def check_remote_installation():
    """检查远程安装状态"""
    home_dir = os.path.expanduser("~")
    remote_dir = os.path.join(home_dir, ".android-docker-cli")
    
    if os.path.exists(remote_dir):
        print(f"✓ 发现远程安装: {remote_dir}")
        
        # 检查文件结构
        android_docker_dir = os.path.join(remote_dir, "android_docker")
        if os.path.exists(android_docker_dir):
            print(f"  - android_docker目录: 存在")
            
            # 检查主要文件
            docker_cli = os.path.join(android_docker_dir, "docker_cli.py")
            if os.path.exists(docker_cli):
                print(f"  - docker_cli.py: 存在")
            else:
                print(f"  - docker_cli.py: 缺失")
        else:
            print(f"  - android_docker目录: 缺失")
        
        return True, remote_dir
    else:
        print("✗ 未发现远程安装")
        return False, None

def check_command_wrappers(termux_prefix):
    """检查命令包装器"""
    if not termux_prefix:
        print("⚠️  不在Termux环境中，跳过命令包装器检查")
        return False, False
    
    bin_dir = os.path.join(termux_prefix, "bin")
    docker_cmd = os.path.join(bin_dir, "docker")
    docker_compose_cmd = os.path.join(bin_dir, "docker-compose")
    
    docker_exists = os.path.exists(docker_cmd)
    docker_compose_exists = os.path.exists(docker_compose_cmd)
    
    if docker_exists:
        print(f"✓ 发现docker命令包装器: {docker_cmd}")
        
        # 检查包装器内容
        try:
            with open(docker_cmd, 'r') as f:
                content = f.read()
                if "android-docker-cli" in content:
                    print("  - 确认是android-docker-cli包装器")
                else:
                    print("  - 可能是其他docker包装器")
        except Exception as e:
            print(f"  - 无法读取包装器内容: {e}")
    else:
        print("✗ 未发现docker命令包装器")
    
    if docker_compose_exists:
        print(f"✓ 发现docker-compose命令包装器: {docker_compose_cmd}")
    else:
        print("✗ 未发现docker-compose命令包装器")
    
    return docker_exists, docker_compose_exists

def check_current_project():
    """检查当前项目状态"""
    current_dir = os.getcwd()
    print(f"\n📁 当前项目目录: {current_dir}")
    
    # 检查项目结构
    android_docker_dir = os.path.join(current_dir, "android_docker")
    if os.path.exists(android_docker_dir):
        print("✓ 当前项目包含android_docker目录")
        
        # 检查主要文件
        docker_cli = os.path.join(android_docker_dir, "docker_cli.py")
        create_rootfs = os.path.join(android_docker_dir, "create_rootfs_tar.py")
        
        if os.path.exists(docker_cli):
            print("  - docker_cli.py: 存在")
        else:
            print("  - docker_cli.py: 缺失")
            
        if os.path.exists(create_rootfs):
            print("  - create_rootfs_tar.py: 存在")
        else:
            print("  - create_rootfs_tar.py: 缺失")
    else:
        print("✗ 当前项目不包含android_docker目录")
        return False
    
    return True

def check_python_modules():
    """检查Python模块导入状态"""
    print("\n🐍 检查Python模块导入...")
    
    try:
        import android_docker
        print("✓ 可以导入android_docker模块")
        
        try:
            from android_docker import docker_cli
            print("✓ 可以导入docker_cli模块")
        except ImportError as e:
            print(f"✗ 无法导入docker_cli模块: {e}")
            
        try:
            from android_docker import create_rootfs_tar
            print("✓ 可以导入create_rootfs_tar模块")
        except ImportError as e:
            print(f"✗ 无法导入create_rootfs_tar模块: {e}")
            
    except ImportError as e:
        print(f"✗ 无法导入android_docker模块: {e}")

def check_cache_directories():
    """检查缓存目录"""
    print("\n📂 检查缓存目录...")
    
    home_dir = os.path.expanduser("~")
    cache_dirs = [
        ".docker_proot_cache",
        ".android-docker-cli",
        ".docker"
    ]
    
    for cache_dir in cache_dirs:
        cache_path = os.path.join(home_dir, cache_dir)
        if os.path.exists(cache_path):
            print(f"✓ 发现缓存目录: {cache_path}")
            
            # 检查大小
            try:
                total_size = 0
                file_count = 0
                for dirpath, dirnames, filenames in os.walk(cache_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)
                            file_count += 1
                
                size_mb = total_size / (1024 * 1024)
                print(f"  - 文件数量: {file_count}")
                print(f"  - 总大小: {size_mb:.2f} MB")
            except Exception as e:
                print(f"  - 无法计算大小: {e}")
        else:
            print(f"✗ 未发现缓存目录: {cache_path}")

def suggest_solutions(has_remote, has_wrappers, has_current):
    """建议解决方案"""
    print("\n💡 建议解决方案:")
    
    if has_remote and has_wrappers:
        print("1. 发现远程安装和命令包装器，建议:")
        print("   - 重命名远程命令避免冲突:")
        print("     mv $PREFIX/bin/docker $PREFIX/bin/docker-remote")
        print("     mv $PREFIX/bin/docker-compose $PREFIX/bin/docker-compose-remote")
        print("   - 创建当前项目的别名:")
        print("     echo 'alias mydocker=\"python -m android_docker.docker_cli\"' >> ~/.bashrc")
        print("     echo 'alias mydocker-compose=\"python -m android_docker.docker_compose_cli\"' >> ~/.bashrc")
        
    elif has_remote and not has_wrappers:
        print("1. 发现远程安装但无命令包装器，建议:")
        print("   - 使用当前项目版本:")
        print("     python -m android_docker.docker_cli --help")
        
    elif not has_remote and has_wrappers:
        print("1. 发现命令包装器但无远程安装，建议:")
        print("   - 检查包装器来源:")
        print("     cat $PREFIX/bin/docker")
        print("   - 如不需要可删除:")
        print("     rm $PREFIX/bin/docker $PREFIX/bin/docker-compose")
        
    else:
        print("1. 无冲突，可以直接使用当前项目:")
        print("   python -m android_docker.docker_cli --help")
    
    if has_current:
        print("\n2. 当前项目使用方式:")
        print("   - 直接运行: python -m android_docker.docker_cli --help")
        print("   - 简洁模式: python -m android_docker.create_rootfs_tar --quiet nginx:alpine")
        print("   - 创建别名: alias mydocker=\"python -m android_docker.docker_cli\"")

def main():
    """主函数"""
    print("🔍 Android Docker CLI 安装状态检查")
    print("=" * 50)
    
    # 检查环境
    is_termux, termux_prefix = check_termux_environment()
    if is_termux:
        print(f"✓ 检测到Termux环境: {termux_prefix}")
    else:
        print("⚠️  不在Termux环境中")
    
    # 检查远程安装
    has_remote, remote_dir = check_remote_installation()
    
    # 检查命令包装器
    has_docker_wrapper, has_compose_wrapper = check_command_wrappers(termux_prefix)
    
    # 检查当前项目
    has_current = check_current_project()
    
    # 检查Python模块
    check_python_modules()
    
    # 检查缓存目录
    check_cache_directories()
    
    # 建议解决方案
    suggest_solutions(has_remote, has_docker_wrapper or has_compose_wrapper, has_current)
    
    print("\n" + "=" * 50)
    print("检查完成！如有问题请参考 INSTALL_ANALYSIS.md")

if __name__ == "__main__":
    main()
