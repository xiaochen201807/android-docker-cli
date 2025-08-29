# Android Docker CLI

English | [中文](README_ZH.md)

A tool to run Docker images on Android using `proot`, without needing a Docker engine. This project is designed to be used within the [Termux](https://github.com/termux/termux-app) application, providing a Docker-like command-line interface to manage persistent containers.

## Core Features

- **Modular Codebase**: All core logic is organized within the `android_docker` package.
- **Main CLI**: The main entry point is `android_docker/docker_cli.py`, providing a Docker-style CLI for full container lifecycle management.
- **Persistent Containers**: Containers have a persistent filesystem and can be started, stopped, and restarted.
- **Underlying Engine**: Uses `android_docker/proot_runner.py` to execute containers and `android_docker/create_rootfs_tar.py` to download and prepare container images.

## Installation

You can install this tool using the following methods:

## Method 1: Install from source (Recommended)

```bash
# Clone the project
git clone <your-repository-url>
cd android-docker-cli

# Install dependencies
pip install -r requirements.txt

# Create symlink to system path (optional)
sudo ln -s $(pwd)/android_docker/docker_cli.py /usr/local/bin/docker
```

## Method 2: Run directly

```bash
# Clone and run directly
git clone <your-repository-url>
cd android-docker-cli
python -m android_docker.docker_cli --help
```

## Install Dependencies

```bash
# Android Termux
pkg update && pkg install python proot curl tar

# Ubuntu/Debian
sudo apt install python3 proot curl tar
```

## Quick Start

After installation, you can use this tool just like the standard Docker command line.

```bash
# Log in to a Docker registry (e.g., Docker Hub)
docker login

# Pull an image from a private registry after logging in
docker login your-private-registry.com
docker pull your-private-registry.com/my-image

# Pull a public image
docker pull alpine:latest

# Run a container in the foreground
docker run alpine:latest echo "Hello from container"

# Run a container in the background (detached)
docker run -d -e "API_KEY=sk-12345" --volume /sdcard:/data nginx:alpine

# Run a container interactively
docker run -it swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/alpine:latest /bin/sh

# Run an Nginx container with a custom configuration file from the project
# This example uses the `examples/nginx.conf` file, which listens on port 8777.
docker run -d --name my-nginx -v $(pwd)/examples/nginx.conf:/etc/nginx/nginx.conf nginx:alpine

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View container logs
docker logs <container_id>
docker logs -f <container_id>  # Follow logs

# Stop a container
docker stop <container_id>

# Start a stopped container
docker start <container_id>

# Restart a container
docker restart <container_id>

# Remove a container
docker rm <container_id>

# Attach to a running container
docker attach <container_id>

# Execute a command in a running container
docker exec <container_id> ls -l
docker exec -it <container_id> /bin/sh

# List cached images
docker images

# Remove a cached image
docker rmi alpine:latest

# Log in to a registry
docker login your-private-registry.com
```

## Docker Compose Support

This tool includes a `docker-compose` command to manage multi-container applications.

```bash
# Start services defined in docker-compose.yml
docker-compose up

# Run in detached mode
docker-compose up -d

# Stop and remove services
docker-compose down
```

### Sample `docker-compose.yml`

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

## Key Features

- ✅ **Full Container Lifecycle**: `run`, `ps`, `stop`, `start`, `restart`, `logs`, `rm`, `attach`, `exec`.
- ✅ **Registry Authentication**: `login` to private or public registries.
- ✅ **Docker Compose Support**: Manage multi-container setups with `docker-compose up` and `down`.
- ✅ **Docker-Style CLI**: A familiar and intuitive command-line interface.
- ✅ **Persistent Storage**: Containers maintain their state and filesystem across restarts, stored in `~/.docker_proot_cache/`.
- ✅ **Android Optimized**: Specially optimized for the Termux environment.

## Troubleshooting

```bash
# Check dependencies
curl --version && tar --version && proot --version

# Use verbose logging for more details
docker --verbose run alpine:latest
```

## Limitations

- Based on `proot`, not full containerization (no kernel-level process or network isolation).
- Some system calls may not be supported.
- Performance is lower compared to native Docker.

## License

MIT License
