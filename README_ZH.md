# Android Docker CLI

[English](README.md) | 中文

一个使用 `proot` 在 Android 上运行 Docker 镜像的工具，无需 Docker 引擎。本项目旨在 [Termux](https://github.com/termux/termux-app) 应用内部使用，为 Android 提供一个类似 Docker 的命令行界面，用于管理持久化容器。

## 核心功能

- **`docker_cli.py`** - 主要入口点。一个用于完整容器生命周期管理的 Docker 风格 CLI。
- **持久化容器**: 容器拥有持久化的文件系统，可以被启动、停止和重启。
- **底层引擎**: 使用 `proot_runner.py` 来执行容器，使用 `create_rootfs_tar.py` 来下载和准备容器镜像。

## 安装

您可以使用一行命令来安装此工具：

```bash
curl -sSL https://raw.githubusercontent.com/jinhan1414/android-docker-cli/main/install.sh | sh
```

这将会创建一个名为 `docker` 的可执行命令到您的系统路径中。安装后，您只需输入 `docker` 即可运行此工具。

## 安装依赖

```bash
# Android Termux
pkg update && pkg install python proot curl tar

# Ubuntu/Debian
sudo apt install python3 proot curl tar
```

## 快速使用

安装后，您可以像使用标准 Docker 命令行一样使用此工具。

```bash
# 拉取镜像
docker pull alpine:latest

# 在前台运行一个容器
docker run alpine:latest echo "Hello from container"

# 在后台（分离模式）运行一个容器
docker run -d -e "API_KEY=sk-12345" --volume /sdcard:/data nginx:alpine

# 交互式运行容器
docker run -it alpine:latest /bin/sh

# 列出正在运行的容器
docker ps

# 列出所有容器（包括已停止的）
docker ps -a

# 查看容器日志
docker logs <container_id>
docker logs -f <container_id>  # 持续跟踪日志

# 停止一个容器
docker stop <container_id>

# 启动一个已停止的容器
docker start <container_id>

# 重启一个容器
docker restart <container_id>

# 删除一个容器
docker rm <container_id>

# 附加到运行中的容器
docker attach <container_id>

# 在运行中的容器中执行命令
docker exec <container_id> ls -l
docker exec -it <container_id> /bin/sh

# 列出缓存的镜像
docker images

# 删除一个缓存的镜像
docker rmi alpine:latest
```

## Docker Compose 支持

此工具包含一个 `docker-compose` 命令，用于管理多容器应用。

```bash
# 启动 docker-compose.yml 中定义的服务
docker-compose up

# 在后台运行
docker-compose up -d

# 停止并移除服务
docker-compose down
```

### `docker-compose.yml` 示例

```yaml
version: '3'
services:
  web:
    image: nginx:alpine
    container_name: my-web-server
  db:
    image: redis:alpine
    container_name: my-redis-db
```

## 主要特性

- ✅ **完整的容器生命周期**: `run`, `ps`, `stop`, `start`, `restart`, `logs`, `rm`, `attach`, `exec`。
- ✅ **Docker Compose 支持**: 使用 `docker-compose up` 和 `down` 管理多容器配置。
- ✅ **Docker风格CLI**: 熟悉且直观的命令行界面。
- ✅ **持久化存储**: 容器在重启后能保持其状态和文件系统，存储于 `~/.docker_proot_cache/`。
- ✅ **Android优化**: 针对 Termux 环境进行了特别优化。

## 故障排除

```bash
# 检查依赖
curl --version && tar --version && proot --version

# 使用详细日志获取更多信息
docker --verbose run alpine:latest
```

## 限制说明

- 基于 `proot`，并非完整的容器化（无内核级的进程或网络隔离）。
- 某些系统调用可能不被支持。
- 性能相较于原生 Docker 会有所下降。

## 许可证

MIT License
