#!/usr/bin/env python3
"""
测试简洁模式的脚本
演示如何使用 --quiet 参数减少冗余输出
"""

import subprocess
import sys
import os

def test_quiet_mode():
    """测试简洁模式"""
    print("=== 测试简洁模式 ===")
    print("1. 正常模式（详细输出）:")
    print("python -m android_docker.create_rootfs_tar nginx:alpine")
    print()
    print("2. 简洁模式（减少冗余输出）:")
    print("python -m android_docker.create_rootfs_tar --quiet nginx:alpine")
    print()
    print("3. 详细模式（调试信息）:")
    print("python -m android_docker.create_rootfs_tar --verbose nginx:alpine")
    print()
    
    # 检查当前目录
    if not os.path.exists('android_docker'):
        print("错误：请在项目根目录下运行此脚本")
        return
    
    # 测试简洁模式
    print("正在测试简洁模式...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'android_docker.create_rootfs_tar',
            '--quiet', '--help'
        ], capture_output=True, text=True, check=True)
        print("✓ 简洁模式参数解析正常")
        print("帮助信息:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"✗ 测试失败: {e}")
        print("错误输出:", e.stderr)

if __name__ == '__main__':
    test_quiet_mode()
