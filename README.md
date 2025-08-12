# Android Docker CLI

English | [中文](README_ZH.md)

Run Docker images on Android Termux without Docker engine.

## Core Features

- **`create_rootfs_tar.py`** - Download Docker images and convert to rootfs tar packages
- **`proot_runner.py`** - Run containers with proot, supports direct image URL execution (one-stop service)

## Install Dependencies

```bash
# Android Termux
pkg update && pkg install python proot curl tar

# Ubuntu/Debian
sudo apt install python3 proot curl tar
```

## Quick Start

### Direct Image Execution (Recommended)
```bash
# Run Alpine Linux
python proot_runner.py swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/alpine:latest

# Run nginx (background)
python proot_runner.py -d nginx:alpine

# With environment variables and mounts
python proot_runner.py -e "API_KEY=sk-12345" -b /host/data:/data alpine:latest
```

### Step-by-Step Operation
```bash
# 1. Download image
python create_rootfs_tar.py alpine:latest

# 2. Run container
python proot_runner.py rootfs.tar.gz
```

## Key Features

- ✅ **Zero External Dependencies**: Only requires curl, tar and Python standard library
- ✅ **One-Stop Service**: Direct image URL execution with auto-download and caching
- ✅ **Docker-Style CLI**: Familiar `-e`, `-b`, `-w`, `-d` parameters
- ✅ **Multi-Architecture**: ARM64, AMD64, etc.
- ✅ **Android Optimized**: Specially optimized for Termux environment

## Common Parameters

### create_rootfs_tar.py
```bash
python create_rootfs_tar.py [IMAGE_URL] [-o OUTPUT_FILE] [-v]
```

### proot_runner.py
```bash
python proot_runner.py [OPTIONS] IMAGE_URL_OR_TAR [COMMAND]

-e KEY=VALUE    Set environment variable
-b HOST:CONTAINER  Bind mount
-w DIR          Working directory
-d              Run in background
-v              Verbose logging
--list-cache    List cached images
--clear-cache   Clear cache
```

## Troubleshooting

```bash
# Check dependencies
curl --version && tar --version && proot --version

# Verbose logging
python proot_runner.py -v alpine:latest

# Clear cache and retry
python proot_runner.py --clear-cache all
```

## Limitations

- Based on proot, not full containerization (no process/network isolation)
- Some system calls may not be supported
- Performance is lower compared to native Docker

## License

MIT License
