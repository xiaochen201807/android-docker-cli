# Android Docker CLI

[English](README.md) | 中文

一个使用 `proot` 在 Android 上运行 Docker 镜像的工具，无需 Docker 引擎。本项目旨在 [Termux](https://github.com/termux/termux-app) 应用内部使用，为 Android 提供一个类似 Docker 的命令行界面，用于管理持久化容器。

## 核心功能

- **模块化代码**: 所有核心逻辑都被组织在 `android_docker` 包中。
- **主命令行界面**: 主要入口点是 `android_docker/docker_cli.py`，提供一个用于完整容器生命周期管理的 Docker 风格 CLI。
- **持久化容器**: 容器拥有持久化的文件系统，可以被启动、停止和重启。
- **底层引擎**: 使用 `android_docker/proot_runner.py` 来执行容器，使用 `android_docker/create_rootfs_tar.py` 来下载和准备容器镜像。

## 安装

您可以使用一行命令来安装此工具：

```bash
curl -sSL https://raw.githubusercontent.com/jinhan1414/android-docker-cli/main/scripts/install.sh | sh
```

这将会创建一个名为 `docker` 的可执行命令到您的系统路径中。安装后，您只需输入 `docker` 即可运行此工具。

## 安装依赖

```bash
# Android Termux
pkg update && pkg install python proot curl tar

# Ubuntu/Debian
sudo apt install python3 proot curl tar

# 安装Python依赖（可选，用于增强功能）
pip install psutil
```

## 快速使用

安装后，您可以像使用标准 Docker 命令行一样使用此工具。

```bash
# 登录到 Docker Registry (例如 Docker Hub)
docker login

# 登录后从私有仓库拉取镜像
docker login your-private-registry.com
docker pull your-private-registry.com/my-image

# 拉取一个公开镜像
docker pull alpine:latest

# 推送镜像到仓库
docker push myimage:latest
docker push username/myapp:v1.0

# 在前台运行一个容器
docker run alpine:latest echo "Hello from container"

# 在后台（分离模式）运行一个容器
docker run -d -e "API_KEY=sk-12345" --volume /sdcard:/data nginx:alpine

# 交互式运行容器
docker run -it alpine:latest /bin/sh

# 使用项目中的自定义配置文件运行 Nginx 容器
# 此示例使用 `examples/nginx.conf` 文件, 它将监听 8777 端口。
docker run -d --name my-nginx -v $(pwd)/examples/nginx.conf:/etc/nginx/nginx.conf nginx:alpine

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

# 登录到镜像仓库
docker login your-private-registry.com
```

## 新增的Docker命令

### 镜像管理命令
```bash
# 构建镜像（概念性实现）
docker build <context_path> -t <tag>

# 保存镜像到tar文件
docker save <image> -o <output.tar>

# 从tar文件加载镜像
docker load -i <input.tar>

# 为镜像添加标签
docker tag <source_image> <target_image>

# 检查容器或镜像的详细信息
docker inspect <container_id_or_image>

# 显示镜像的历史记录
docker history <image>

# 推送镜像到Docker Registry
docker push <image>[:tag]
```

### 容器管理命令
```bash
# 显示容器中运行的进程
docker top <container_id>

# 显示容器的资源使用统计
docker stats [container_id]

# 在容器和主机之间复制文件
docker cp <source> <dest>
# 例如：docker cp mycontainer:/app/logs ./logs
# 例如：docker cp ./config mycontainer:/app/

# 显示容器文件系统的变更
docker diff <container_id>

# 从容器创建新镜像
docker commit <container_id> <repository>[:tag]

# 导出容器文件系统到tar文件
docker export <container_id> -o <output.tar>

# 从tar文件导入镜像
docker import <file.tar> <repository>[:tag]
```

### 网络管理命令
```bash
# 创建网络
docker network create <network_name> [--driver bridge]

# 列出网络
docker network ls

# 删除网络
docker network rm <network_name>
```

### 卷管理命令
```bash
# 创建卷
docker volume create <volume_name>

# 列出卷
docker volume ls

# 删除卷
docker volume rm <volume_name>
```

### 系统管理命令
```bash
# 显示系统信息
docker info

# 显示版本信息
docker version

# 显示帮助信息
docker help [command]

# 清理未使用的资源
docker system prune [-a]
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
- ✅ **镜像仓库认证**: 使用 `login` 命令登录私有或公共镜像仓库。
- ✅ **Docker Compose 支持**: 使用 `docker-compose up` 和 `down` 管理多容器配置。
- ✅ **Docker风格CLI**: 熟悉且直观的命令行界面。
- ✅ **持久化存储**: 容器在重启后能保持其状态和文件系统，存储于 `~/.docker_proot_cache/`。
- ✅ **Android优化**: 针对 Termux 环境进行了特别优化。
- ✅ **扩展的镜像管理**: `build`, `save`, `load`, `tag`, `inspect`, `history`。
- ✅ **增强的容器管理**: `top`, `stats`, `cp`, `diff`, `commit`, `export`, `import`。
- ✅ **网络和卷管理**: `network create/ls/rm`, `volume create/ls/rm`。
- ✅ **系统管理**: `info`, `version`, `help`, `system prune`。

## 故障排除

```bash
# 检查依赖
curl --version && tar --version && proot --version

# 使用详细日志获取更多信息
docker --verbose run alpine:latest

# 显示帮助信息
docker help
docker help run  # 显示特定命令的帮助
```

## 限制说明

- 基于 `proot`，并非完整的容器化（无内核级的进程或网络隔离）。
- 某些系统调用可能不被支持。
- 性能相较于原生 Docker 会有所下降。
- 某些高级功能（如镜像构建、网络隔离）在proot环境下有限制，主要是概念性实现。

## 许可证

MIT License
