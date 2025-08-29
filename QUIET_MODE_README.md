# 简洁模式使用说明

## 概述

为了减少冗余输出并提供更好的用户体验，我们为 `create_rootfs_tar.py` 脚本添加了简洁模式选项。

## 使用方法

### 1. 简洁模式（推荐）

```bash
python -m android_docker.create_rootfs_tar --quiet nginx:alpine
```

**特点：**
- 减少冗余的步骤信息
- 显示下载进度条
- 只显示关键的成功/失败信息
- 输出更清晰易读

### 2. 正常模式（默认）

```bash
python -m android_docker.create_rootfs_tar nginx:alpine
```

**特点：**
- 显示所有步骤信息
- 显示详细的curl命令
- 适合调试和了解详细过程

### 3. 详细模式

```bash
python -m android_docker.create_rootfs_tar --verbose nginx:alpine
```

**特点：**
- 显示最详细的调试信息
- 显示所有HTTP请求和响应
- 适合开发者调试

## 输出对比

### 简洁模式输出示例：
```
2025-08-29 11:17:24,714 - INFO - 开始处理Docker镜像: nginx
2025-08-29 11:17:24,866 - INFO - 目标架构: arm64
2025-08-29 11:17:24,896 - INFO - ✓ curl 已安装
2025-08-29 11:17:24,911 - INFO - ✓ tar 已安装
2025-08-29 11:17:24,914 - INFO - 创建临时目录: /tmp/docker_rootfs_xxx
2025-08-29 11:17:24,914 - INFO - 步骤 1/4: 下载Docker镜像...
2025-08-29 11:17:24,915 - INFO - 获取镜像信息: library/nginx:latest
2025-08-29 11:17:24,916 - INFO - 探测认证服务器...
2025-08-29 11:17:29,605 - INFO - ✓ 成功获取认证Token
2025-08-29 11:17:31,390 - INFO - 检测到多架构镜像，选择匹配架构...
2025-08-29 11:17:31,391 - INFO - 选择架构: arm64
2025-08-29 11:17:31,392 - INFO - 开始下载 2 个层...
2025-08-29 11:17:31,392 - INFO - 下载层 1/2...
2025-08-29 11:17:31,392 - INFO - 下载: 9a80f9a05524...
████████████████████████████████████████ 100%
2025-08-29 11:18:15,957 - INFO - ✓ 下载完成
2025-08-29 11:18:15,958 - INFO - 下载层 2/2...
████████████████████████████████████████ 100%
2025-08-29 11:18:45,123 - INFO - ✓ 下载完成
2025-08-29 11:18:45,124 - INFO - ✓ 所有层下载完成
2025-08-29 11:18:45,125 - INFO - ✓ 镜像下载完成
2025-08-29 11:18:45,126 - INFO - 步骤 2/4: 提取根文件系统...
2025-08-29 11:18:45,127 - INFO - 步骤 3/4: 保存镜像配置...
2025-08-29 11:18:45,128 - INFO - 步骤 4/4: 优化根文件系统...
2025-08-29 11:18:45,129 - INFO - 创建最终tar包...
2025-08-29 11:18:45,130 - INFO - ✓ 成功创建根文件系统tar包: nginx_rootfs.tar
```

