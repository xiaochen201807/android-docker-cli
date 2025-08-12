# Android Docker CLI

[English](README.md) | 中文

在Android Termux中运行Docker镜像，无需Docker引擎。

## 核心功能

- **`create_rootfs_tar.py`** - 下载Docker镜像并转换为根文件系统tar包
- **`proot_runner.py`** - 使用proot运行容器，支持直接运行镜像URL（一条龙服务）

## 安装依赖

```bash
# Android Termux
pkg update && pkg install python proot curl tar

# Ubuntu/Debian
sudo apt install python3 proot curl tar
```

## 快速使用

### 直接运行镜像（推荐）
```bash
# 运行Alpine Linux
python proot_runner.py swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/alpine:latest

# 运行nginx（后台）
python proot_runner.py -d nginx:alpine

# 带环境变量和挂载
python proot_runner.py -e "API_KEY=sk-12345" -b /host/data:/data alpine:latest
```

### 分步操作
```bash
# 1. 下载镜像
python create_rootfs_tar.py alpine:latest

# 2. 运行容器
python proot_runner.py rootfs.tar.gz
```

## 主要特性

- ✅ **零外部依赖**: 只需curl、tar和Python标准库
- ✅ **一条龙服务**: 直接运行镜像URL，自动下载和缓存
- ✅ **Docker风格CLI**: 熟悉的`-e`、`-b`、`-w`、`-d`参数
- ✅ **多架构支持**: ARM64、AMD64等
- ✅ **Android优化**: 特别针对Termux环境优化

## 常用参数

### create_rootfs_tar.py
```bash
python create_rootfs_tar.py [镜像URL] [-o 输出文件] [-v]
```

### proot_runner.py
```bash
python proot_runner.py [选项] 镜像URL或tar文件 [命令]

-e KEY=VALUE    设置环境变量
-b HOST:CONTAINER  绑定挂载
-w DIR          工作目录
-d              后台运行
-v              详细日志
--list-cache    列出缓存
--clear-cache   清理缓存
```

## 故障排除

```bash
# 检查依赖
curl --version && tar --version && proot --version

# 详细日志
python proot_runner.py -v alpine:latest

# 清理缓存重试
python proot_runner.py --clear-cache all
```

## 限制说明

- 基于proot，不是完整容器化（无进程/网络隔离）
- 某些系统调用可能不被支持
- 性能相比原生Docker有所下降

## 许可证

MIT License
