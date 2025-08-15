# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## High-level code architecture and structure

This project provides a Docker-like command-line interface for running containers on Android using `proot`. It is designed to be used within the Termux environment.

The main components of the project are:

-   **`docker_cli.py`**: The main entry point for the CLI. It parses commands and orchestrates container management. It is responsible for managing container metadata, which is stored in `~/.docker_proot_cache/containers.json`.
-   **`proot_runner.py`**: This script is responsible for running containers using `proot`. It handles the details of setting up the container's root filesystem and executing commands within it.
-   **`create_rootfs_tar.py`**: This script downloads Docker images and prepares them as root filesystem archives for use with `proot`.
-   **`install.sh`**: This script installs the tool and its dependencies.
-   **`docker_compose_cli.py`**: This new script provides `docker-compose`-like functionality, allowing you to define and run multi-container applications using a `docker-compose.yml` file.

## Commonly used commands

The project provides a Docker-style CLI for managing containers. Here are some of the most common commands:

-   **Install dependencies**:
    -   On Android (Termux): `pkg update && pkg install python proot curl tar`
    -   On Ubuntu/Debian: `sudo apt install python3 proot curl tar`
-   **Pull an image**: `docker pull <image_url>`
-   **Run a container**: `docker run <image_url> [command]`
-   **List running containers**: `docker ps`
-   **List all containers**: `docker ps -a`
-   **Stop a container**: `docker stop <container_id>`
-   **Remove a container**: `docker rm <container_id>`
-   **View container logs**: `docker logs <container_id>`
-   **List cached images**: `docker images`
-   **Remove a cached image**: `docker rmi <image_url>`

## Docker Compose-like commands

-   **Bring up services**: `python docker_compose_cli.py up`
    -   This will read the `docker-compose.yml` file in the current directory and create/start the defined services.
-   **Bring down services**: `python docker_compose_cli.py down`
    -   This will stop and remove the containers defined in the `docker-compose.yml` file.

