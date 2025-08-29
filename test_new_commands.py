#!/usr/bin/env python3
"""
测试新增的Docker命令
"""

import sys
import os
import subprocess

def test_command(command, description):
    """测试一个Docker命令"""
    print(f"\n测试: {description}")
    print(f"命令: {command}")
    
    try:
        # 使用Python模块的方式运行docker命令
        if command.startswith("docker "):
            # 将 docker command 转换为 python -m android_docker.docker_cli command
            cmd_parts = command.split()
            if len(cmd_parts) >= 2:
                subcommand = cmd_parts[1]
                args = cmd_parts[2:] if len(cmd_parts) > 2 else []
                
                # 构建Python模块命令
                python_cmd = ["python", "-m", "android_docker.docker_cli", subcommand] + args
                print(f"执行: {' '.join(python_cmd)}")
                
                result = subprocess.run(python_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("✅ 成功")
                    if result.stdout:
                        print("输出:", result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
                else:
                    print("❌ 失败")
                    if result.stderr:
                        print("错误:", result.stderr)
            else:
                print("❌ 命令格式错误")
        else:
            print("❌ 不是docker命令")
            
    except subprocess.TimeoutExpired:
        print("⏰ 超时")
    except Exception as e:
        print(f"❌ 异常: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试新增的Docker命令")
    
    # 测试基本命令
    test_command("docker --help", "显示帮助信息")
    test_command("docker version", "显示版本信息")
    test_command("docker info", "显示系统信息")
    
    # 测试镜像管理命令
    test_command("docker build --help", "构建镜像帮助")
    test_command("docker save --help", "保存镜像帮助")
    test_command("docker load --help", "加载镜像帮助")
    test_command("docker tag --help", "标签管理帮助")
    test_command("docker inspect --help", "检查命令帮助")
    test_command("docker history --help", "历史记录帮助")
    test_command("docker push --help", "推送镜像帮助")
    
    # 测试容器管理命令
    test_command("docker top --help", "进程查看帮助")
    test_command("docker stats --help", "资源统计帮助")
    test_command("docker cp --help", "文件复制帮助")
    test_command("docker diff --help", "文件变更帮助")
    test_command("docker commit --help", "镜像提交帮助")
    test_command("docker export --help", "容器导出帮助")
    test_command("docker import --help", "镜像导入帮助")
    
    # 测试网络管理命令
    test_command("docker network --help", "网络管理帮助")
    test_command("docker network create --help", "创建网络帮助")
    test_command("docker network ls --help", "列出网络帮助")
    test_command("docker network rm --help", "删除网络帮助")
    
    # 测试卷管理命令
    test_command("docker volume --help", "卷管理帮助")
    test_command("docker volume create --help", "创建卷帮助")
    test_command("docker volume ls --help", "列出卷帮助")
    test_command("docker volume rm --help", "删除卷帮助")
    
    # 测试系统管理命令
    test_command("docker system --help", "系统管理帮助")
    test_command("docker system prune --help", "清理资源帮助")
    
    print("\n🎉 测试完成！")
    print("\n注意：这些测试主要验证命令解析器是否正常工作。")
    print("某些命令在proot环境下可能有限制，这是正常的。")

if __name__ == '__main__':
    main()