### 正常模式输出示例：
```
2025-08-29 11:17:24,714 - INFO - 开始处理Docker镜像: nginx
2025-08-29 11:17:24,715 - INFO - 找到 https://index.docker.io/v1/ 的凭证
2025-08-29 11:17:24,715 - INFO - 下载镜像: nginx
2025-08-29 11:17:24,865 - INFO - 开始处理Docker镜像: nginx
2025-08-29 11:17:24,866 - INFO - 目标架构: arm64
2025-08-29 11:17:24,896 - INFO - ✓ curl 已安装
2025-08-29 11:17:24,911 - INFO - ✓ tar 已安装
2025-08-29 11:17:24,914 - INFO - 创建临时目录: /tmp/docker_rootfs_xxx
2025-08-29 11:17:24,914 - INFO - 步骤 1/4: 使用Python下载Docker镜像...
2025-08-29 11:17:24,915 - INFO - 解析镜像URL: registry=https://registry-1.docker.io, image=library/nginx, tag=latest
2025-08-29 11:17:24,915 - INFO - 获取镜像manifest: library/nginx:latest
2025-08-29 11:17:24,916 - INFO - ---
[ 步骤 1/3: 探测认证服务器 ]
---
2025-08-29 11:17:24,916 - INFO - ---
[ 执行命令 ]
curl -v -i --insecure https://registry-1.docker.io/v2/library/nginx/manifests/latest
---
2025-08-29 11:17:27,190 - INFO - ---
[ 步骤 2/3: 获取认证Token ]
---
2025-08-29 11:17:27,191 - INFO - ---
[ 执行命令 ]
curl -v -u xiaochen1649:*** -H User-Agent: docker-rootfs-creator/1.0 https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/nginx:pull
---
2025-08-29 11:17:29,605 - INFO - ✓ 成功获取认证Token
2025-08-29 11:17:29,606 - INFO - ---
[ 步骤 3/3: 获取镜像Manifest ]
---
2025-08-29 11:17:29,606 - INFO - ---
[ 执行命令 ]
curl -v -i --insecure -H User-Agent: docker-rootfs-creator/1.0 -H Accept: application/vnd.docker.distribution.manifest.v2+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json -H Authorization: Bearer [TOKEN] https://registry-1.docker.io/v2/library/nginx/manifests/latest
---
2025-08-29 11:17:31,390 - INFO - Manifest类型: application/vnd.oci.image.index.v1+json
2025-08-29 11:17:31,391 - INFO - 检测到manifest list，正在寻找匹配的架构...
2025-08-29 11:17:31,391 - INFO - 找到匹配架构 'arm64' 的manifest: sha256:1e297dbd6dd3441f54fbeeef6be4688f257a85580b21940d18c2c11f9ce6a708
2025-08-29 11:17:31,392 - INFO - ---
[ 步骤 3/3: 获取镜像Manifest ]
---
2025-08-29 11:17:31,392 - INFO - ---
[ 执行命令 ]
curl -v -i --insecure -H User-Agent: docker-rootfs-creator/1.0 -H Authorization: Bearer [TOKEN] https://registry-1.docker.io/v2/library/nginx/manifests/sha256:1e297dbd6dd3441f54fbeeef6be4688f257a85580b21940d18c2c11f9ce6a708
---
2025-08-29 11:17:33,035 - INFO - 已选择子manifest，类型: application/vnd.oci.image.manifest.v1+json
2025-08-29 11:17:33,039 - INFO - 下载blob: sha256:9a80f9a055240e1d5ffd4b99717e18b5b3e924369b9155fb0a951a7a94b2c61f
2025-08-29 11:17:33,039 - INFO - ---
[ 执行命令 ]
curl -v -L -H User-Agent: docker-rootfs-creator/1.0 -H Authorization: Bearer [TOKEN] -o /tmp/docker_rootfs_xxx/oci/blobs/sha256/9a80f9a055240e1d5ffd4b99717e18b5b3e924369b9155fb0a951a7a94b2c61f https://registry-1.docker.io/v2/library/nginx/blobs/sha256:9a80f9a055240e1d5ffd4b99717e18b5b3e924369b9155fb0a951a7a94b2c61f
---
2025-08-29 11:18:15,957 - INFO - 下载blob: sha256:baccdd222209a10a86b4ec8d0f5fd41fbd8a0a40c869964c1c59f067b6e39e0c
2025-08-29 11:18:15,958 - INFO - ---
[ 执行命令 ]
curl -v -L -H User-Agent: docker-rootfs-creator/1.0 -H Authorization: Bearer [TOKEN] -o /tmp/docker_rootfs_xxx/oci/blobs/sha256/baccdd222209a10a86b4ec8d0f5fd41fbd8a0a40c869964c1c59f067b6e39e0c https://registry-1.docker.io/v2/library/nginx/blobs/sha256:baccdd222209a10a86b4ec8d0f5fd41fbd8a0a40c869964c1c59f067b6e39e0c
---
... (更多详细输出)
```

## 参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `--quiet` | `-q` | 启用简洁模式，减少冗余输出 |
| `--verbose` | `-v` | 启用详细模式，显示调试信息 |
| 无参数 | - | 正常模式，显示所有步骤信息 |

## 推荐使用场景

### 简洁模式适合：
- 日常使用
- 自动化脚本
- 需要清晰进度显示的场景
- 减少日志文件大小

### 正常模式适合：
- 首次使用，了解工作流程
- 需要了解详细步骤的场景
- 教学和演示

### 详细模式适合：
- 调试问题
- 开发测试
- 需要了解底层细节的场景

## 注意事项

1. **进度条显示**：简洁模式下会显示curl的下载进度条
2. **错误信息**：所有模式下都会显示错误和警告信息
3. **成功标记**：简洁模式下会显示 ✓ 标记的成功信息
4. **日志级别**：简洁模式会过滤掉大部分INFO级别的步骤信息

## 示例命令

```bash
# 简洁模式拉取nginx镜像
python -m android_docker.create_rootfs_tar --quiet nginx:alpine

# 简洁模式拉取alpine镜像
python -m android_docker.create_rootfs_tar -q alpine:latest

# 简洁模式拉取自定义镜像
python -m android_docker.create_rootfs_tar --quiet my-registry.com/my-image:v1.0

# 简洁模式 + 指定输出文件
python -m android_docker.create_rootfs_tar --quiet -o my_image.tar nginx:alpine
```
