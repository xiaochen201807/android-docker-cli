# 安装冲突避免指南

## 问题分析

用户询问的安装命令：
```bash
curl -sSL https://raw.githubusercontent.com/jinhan1414/android-docker-cli/main/scripts/install.sh | sh
```

这个命令会安装一个远程版本的 `android-docker-cli`，可能与我们的本地修改版本产生冲突。

## 冲突分析结果

### ✅ **好消息：基本无冲突**

远程安装脚本与我们当前项目**基本无冲突**，因为：

1. **独立安装目录**：安装到 `$HOME/.android-docker-cli`
2. **不同Python路径**：使用独立的 `PYTHONPATH`
3. **不影响当前项目**：不会修改我们正在开发的代码

### ⚠️ **潜在冲突点**

1. **命令名称冲突**：都会创建 `docker` 命令
2. **缓存目录冲突**：可能使用相同的缓存目录
3. **配置文件冲突**：可能使用相同的配置目录

## 解决方案

### 🎯 **推荐方案：避免冲突**

#### 1. **使用不同的命令名称**
```bash
# 远程安装使用
docker --help

# 我们使用
python -m android_docker.docker_cli --help

# 或者创建别名
alias mydocker="python -m android_docker.docker_cli"
alias mydocker-compose="python -m android_docker.docker_compose_cli"
```

#### 2. **使用不同的缓存目录**
```bash
# 在 docker_cli.py 中设置
cache_dir = os.path.join(os.path.expanduser('~'), '.my_docker_cache')
```

#### 3. **使用不同的配置目录**
```bash
# 避免配置文件冲突
config_dir = os.path.join(os.path.expanduser('~'), '.my_docker_config')
```

### 🔧 **具体操作步骤**

#### 步骤1：检查当前状态
```bash
# 运行检查脚本
python check_installation.py
```

#### 步骤2：如果已安装远程版本，重命名命令
```bash
# 重命名远程命令避免冲突
mv $PREFIX/bin/docker $PREFIX/bin/docker-remote
mv $PREFIX/bin/docker-compose $PREFIX/bin/docker-compose-remote
```

#### 步骤3：创建我们的命令别名
```bash
# 添加到 ~/.bashrc
echo 'alias mydocker="python -m android_docker.docker_cli"' >> ~/.bashrc
echo 'alias mydocker-compose="python -m android_docker.docker_compose_cli"' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

#### 步骤4：测试我们的版本
```bash
# 测试docker命令
mydocker --help

# 测试简洁模式
python -m android_docker.create_rootfs_tar --quiet --help
```

## 卸载指南

### 如果需要完全卸载远程版本

#### 方法1：使用卸载脚本
```bash
# 运行卸载脚本
bash uninstall_remote.sh
```

#### 方法2：手动卸载
```bash
# 1. 删除安装目录
rm -rf ~/.android-docker-cli

# 2. 删除命令包装器
rm -f $PREFIX/bin/docker
rm -f $PREFIX/bin/docker-compose

# 3. 清理缓存（可选）
rm -rf ~/.docker_proot_cache
```

## 使用建议

### 🚀 **开发环境**
- 使用我们的本地版本
- 通过 `python -m` 运行
- 使用简洁模式 `--quiet` 减少输出

### 🏭 **生产环境**
- 使用远程安装版本
- 通过 `docker` 命令运行
- 更稳定，经过测试

### 🔄 **切换使用**
```bash
# 使用远程版本
docker --help

# 使用我们的版本
mydocker --help
# 或者
python -m android_docker.docker_cli --help
```

## 文件说明

### 📁 **新增文件**
1. `INSTALL_ANALYSIS.md` - 详细冲突分析
2. `check_installation.py` - 安装状态检查脚本
3. `uninstall_remote.sh` - 远程安装卸载脚本
4. `README_INSTALL_CONFLICT.md` - 本指南

### 📁 **原有文件**
1. `android_docker/create_rootfs_tar.py` - 已添加简洁模式
2. `QUIET_MODE_README.md` - 简洁模式使用说明
3. `OPTIMIZATION_SUMMARY.md` - 优化总结

## 总结

1. **远程安装基本无冲突**，可以安全安装
2. **主要冲突是命令名称**，通过重命名或别名解决
3. **我们提供了完整的解决方案**，包括检查、避免冲突、卸载等
4. **推荐使用我们的版本进行开发**，远程版本用于生产

## 快速开始

```bash
# 1. 检查安装状态
python check_installation.py

# 2. 使用我们的版本（推荐）
python -m android_docker.docker_cli --help

# 3. 使用简洁模式
python -m android_docker.create_rootfs_tar --quiet nginx:alpine

# 4. 创建别名（可选）
echo 'alias mydocker="python -m android_docker.docker_cli"' >> ~/.bashrc
source ~/.bashrc
mydocker --help
```

如有问题，请参考相关文档或运行检查脚本获取帮助。
