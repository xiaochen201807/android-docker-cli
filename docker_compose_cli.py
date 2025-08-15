#!/usr/bin/env python3

import argparse
import subprocess
import os
import yaml
import shlex
import sys
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 获取当前脚本的目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKER_CLI_PATH = os.path.join(SCRIPT_DIR, 'docker_cli_wrapper.py')

def run_docker_cli_command(command, args, detach=False):
    cmd = [sys.executable, DOCKER_CLI_PATH, command] + args
    logger.info(f"Executing: {' '.join(cmd)}")
    try:
        if detach:
            # 使用 Popen 启动后台进程，不等待其完成
            subprocess.Popen(cmd)
        else:
            # 使用 run 等待前台进程完成
            subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

def parse_compose_file(file_path="docker-compose.yml"):
    if not os.path.exists(file_path):
        logger.error(f"Compose file not found: {file_path}")
        sys.exit(1)
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def cmd_up(args):
    compose_config = parse_compose_file(args.file)
    if not compose_config or 'services' not in compose_config:
        logger.error("No services defined in compose file.")
        sys.exit(1)

    project_name = os.path.basename(os.getcwd()) # Use current directory name as project name

    for service_name, service_config in compose_config['services'].items():
        image = service_config.get('image')
        container_name = service_config.get('container_name', f"{project_name}-{service_name}")
        command = service_config.get('command')

        if not image:
            logger.error(f"Service '{service_name}' is missing an image.")
            continue

        logger.info(f"Starting service: {service_name} (Container: {container_name})")
        run_docker_cli_command(
            'run',
            (['-d'] if args.detach else []) + ['--name', container_name, image] + (['--'] + shlex.split(command) if command else []),
            detach=args.detach
        )
        time.sleep(1) # Add a short delay to avoid race conditions


def cmd_down(args):
    compose_config = parse_compose_file(args.file)
    if not compose_config or 'services' not in compose_config:
        logger.info("No services defined in compose file, nothing to stop/remove.")
        sys.exit(0)

    project_name = os.path.basename(os.getcwd()) # Use current directory name as project name

    for service_name, service_config in compose_config['services'].items():
        container_name = service_config.get('container_name', f"{project_name}-{service_name}")
        logger.info(f"Stopping service: {service_name} (Container: {container_name})")
        run_docker_cli_command('stop', [container_name])
        logger.info(f"Removing service: {service_name} (Container: {container_name})")
        run_docker_cli_command('rm', [container_name])

def main():
    parser = argparse.ArgumentParser(
        description='Docker Compose-like CLI for Android Docker CLI'
    )
    parser.add_argument(
        '-f', '--file',
        default='docker-compose.yml',
        help='Specify an alternate compose file (default: docker-compose.yml)'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    up_parser = subparsers.add_parser('up', help='Create and start containers')
    up_parser.add_argument('-d', '--detach', action='store_true', help='后台运行容器')
    up_parser.set_defaults(func=cmd_up)

    down_parser = subparsers.add_parser('down', help='Stop and remove containers')
    down_parser.set_defaults(func=cmd_down)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
