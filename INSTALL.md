# Android Docker CLI 安装指南

## 系统要求

- **Android**: Android 7.0+ (推荐 Android 10+)
- **Termux**: 最新版本的 Termux 应用
- **存储空间**: 至少 500MB 可用空间
- **网络**: 稳定的网络连接（用于下载镜像）

## 安装步骤

### 1. 安装 Termux

从 [F-Droid](https://f-droid.org/en/packages/com.termux/) 下载并安装 Termux 应用。

### 2. 更新系统包

```bash
pkg update && pkg upgrade
```

### 3. 安装基础依赖

```bash
pkg install python proot curl tar
```

### 4. 克隆项目

```bash
git clone <your-repository-url>
cd android-docker-cli
```

### 5. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 6. 运行安装脚本

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

安装脚本会自动：
- 检查系统依赖
- 安装 Python 包
- 创建 `docker` 命令链接
- 测试安装

## 验证安装

安装完成后，验证是否成功：

```bash
# 检查版本
docker version

# 查看帮助
docker --help

# 测试拉取镜像
docker pull alpine:latest
```

## 手动安装（不使用脚本）

如果不想使用安装脚本，可以手动安装：

```bash
# 创建软链接到系统路径
sudo ln -s $(pwd)/android_docker/docker_cli.py /usr/local/bin/docker

# 或者添加到用户 PATH
echo 'export PATH="$PWD:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 卸载

使用卸载脚本：

```bash
./scripts/uninstall.sh
```

卸载脚本会：
- 备份重要数据
- 删除命令链接
- 删除安装目录
- 可选清理缓存

## 故障排除

### 常见问题

1. **权限不足**
   ```bash
   # 检查权限
   ls -la android_docker/docker_cli.py
   
   # 添加执行权限
   chmod +x android_docker/docker_cli.py
   ```

2. **Python 版本问题**
   ```bash
   # 检查 Python 版本
   python --version
   
   # 如果版本过低，使用 python3
   python3 -m android_docker.docker_cli --help
   ```

3. **依赖缺失**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt --force-reinstall
   ```

4. **网络问题**
   ```bash
   # 检查网络连接
   curl -I https://registry-1.docker.io
   
   # 如果使用代理，设置环境变量
   export HTTP_PROXY=http://your-proxy:port
   export HTTPS_PROXY=http://your-proxy:port
   ```

### 获取帮助

```bash
# 查看详细帮助
docker --help

# 查看特定命令帮助
docker help run
docker help pull

# 启用详细日志
docker --verbose run alpine:latest
```

## 配置选项

### 环境变量

```bash
# 设置缓存目录
export DOCKER_PROOT_CACHE=/sdcard/docker_cache

# 设置镜像仓库
export DOCKER_REGISTRY=https://your-registry.com

# 设置超时时间
export DOCKER_TIMEOUT=300
```

### 配置文件

创建 `~/.docker/config.json` 文件：

```json
{
  "auths": {
    "https://index.docker.io/v1/": {
      "auth": "base64-encoded-credentials"
    }
  },
  "HttpHeaders": {
    "User-Agent": "Android-Docker-CLI/1.0"
  }
}
```

## 更新

```bash
# 拉取最新代码
git pull origin main

# 重新安装依赖
pip install -r requirements.txt --upgrade

# 重新运行安装脚本
./scripts/install.sh
```

## 支持

如果遇到问题：

1. 查看 [故障排除](#故障排除) 部分
2. 检查 [GitHub Issues](https://github.com/your-repo/issues)
3. 查看项目文档
4. 提交新的 Issue 描述问题

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。
