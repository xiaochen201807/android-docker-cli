# 远程安装脚本分析报告

## 安装命令分析

```bash
curl -sSL https://raw.githubusercontent.com/jinhan1414/android-docker-cli/main/scripts/install.sh | sh
```

这个命令会：
1. 从GitHub下载安装脚本
2. 通过管道传递给shell执行
3. 安装到 `$HOME/.android-docker-cli` 目录

## 安装脚本工作原理

### 1. 安装位置
- **安装目录**: `$HOME/.android-docker-cli`
- **命令路径**: `$PREFIX/bin/docker` 和 `$PREFIX/bin/docker-compose`
- **Python路径**: 通过 `PYTHONPATH` 环境变量设置

### 2. 安装步骤
1. 检查依赖（git, python）
2. 克隆仓库到 `~/.android-docker-cli`
3. 安装Python依赖（PyYAML）
4. 创建 `docker` 命令包装器
5. 创建 `docker-compose` 命令包装器

### 3. 命令包装器内容
```bash
#!/data/data/com.termux/files/usr/bin/sh
INSTALL_DIR="$HOME/.android-docker-cli"
PYTHON_SCRIPT="$INSTALL_DIR/android_docker/docker_cli.py"
exec env PYTHONPATH="$INSTALL_DIR" python -m android_docker.docker_cli "$@"
```

## 与当前项目的冲突分析

### ✅ **无冲突的部分**
- 安装到独立目录 `~/.android-docker-cli`
- 不影响当前项目文件
- 使用不同的Python路径

### ⚠️ **潜在冲突点**
1. **命令名称冲突**: 都会创建 `docker` 命令
2. **Python模块冲突**: 如果同时运行，可能有模块导入问题
3. **缓存目录冲突**: 可能使用相同的缓存目录

### 🔍 **具体冲突分析**

#### 命令冲突
```bash
# 远程安装会创建
$PREFIX/bin/docker -> 指向 ~/.android-docker-cli

# 我们当前项目
# 通过 python -m android_docker.docker_cli 运行
```

#### 模块冲突
```bash
# 远程安装
PYTHONPATH="$HOME/.android-docker-cli"

# 我们当前项目
# 使用当前目录的PYTHONPATH
```

## 避免冲突的策略

### 1. **使用不同的命令名称**
```bash
# 远程安装使用
docker

# 我们使用
python -m android_docker.docker_cli
# 或者创建别名
alias mydocker="python -m android_docker.docker_cli"
```

### 2. **使用不同的缓存目录**
```bash
# 在docker_cli.py中设置不同的缓存目录
cache_dir = os.path.join(os.path.expanduser('~'), '.my_docker_cache')
```

### 3. **使用不同的配置目录**
```bash
# 避免配置文件冲突
config_dir = os.path.join(os.path.expanduser('~'), '.my_docker_config')
```

## 卸载指南

### 方法1: 完全卸载远程安装
```bash
# 1. 删除安装目录
rm -rf ~/.android-docker-cli

# 2. 删除命令包装器
rm -f $PREFIX/bin/docker
rm -f $PREFIX/bin/docker-compose

# 3. 清理缓存和配置
rm -rf ~/.docker_proot_cache
rm -f ~/.docker_proot_cache/config.json

# 4. 检查是否还有其他相关文件
find ~ -name "*docker*" -type d 2>/dev/null
```

### 方法2: 保留远程安装，避免冲突
```bash
# 1. 重命名远程安装的命令
mv $PREFIX/bin/docker $PREFIX/bin/docker-remote
mv $PREFIX/bin/docker-compose $PREFIX/bin/docker-compose-remote

# 2. 创建我们的命令别名
echo 'alias mydocker="python -m android_docker.docker_cli"' >> ~/.bashrc
echo 'alias mydocker-compose="python -m android_docker.docker_compose_cli"' >> ~/.bashrc

# 3. 重新加载配置
source ~/.bashrc
```

### 方法3: 使用不同的安装目录
```bash
# 1. 修改远程安装脚本，使用不同的目录
# 将 INSTALL_DIR 改为：
INSTALL_DIR="$HOME/.android-docker-cli-remote"

# 2. 或者使用我们的安装脚本
./scripts/install.sh
```

## 推荐解决方案

### 🎯 **最佳实践：避免冲突**

1. **不要同时运行两个版本**
2. **使用不同的命令名称**
3. **使用不同的缓存和配置目录**
4. **在开发时使用我们的版本**
5. **在生产环境使用远程安装版本**

### 📝 **具体操作步骤**

```bash
# 1. 检查当前安装状态
ls -la $PREFIX/bin/docker*
ls -la ~/.android-docker-cli

# 2. 如果已安装远程版本，重命名命令
if [ -f "$PREFIX/bin/docker" ]; then
    mv "$PREFIX/bin/docker" "$PREFIX/bin/docker-remote"
    mv "$PREFIX/bin/docker-compose" "$PREFIX/bin/docker-compose-remote"
    echo "已重命名远程安装的命令"
fi

# 3. 创建我们的命令别名
echo 'alias mydocker="python -m android_docker.docker_cli"' >> ~/.bashrc
echo 'alias mydocker-compose="python -m android_docker.docker_compose_cli"' >> ~/.bashrc

# 4. 重新加载配置
source ~/.bashrc

# 5. 测试我们的版本
mydocker --help
```

## 总结

远程安装脚本与我们当前项目**基本无冲突**，因为：
- 安装到独立目录
- 使用不同的Python路径
- 不影响当前项目文件

**主要冲突点**是命令名称，可以通过重命名或使用别名解决。

**推荐做法**：
1. 保留远程安装（如果需要）
2. 重命名远程命令避免冲突
3. 使用我们的版本进行开发和测试
4. 在需要时使用远程安装版本
