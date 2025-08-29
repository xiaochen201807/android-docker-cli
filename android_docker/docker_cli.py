#!/usr/bin/env python3
"""
Docker风格的命令行接口
模仿Docker命令行工具，提供pull、run、ps、images等命令
用于管理通过proot运行的容器
"""

import os
import sys
import argparse
import json
import logging
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime
import getpass
from urllib.parse import urlparse

# 导入现有模块
from .proot_runner import ProotRunner
from .create_rootfs_tar import DockerImageToRootFS

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DockerCLI:
    """Docker风格的命令行接口"""
    
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or self._get_default_cache_dir()
        self.runner = ProotRunner(cache_dir=self.cache_dir)
        self.containers_file = os.path.join(self.cache_dir, 'containers.json')
        self.config_file = self._get_config_file_path()
        self._ensure_cache_dir()
        
    def _get_default_cache_dir(self):
        """获取默认缓存目录"""
        home_dir = os.path.expanduser('~')
        return os.path.join(home_dir, '.docker_proot_cache')

    def _get_config_file_path(self):
        """获取配置文件的路径"""
        return os.path.join(self.cache_dir, 'config.json')

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _load_containers(self):
        """加载容器信息"""
        if os.path.exists(self.containers_file):
            try:
                with open(self.containers_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取容器信息失败: {e}")
        return {}
        
    def _save_containers(self, containers):
        """保存容器信息"""
        try:
            with open(self.containers_file, 'w') as f:
                json.dump(containers, f, indent=2)
        except Exception as e:
            logger.error(f"保存容器信息失败: {e}")

    def _load_config(self):
        """加载配置信息，包括认证凭证"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取配置文件失败: {e}")
        return {'auths': {}}

    def _save_config(self, config):
        """保存配置信息"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            
    def _generate_container_id(self):
        """生成容器ID"""
        import hashlib
        import uuid
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12]
    def _is_process_running(self, pid):
        """检查进程是否还在运行"""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def _get_container_dir(self, container_id):
        """获取容器的持久化数据目录"""
        return os.path.join(self.cache_dir, 'containers', container_id)

    def _get_pid_file(self, container_dir):
        """获取PID文件路径"""
        return os.path.join(container_dir, 'container.pid')

    def _get_log_file(self, container_dir):
        """获取日志文件路径"""
        return os.path.join(container_dir, 'container.log')

            
    def login(self, server, username, password):
        """登录到Docker Registry"""
        if not username:
            username = input("Username: ")
        if not password:
            password = getpass.getpass("Password: ")

        config = self._load_config()
        if 'auths' not in config:
            config['auths'] = {}
        
        # 默认服务器为Docker Hub
        if not server:
            server = "https://index.docker.io/v1/"

        config['auths'][server] = {
            'username': username,
            'password': password # For simplicity, storing plain text.
        }
        self._save_config(config)
        logger.info(f"登录成功: {server}")
        return True

    def pull(self, image_url, force=False, quiet=False):
        """拉取镜像"""
        if not quiet:
            logger.info(f"拉取镜像: {image_url}")

        # 检查是否已缓存
        if not force and self.runner._is_image_cached(image_url):
            cache_info = self.runner._load_cache_info(image_url)
            if cache_info:
                if not quiet:
                    logger.info(f"镜像已存在于缓存中")
                    logger.info(f"缓存时间: {cache_info.get('created_time_str', 'Unknown')}")
                else:
                    # 在quiet模式下，只输出镜像ID或名称
                    print(image_url)
                return True

        # 加载凭证
        config = self._load_config()
        auths = config.get('auths', {})
        
        # 简单的匹配逻辑，实际可能需要更复杂的匹配
        # 这里我们假设镜像URL的域名部分能匹配到auths中的key
        username, password = None, None
        for server, creds in auths.items():
            server_name = urlparse(server).hostname or server
            if server_name in image_url or (server_name == "index.docker.io" and '/' not in image_url.split(':')[0]):
                username = creds.get('username')
                password = creds.get('password')
                logger.info(f"找到 {server} 的凭证")
                break
        
        # 现在pull直接调用runner的下载方法
        if quiet:
            # 在quiet模式下，临时抑制日志输出
            original_level = logging.getLogger().level
            logging.getLogger().setLevel(logging.ERROR)
            
        try:
            cache_path = self.runner._download_image(
                image_url,
                force_download=force,
                username=username,
                password=password,
                quiet=quiet
            )
        finally:
            if quiet:
                # 恢复原始日志级别
                logging.getLogger().setLevel(original_level)

        if cache_path:
            if not quiet:
                logger.info(f"✓ 镜像拉取成功: {image_url}")
            else:
                # 在quiet模式下，只输出镜像ID或名称
                print(image_url)
            return True
        else:
            if not quiet:
                logger.error(f"✗ 镜像拉取失败: {image_url}")
            return False
            
    def run(self, image_url, command=None, name=None, **kwargs):
        """运行容器"""
        # 确保在运行前镜像存在
        if not self.runner._is_image_cached(image_url) or kwargs.get('force_download', False):
            logger.info(f"镜像不存在或需要强制下载，执行 'pull' 操作...")
            pull_success = self.pull(image_url, force=kwargs.get('force_download', False), quiet=False)
            if not pull_success:
                logger.error(f"无法运行容器，因为镜像拉取失败: {image_url}")
                return None

        container_id = name if name else self._generate_container_id()
        container_dir = self._get_container_dir(container_id)
        os.makedirs(container_dir, exist_ok=True)
        
        # 构建运行参数
        class Args:
            def __init__(self):
                self.env = kwargs.get('env', [])
                self.bind = kwargs.get('bind', [])
                for v in self.bind:
                    host_path = v.split(':')[0]
                    if not os.path.exists(host_path):
                        # 仅记录警告，而不是中止，因为某些路径可能在容器启动后才可用
                        logger.warning(f"卷挂载的源路径不存在: {host_path}")
                self.workdir = kwargs.get('workdir')
                self.detach = kwargs.get('detach', False)
                self.interactive = kwargs.get('interactive', False)
                self.force_download = kwargs.get('force_download', False)
                self.username = kwargs.get('username')
                self.password = kwargs.get('password')
                self.command = command
                if self.command and self.command[0] == '--':
                    self.command = self.command[1:]
                
        args = Args()
        
        # 记录容器信息
        containers = self._load_containers()
        container_info = {
            'id': container_id,
            'image': image_url,
            'name': name,
            'command': command or [],
            'created': time.time(),
            'created_str': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'created',
            'pid': None,
            'container_dir': container_dir, 
            'detached': args.detach,
            'run_args': { # Store all arguments needed to restart
                'env': args.env,
                'bind': args.bind,
                'workdir': args.workdir,
            }
        }
        
        containers[container_id] = container_info
        self._save_containers(containers)

        logger.info(f"启动容器: {container_id}")
        
        try:
            # Run container
            if args.detach:
                success = self._run_detached(image_url, args, container_id, container_dir)
            else:
                # For foreground mode, ProotRunner handles the temporary rootfs.
                container_info['status'] = 'running'
                containers[container_id] = container_info
                self._save_containers(containers)
                
                # We pass None for rootfs_dir so ProotRunner creates a temporary one
                success = self.runner.run(image_url, args, rootfs_dir=None)
                
                # Update status after completion
                container_info['status'] = 'exited'
                container_info['finished'] = time.time()
                container_info['finished_str'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                containers[container_id] = container_info
                # In foreground mode, the temporary rootfs is cleaned up by ProotRunner,
                # so we can remove the persistent container dir.
                if os.path.exists(container_dir):
                    import shutil
                    shutil.rmtree(container_dir)
                del containers[container_id]
                self._save_containers(containers)
                
            if success:
                if args.detach:
                    logger.info(f"容器 {container_id} 已在后台启动")
                else:
                    logger.info(f"容器 {container_id} 运行完成")
                return container_id
            else:
                container_info['status'] = 'failed'
                containers[container_id] = container_info
                self._save_containers(containers)
                return None
                
        except KeyboardInterrupt:
            container_info['status'] = 'interrupted'
            containers[container_id] = container_info
            self._save_containers(containers)
            logger.info(f"容器 {container_id} 被用户中断")
            return container_id
            
    def _run_detached(self, image_url, args, container_id, container_dir):
        """后台运行容器, 直接调用proot_runner.py脚本"""
        rootfs_dir = os.path.join(container_dir, 'rootfs')
        pid_file = self._get_pid_file(container_dir)
        log_file = self._get_log_file(container_dir)

        # 构建proot_runner.py的命令行参数
        cmd = [
            sys.executable,
            '-m', 'android_docker.proot_runner',
            '--rootfs-dir', rootfs_dir,
            '--pid-file', pid_file,
            '--log-file', log_file,
            '--detach',
        ]
        
        # 统一从args对象获取凭证
        if hasattr(args, 'username') and args.username:
            cmd.extend(['--username', args.username])
        if hasattr(args, 'password') and args.password:
            cmd.extend(['--password', args.password])

        # 添加从docker_cli传递过来的参数
        if args.force_download:
            cmd.append('--force-download')
        if args.workdir:
            cmd.extend(['--workdir', args.workdir])
        if args.interactive:
            cmd.append('--interactive')
        for e in args.env:
            cmd.extend(['-e', e])
        for b in args.bind:
            cmd.extend(['-b', b])
        
        # 添加镜像URL和命令
        # 添加 -- 分隔符来区分 proot_runner.py 的参数和容器的命令
        cmd.append(image_url)
        if args.command:
            cmd.append('--')
            cmd.extend(args.command)

        try:
            logger.debug(f"Executing detached command: {' '.join(cmd)}")
            # 打开日志文件用于重定向输出
            with open(log_file, 'a') as lf:
                lf.write(f"--- Starting container at {datetime.now()} ---\\n")
                process = subprocess.Popen(
                    cmd,
                    stdout=lf,
                    stderr=lf,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            # 等待pid文件被创建，最多等待5秒
            pid = None
            # 延长等待时间至15秒 (30 * 0.5s)
            for i in range(30):
                time.sleep(0.5)
                if os.path.exists(pid_file):
                    with open(pid_file, 'r') as pf:
                        pid_str = pf.read().strip()
                        if pid_str:
                            try:
                                pid = int(pid_str)
                                logger.debug(f"成功从PID文件获取PID: {pid}")
                                break
                            except ValueError:
                                logger.debug(f"PID文件内容无效: '{pid_str}'，继续等待...")
                logger.debug(f"等待PID文件... (尝试 {i+1}/30)")
            
            if not pid:
                logger.error("无法获取后台进程的PID，启动可能失败。")
                logger.error(f"请查看日志文件获取更多信息: {log_file}")
                return False

            # 更新容器信息
            containers = self._load_containers()
            containers[container_id]['status'] = 'running'
            containers[container_id]['pid'] = pid
            self._save_containers(containers)
            
            return True
            
        except Exception as e:
            logger.error(f"启动后台容器失败: {e}")
            logger.error(f"请查看日志文件获取更多信息: {log_file}")
            return False

            
    def _cleanup_stale_lock_files(self, rootfs_dir):
        """在重启前清理常见的陈旧锁文件或PID文件"""
        logger.debug(f"正在清理根文件系统中的陈旧锁文件: {rootfs_dir}")
        lock_dirs = ['run', 'var/run', 'tmp']
        cleaned_files = 0

        for l_dir in lock_dirs:
            full_dir_path = os.path.join(rootfs_dir, l_dir.lstrip('/'))
            if os.path.isdir(full_dir_path):
                try:
                    for filename in os.listdir(full_dir_path):
                        if filename.endswith('.pid'):
                            file_path = os.path.join(full_dir_path, filename)
                            try:
                                os.remove(file_path)
                                logger.debug(f"已删除陈旧的PID文件: {file_path}")
                                cleaned_files += 1
                            except OSError as e:
                                logger.warning(f"删除PID文件失败 {file_path}: {e}")
                except Exception as e:
                    logger.warning(f"扫描目录失败 {full_dir_path}: {e}")
        
        if cleaned_files > 0:
            logger.info(f"清理了 {cleaned_files} 个陈旧的PID/锁文件。")
        else:
            logger.debug("未找到需要清理的陈旧PID/锁文件。")

    def start(self, container_id):
        """启动一个已停止的容器，并保持其ID和数据不变"""
        containers = self._load_containers()
        if container_id not in containers:
            logger.error(f"容器不存在: {container_id}")
            return False

        container_info = containers[container_id]
        status = container_info.get('status')

        if status == 'running':
            logger.error(f"容器 {container_id} 已经在运行")
            return False

        if status not in ['created', 'exited', 'killed', 'interrupted', 'failed']:
            logger.error(f"无法启动处于 '{status}' 状态的容器 {container_id}")
            return False

        logger.info(f"正在启动容器: {container_id}")

        image_url = container_info['image']
        command = container_info['command']
        run_args = container_info.get('run_args', {})
        is_detached = container_info.get('detached', False)
        container_dir = container_info.get('container_dir')

        if not container_dir or not os.path.exists(container_dir):
            logger.error(f"找不到容器 {container_id} 的数据目录。")
            return False

        rootfs_dir = os.path.join(container_dir, 'rootfs')
        if not os.path.exists(rootfs_dir):
            logger.error(f"找不到容器 {container_id} 的根文件系统。")
            return False

        # 清理旧的锁文件，这是关键修复
        self._cleanup_stale_lock_files(rootfs_dir)

        class Args:
            def __init__(self):
                self.env = run_args.get('env', [])
                self.bind = run_args.get('bind', [])
                self.workdir = run_args.get('workdir')
                self.command = command
                self.detach = is_detached
                self.interactive = run_args.get('interactive', False)
                self.force_download = False

        args = Args()

        if is_detached:
            # For detached containers, we can reuse the _run_detached logic
            # It will handle logging, PID files, and command construction correctly.
            # We must first update the container status to 'restarting' or similar
            # because _run_detached assumes it's creating a new container.
            # However, a simpler fix is to call it and then update the container info.
            # The _run_detached method already saves container status.
            logger.info(f"Calling _run_detached to restart container {container_id}")
            success = self._run_detached(image_url, args, container_id, container_dir)
            
            if success:
                logger.info(f"容器 {container_id} 已成功启动")
            else:
                logger.error(f"启动容器 {container_id} 失败")

            return success
        else:
            # Foreground restart logic remains the same
            container_info['status'] = 'running'
            containers[container_id] = container_info
            self._save_containers(containers)
            success = self.runner.run(image_url, args, rootfs_dir=rootfs_dir)
            
            containers = self._load_containers()
            container_info = containers.get(container_id, {})
            container_info['status'] = 'exited'
            container_info['finished'] = time.time()
            container_info['finished_str'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            containers[container_id] = container_info
            self._save_containers(containers)
            return success

    def restart(self, container_id):
        """重启一个容器"""
        logger.info(f"正在重启容器: {container_id}")

        # 1. 停止容器 (如果正在运行)
        containers = self._load_containers()
        if container_id not in containers:
            logger.error(f"容器不存在: {container_id}")
            return False

        status = containers[container_id].get('status')
        if status == 'running':
            stop_success = self.stop(container_id)
            if not stop_success:
                logger.error(f"无法停止容器 {container_id}，重启失败")
                return False

        # 2. 启动容器
        start_success = self.start(container_id)
        if start_success:
            logger.info(f"成功重启容器 {container_id}")
        else:
            logger.error(f"重启容器 {container_id} 失败")

        return start_success

    def logs(self, container_id, follow=False):
        """显示容器的日志"""
        containers = self._load_containers()
        if container_id not in containers:
            logger.error(f"容器不存在: {container_id}")
            return False

        container_info = containers[container_id]
        container_dir = container_info.get('container_dir')
        if not container_dir:
            logger.error(f"找不到容器 {container_id} 的日志文件路径")
            return False
            
        log_file = self._get_log_file(container_dir)
        if not os.path.exists(log_file):
            logger.info(f"容器 {container_id} 没有日志")
            return True

        try:
            with open(log_file, 'r') as f:
                if not follow:
                    # Print existing content and exit
                    print(f.read(), end='')
                    return True
                else:
                    # Follow mode (like tail -f)
                    # Print existing content first
                    print(f.read(), end='')
                    # Then wait for new content
                    while True:
                        line = f.readline()
                        if not line:
                            time.sleep(0.1)
                            continue
                        print(line, end='')
        except KeyboardInterrupt:
            print() # Print a newline after Ctrl+C
            return True
        except Exception as e:
            logger.error(f"读取日志失败: {e}")
            return False

    def attach(self, container_id):
        """通过在容器中执行一个交互式shell来附加到容器"""
        logger.info(f"附加到容器 {container_id} (通过 'exec -it <shell>' 实现)")
        logger.info("输入 'exit' 或按 Ctrl+D 退出.")
        # Attach is implemented by executing an interactive shell in the container.
        return self.exec(container_id, [], interactive=True)

    def exec(self, container_id, command, interactive=False):
        """在运行中的容器中执行命令"""
        containers = self._load_containers()
        if container_id not in containers:
            logger.error(f"容器不存在: {container_id}")
            return False

        container_info = containers[container_id]
        status = container_info.get('status')
        if status != 'running':
            logger.error(f"容器 {container_id} 未在运行中")
            return False

        pid = container_info.get('pid')
        if not pid:
            logger.error(f"容器 {container_id} 没有PID信息")
            return False

        if not self._is_process_running(pid):
            logger.error(f"容器 {container_id} 进程未运行")
            return False

        # Get container directory and rootfs path
        container_dir = container_info.get('container_dir')
        if not container_dir:
            logger.error(f"找不到容器 {container_id} 的目录")
            return False

        rootfs_dir = os.path.join(container_dir, 'rootfs')
        if not os.path.exists(rootfs_dir):
            logger.error(f"找不到容器 {container_id} 的根文件系统")
            return False

        # Build exec command using proot
        proot_cmd = ['proot', '-r', rootfs_dir]
        
        # Add default binds
        default_binds = ['/dev', '/proc', '/sys']
        for bind in default_binds:
            if os.path.exists(bind):
                proot_cmd.extend(['-b', bind])

        # Add user specified binds from original container
        original_binds = container_info.get('run_args', {}).get('bind', [])
        for bind in original_binds:
            proot_cmd.extend(['-b', bind])

        # Set working directory
        workdir = container_info.get('run_args', {}).get('workdir') or '/'
        proot_cmd.extend(['-w', workdir])

        # If no command provided, use default shell
        if not command:
            # Find available shell
            default_shells = ['/bin/bash', '/bin/sh']
            shell = '/bin/sh'  # default fallback
            for s in default_shells:
                shell_path = os.path.join(rootfs_dir, s.lstrip('/'))
                if os.path.exists(shell_path):
                    shell = s
                    break
            command = [shell]
        elif isinstance(command, str):
            # If command is a string, convert it to a list
            command = [command]
        
        # Ensure command is a list and not None
        if not isinstance(command, list):
            command = [str(command)] if command else ['/bin/sh']

        # Add the command to execute
        proot_cmd.extend(command)

        logger.info(f"在容器 {container_id} 中执行命令: {' '.join(command)}")
        
        try:
            if interactive:
                # Interactive mode: connect stdin/stdout/stderr
                env = os.environ.copy()
                # Remove LD_PRELOAD for Android Termux compatibility
                if 'LD_PRELOAD' in env:
                    del env['LD_PRELOAD']
                subprocess.run(proot_cmd, env=env)
            else:
                # Non-interactive mode: capture output
                env = os.environ.copy()
                # Remove LD_PRELOAD for Android Termux compatibility
                if 'LD_PRELOAD' in env:
                    del env['LD_PRELOAD']
                result = subprocess.run(proot_cmd, env=env, capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout, end='')
                if result.stderr:
                    print(result.stderr, end='', file=sys.stderr)
                return result.returncode == 0
            return True
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return False

    def ps(self, all_containers=False):
        """列出容器"""
        containers = self._load_containers()
        
        if not containers:
            logger.info("没有容器")
            return
            
        # 更新运行中容器的状态
        for container_id, info in containers.items():
            if info.get('status') == 'running' and info.get('pid'):
                # 对于通过新方法启动的容器，pid是proot进程的真实pid
                if not self._is_process_running(info['pid']):
                    info['status'] = 'exited'
                    info['finished'] = time.time()
                    info['finished_str'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif info.get('status') == 'running' and info.get('script_path'):
                 # 兼容旧的、通过wrapper script启动的容器
                if not self._is_process_running(info['pid']):
                    info['status'] = 'exited'
                    info['finished'] = time.time()
                    info['finished_str'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        
        self._save_containers(containers)
        
        # 过滤容器
        if not all_containers:
            containers = {k: v for k, v in containers.items() 
                         if v.get('status') in ['running', 'created']}
            
        if not containers:
            logger.info("没有运行中的容器")
            return
            
        # 显示容器列表
        print(f"{'CONTAINER ID':<12} {'IMAGE':<30} {'COMMAND':<20} {'CREATED':<20} {'STATUS':<10}")
        print("-" * 100)
        
        for container_id, info in containers.items():
            image = info.get('image', 'unknown')[:28]
            command = ' '.join(info.get('command', []))[:18] or 'default'
            created = info.get('created_str', 'unknown')
            status = info.get('status', 'unknown')
            
            print(f"{container_id:<12} {image:<30} {command:<20} {created:<20} {status:<10}")
            
    def images(self):
        """列出镜像"""
        logger.info("列出缓存的镜像:")
        self.runner.list_cache()
        
    def rmi(self, image_url):
        """删除镜像"""
        logger.info(f"删除镜像: {image_url}")
        try:
            self.runner.clear_cache(image_url)
            return True
        except Exception as e:
            logger.error(f"删除镜像失败: {e}")
            return False
        
    def stop(self, container_id):
        """停止容器"""
        containers = self._load_containers()
        
        if container_id not in containers:
            logger.error(f"容器不存在: {container_id}")
            return False
            
        container_info = containers[container_id]
        pid = container_info.get('pid')
        
        if pid and not self._is_process_running(pid):
            logger.info(f"容器 {container_id} 进程已停止，更新状态为 'exited'")
            container_info['status'] = 'exited'
            container_info['finished'] = time.time()
            container_info['finished_str'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_containers(containers)
            return True

        # 如果没有PID，或者PID对应的进程没有运行，并且容器状态不是运行中，则直接认为已停止
        if not pid or not self._is_process_running(pid):
            if container_info.get('status') in ['exited', 'killed', 'failed', 'created']:
                logger.info(f"容器 {container_id} 已经停止或处于非运行状态 ({container_info.get('status')}).")
                # 确保状态被正确更新，即使PID缺失
                if container_info.get('status') != 'exited':
                    container_info['status'] = 'exited'
                    container_info['finished'] = time.time()
                    container_info['finished_str'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._save_containers(containers)
                return True
            else:
                logger.warning(f"容器 {container_id} 没有有效的PID信息或进程未运行，但状态为 {container_info.get('status')}. 尝试强制停止.")
                # 对于那些状态异常（如'running'但无PID或进程），尝试强制清理
                # 这部分逻辑需要非常小心，以避免误删数据
                # 对于docker-compose down场景，如果stop失败，rm会接管清理工作
                # 所以这里主要目的是让stop返回True，让rm可以继续执行
                container_info['status'] = 'exited' # 强制标记为已退出，以便rm可以处理
                container_info['finished'] = time.time()
                container_info['finished_str'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_containers(containers)
                return True
            
        try:
            # 发送SIGTERM信号到整个进程组
            os.killpg(pid, signal.SIGTERM)
            logger.info(f"已发送停止信号给容器进程组 {container_id} (PGID: {pid})")
            
            # 等待一段时间后检查是否停止
            time.sleep(2)
            if not self._is_process_running(pid):
                container_info['status'] = 'exited'
                container_info['finished'] = time.time()
                container_info['finished_str'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                containers[container_id] = container_info
                self._save_containers(containers)
                logger.info(f"容器 {container_id} 已停止")
                return True
            else:
                logger.warning(f"容器 {container_id} 未响应SIGTERM，尝试SIGKILL")
                os.killpg(pid, signal.SIGKILL)
                container_info['status'] = 'killed'
                containers[container_id] = container_info
                self._save_containers(containers)
                return True
                
        except (OSError, ProcessLookupError) as e:
            logger.error(f"停止容器失败: {e}")
            return False
            
    def rm(self, container_id, force=False):
        """删除容器"""
        containers = self._load_containers()
        
        if container_id not in containers:
            logger.error(f"容器不存在: {container_id}")
            return False
            
        container_info = containers[container_id]
        
        # 检查容器是否在运行
        # 更新状态以防万一
        if container_info.get('status') == 'running' and container_info.get('pid'):
            if not self._is_process_running(container_info['pid']):
                container_info['status'] = 'exited'
        
        if container_info.get('status') == 'running':
            if not force:
                logger.error(f"容器 {container_id} 正在运行，使用 --force 强制删除")
                return False
            else:
                # 强制停止容器
                logger.info(f"强制停止容器: {container_id}")
                self.stop(container_id)
                # 重新加载信息
                containers = self._load_containers()
                container_info = containers.get(container_id, {})
                if not container_info:
                    logger.info(f"容器 {container_id} 在停止后已被移除")
                    return True
                
        # 清理容器的持久化目录
        container_dir = container_info.get('container_dir')
        if container_dir and os.path.isdir(container_dir):
            try:
                import shutil
                shutil.rmtree(container_dir)
                logger.debug(f"已清理容器目录: {container_dir}")
            except OSError as e:
                logger.warning(f"清理容器目录失败 {container_dir}: {e}")

        # 兼容旧的清理逻辑
        rootfs_dir = container_info.get('rootfs_dir')
        if rootfs_dir and os.path.isdir(rootfs_dir):
            try:
                import shutil
                shutil.rmtree(rootfs_dir)
            except OSError:
                pass

        script_path = container_info.get('script_path')
        if script_path and os.path.exists(script_path):
            try:
                os.remove(script_path)
            except OSError:
                pass
                
        # 删除容器记录
        if container_id in containers:
            del containers[container_id]
            self._save_containers(containers)
        
        logger.info(f"容器 {container_id} 已删除")
        return True

    def volume_rm(self, volume_name):
        """删除卷"""
        logger.info(f"删除卷: {volume_name}")
        try:
            # 这里可以实现卷的删除逻辑
            # 例如，如果卷是基于目录的，则删除目录
            # 如果卷是基于文件的，则删除文件
            # 如果卷是基于容器的，则需要停止容器或删除容器
            # 由于proot的限制，这里主要是概念性实现
            logger.warning("卷删除功能在proot环境下有限制，建议手动清理")
            return True
        except Exception as e:
            logger.error(f"删除卷失败: {e}")
            return False

    def build(self, dockerfile_path, tag=None, context_path="."):
        """构建Docker镜像"""
        logger.info(f"构建镜像: {dockerfile_path}")
        # 这里可以实现简单的镜像构建逻辑
        # 由于proot的限制，这里主要是概念性实现
        logger.warning("镜像构建功能在proot环境下有限制，建议使用预构建的镜像")
        return True

    def save(self, image_url, output_path):
        """保存镜像到tar文件"""
        logger.info(f"保存镜像 {image_url} 到 {output_path}")
        try:
            # 获取镜像的rootfs路径
            image_dir = os.path.join(self.cache_dir, 'images', image_url.replace(':', '_'))
            if os.path.exists(image_dir):
                import tarfile
                with tarfile.open(output_path, 'w') as tar:
                    tar.add(image_dir, arcname='.')
                logger.info(f"镜像已保存到 {output_path}")
                return True
            else:
                logger.error(f"镜像 {image_url} 不存在")
                return False
        except Exception as e:
            logger.error(f"保存镜像失败: {e}")
            return False

    def load(self, tar_path):
        """从tar文件加载镜像"""
        logger.info(f"从 {tar_path} 加载镜像")
        try:
            import tarfile
            with tarfile.open(tar_path, 'r') as tar:
                # 提取到临时目录
                temp_dir = os.path.join(self.cache_dir, 'temp_load')
                os.makedirs(temp_dir, exist_ok=True)
                tar.extractall(temp_dir)
                
                # 这里可以添加镜像导入逻辑
                logger.info("镜像加载完成")
                return True
        except Exception as e:
            logger.error(f"加载镜像失败: {e}")
            return False

    def tag(self, source_image, target_image):
        """为镜像添加标签"""
        logger.info(f"为镜像 {source_image} 添加标签 {target_image}")
        try:
            # 检查源镜像是否存在（使用runner的缓存路径）
            if not self.runner._is_image_cached(source_image):
                logger.error(f"源镜像 {source_image} 不存在")
                return False
            
            # 获取源镜像的缓存路径
            source_cache_path = self.runner._get_image_cache_path(source_image)
            target_cache_path = self.runner._get_image_cache_path(target_image)
            
            if os.path.exists(source_cache_path):
                # 复制tar.gz文件
                import shutil
                shutil.copy2(source_cache_path, target_cache_path)
                
                # 复制info文件（如果存在）
                source_info_path = source_cache_path + '.info'
                target_info_path = target_cache_path + '.info'
                if os.path.exists(source_info_path):
                    shutil.copy2(source_info_path, target_info_path)
                
                # 保存新的缓存信息
                self.runner._save_cache_info(target_image, target_cache_path)
                
                logger.info(f"标签添加成功: {target_image}")
                return True
            else:
                logger.error(f"源镜像文件 {source_cache_path} 不存在")
                return False
        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False

    def inspect(self, target):
        """检查容器或镜像的详细信息"""
        logger.info(f"检查 {target} 的详细信息")
        try:
            # 检查是否是容器
            containers = self._load_containers()
            if target in containers:
                container_info = containers[target]
                print(json.dumps(container_info, indent=2, ensure_ascii=False))
                return True
            
            # 检查是否是镜像
            image_dir = os.path.join(self.cache_dir, 'images', target.replace(':', '_'))
            if os.path.exists(image_dir):
                image_info = {
                    'Id': target,
                    'RepoTags': [target],
                    'Created': datetime.fromtimestamp(os.path.getctime(image_dir)).isoformat(),
                    'Size': self._get_dir_size(image_dir),
                    'Architecture': 'unknown',
                    'Os': 'linux'
                }
                print(json.dumps(image_info, indent=2, ensure_ascii=False))
                return True
            
            logger.error(f"未找到容器或镜像: {target}")
            return False
        except Exception as e:
            logger.error(f"检查失败: {e}")
            return False

    def top(self, container_id):
        """显示容器中运行的进程"""
        logger.info(f"显示容器 {container_id} 的进程")
        try:
            containers = self._load_containers()
            if container_id not in containers:
                logger.error(f"容器 {container_id} 不存在")
                return False
            
            container = containers[container_id]
            pid = container.get('pid')
            if not pid or not self._is_process_running(pid):
                logger.error(f"容器 {container_id} 未运行")
                return False
            
            # 使用ps命令查看进程
            try:
                result = subprocess.run(['ps', '-p', str(pid), '-o', 'pid,ppid,cmd'], 
                                      capture_output=True, text=True)
                print(result.stdout)
                return True
            except Exception as e:
                logger.error(f"获取进程信息失败: {e}")
                return False
        except Exception as e:
            logger.error(f"top命令失败: {e}")
            return False

    def stats(self, container_id=None):
        """显示容器的资源使用统计"""
        logger.info("显示容器资源统计")
        try:
            containers = self._load_containers()
            if container_id:
                if container_id not in containers:
                    logger.error(f"容器 {container_id} 不存在")
                    return False
                container_list = [container_id]
            else:
                container_list = list(containers.keys())
            
            print(f"{'容器ID':<12} {'CPU%':<8} {'内存使用':<12} {'内存%':<8} {'网络I/O':<20} {'磁盘I/O':<20}")
            print("-" * 80)
            
            for cid in container_list:
                container = containers[cid]
                pid = container.get('pid')
                if pid and self._is_process_running(pid):
                    # 这里可以添加实际的资源统计逻辑
                    print(f"{cid:<12} {'0.0':<8} {'0 B':<12} {'0.0':<8} {'0 B / 0 B':<20} {'0 B / 0 B':<20}")
                else:
                    print(f"{cid:<12} {'--':<8} {'--':<12} {'--':<8} {'--':<20} {'--':<20}")
            
            return True
        except Exception as e:
            logger.error(f"stats命令失败: {e}")
            return False

    def cp(self, source, dest):
        """在容器和主机之间复制文件"""
        logger.info(f"复制文件: {source} -> {dest}")
        try:
            # 解析源和目标路径
            if ':' in source:
                container_id, container_path = source.split(':', 1)
                is_copy_from_container = True
            elif ':' in dest:
                container_id, container_path = dest.split(':', 1)
                is_copy_from_container = False
            else:
                logger.error("复制命令格式错误，应为: docker cp CONTAINER:CONTAINER_PATH HOST_PATH 或 docker cp HOST_PATH CONTAINER:CONTAINER_PATH")
                return False
            
            containers = self._load_containers()
            if container_id not in containers:
                logger.error(f"容器 {container_id} 不存在")
                return False
            
            container = containers[container_id]
            container_rootfs = container.get('rootfs_dir')
            if not container_rootfs:
                logger.error(f"容器 {container_id} 的rootfs目录不存在")
                return False
            
            if is_copy_from_container:
                # 从容器复制到主机
                source_path = os.path.join(container_rootfs, container_path)
                if os.path.exists(source_path):
                    import shutil
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source_path, dest)
                    logger.info(f"文件已从容器复制到主机: {dest}")
                    return True
                else:
                    logger.error(f"容器内路径不存在: {container_path}")
                    return False
            else:
                # 从主机复制到容器
                dest_path = os.path.join(container_rootfs, container_path)
                if os.path.exists(source):
                    import shutil
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    if os.path.isdir(source):
                        shutil.copytree(source, dest_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, dest_path)
                    logger.info(f"文件已从主机复制到容器: {dest_path}")
                    return True
                else:
                    logger.error(f"主机路径不存在: {source}")
                    return False
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
            return False

    def diff(self, container_id):
        """显示容器文件系统的变更"""
        logger.info(f"显示容器 {container_id} 的文件系统变更")
        try:
            containers = self._load_containers()
            if container_id not in containers:
                logger.error(f"容器 {container_id} 不存在")
                return False
            
            container = containers[container_id]
            container_rootfs = container.get('rootfs_dir')
            if not container_rootfs:
                logger.error(f"容器 {container_id} 的rootfs目录不存在")
                return False
            
            # 这里可以实现文件系统变更检测逻辑
            # 由于proot的限制，这里主要是概念性实现
            logger.info("文件系统变更检测功能在proot环境下有限制")
            return True
        except Exception as e:
            logger.error(f"diff命令失败: {e}")
            return False

    def commit(self, container_id, repository, tag="latest"):
        """从容器创建新镜像"""
        logger.info(f"从容器 {container_id} 创建镜像 {repository}:{tag}")
        try:
            containers = self._load_containers()
            if container_id not in containers:
                logger.error(f"容器 {container_id} 不存在")
                return False
            
            container = containers[container_id]
            container_rootfs = container.get('rootfs_dir')
            if not container_rootfs:
                logger.error(f"容器 {container_id} 的rootfs目录不存在")
                return False
            
            # 创建新镜像目录
            image_name = f"{repository}:{tag}"
            image_dir = os.path.join(self.cache_dir, 'images', image_name.replace(':', '_'))
            
            if os.path.exists(image_dir):
                import shutil
                shutil.rmtree(image_dir)
            
            import shutil
            shutil.copytree(container_rootfs, image_dir)
            
            logger.info(f"镜像创建成功: {image_name}")
            return True
        except Exception as e:
            logger.error(f"创建镜像失败: {e}")
            return False

    def export(self, container_id, output_path):
        """导出容器文件系统到tar文件"""
        logger.info(f"导出容器 {container_id} 到 {output_path}")
        try:
            containers = self._load_containers()
            if container_id not in containers:
                logger.error(f"容器 {container_id} 不存在")
                return False
            
            container = containers[container_id]
            container_rootfs = container.get('rootfs_dir')
            if not container_rootfs:
                logger.error(f"容器 {container_id} 的rootfs目录不存在")
                return False
            
            import tarfile
            with tarfile.open(output_path, 'w') as tar:
                tar.add(container_rootfs, arcname='.')
            
            logger.info(f"容器已导出到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出容器失败: {e}")
            return False

    def import_(self, tar_path, repository, tag="latest"):
        """从tar文件导入镜像"""
        logger.info(f"从 {tar_path} 导入镜像 {repository}:{tag}")
        try:
            import tarfile
            image_name = f"{repository}:{tag}"
            image_dir = os.path.join(self.cache_dir, 'images', image_name.replace(':', '_'))
            
            if os.path.exists(image_dir):
                import shutil
                shutil.rmtree(image_dir)
            
            os.makedirs(image_dir, exist_ok=True)
            
            with tarfile.open(tar_path, 'r') as tar:
                tar.extractall(image_dir)
            
            logger.info(f"镜像导入成功: {image_name}")
            return True
        except Exception as e:
            logger.error(f"导入镜像失败: {e}")
            return False

    def history(self, image_url):
        """显示镜像的历史记录"""
        logger.info(f"显示镜像 {image_url} 的历史记录")
        try:
            image_dir = os.path.join(self.cache_dir, 'images', image_url.replace(':', '_'))
            if not os.path.exists(image_dir):
                logger.error(f"镜像 {image_url} 不存在")
                return False
            
            # 由于proot的限制，这里主要是概念性实现
            print(f"IMAGE          CREATED       CREATED BY                                      SIZE      COMMENT")
            print(f"{image_url:<15} {datetime.fromtimestamp(os.path.getctime(image_dir)):<13} /bin/sh -c #(nop) ADD file:...   0 B")
            logger.info("历史记录功能在proot环境下有限制")
            return True
        except Exception as e:
            logger.error(f"history命令失败: {e}")
            return False

    def info(self):
        """显示系统信息"""
        logger.info("显示系统信息")
        try:
            import platform
            import psutil
            
            info = {
                'Containers': len(self._load_containers()),
                'Images': len([d for d in os.listdir(os.path.join(self.cache_dir, 'images')) if os.path.isdir(os.path.join(self.cache_dir, 'images', d))]),
                'System Time': datetime.now().isoformat(),
                'Operating System': platform.system(),
                'Architecture': platform.machine(),
                'Kernel Version': platform.release(),
                'Total Memory': f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
                'Available Memory': f"{psutil.virtual_memory().available / (1024**3):.2f} GB",
                'Cache Directory': self.cache_dir
            }
            
            for key, value in info.items():
                print(f"{key}: {value}")
            
            return True
        except Exception as e:
            logger.error(f"info命令失败: {e}")
            return False

    def version(self):
        """显示版本信息"""
        logger.info("显示版本信息")
        try:
            import platform
            version_info = {
                'Version': '1.0.0',
                'API Version': '1.41',
                'Go Version': 'N/A',
                'Git Commit': 'N/A',
                'Built': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'OS/Arch': f"{platform.system()}/{platform.machine()}",
                'Experimental': 'false'
            }
            
            for key, value in version_info.items():
                print(f"{key}: {value}")
            
            return True
        except Exception as e:
            logger.error(f"version命令失败: {e}")
            return False

    def help(self, command=None):
        """显示帮助信息"""
        if command:
            logger.info(f"显示命令 {command} 的帮助信息")
            # 这里可以显示特定命令的帮助
            print(f"docker {command} 命令的帮助信息")
        else:
            logger.info("显示Docker帮助信息")
            print("Docker命令帮助:")
            print("  run        运行容器")
            print("  start      启动容器")
            print("  stop       停止容器")
            print("  restart    重启容器")
            print("  ps         列出容器")
            print("  logs       查看容器日志")
            print("  attach     附加到容器")
            print("  exec       在容器中执行命令")
            print("  rm         删除容器")
            print("  pull       拉取镜像")
            print("  images     列出镜像")
            print("  rmi        删除镜像")
            print("  login      登录到Registry")
            print("  build      构建镜像")
            print("  save       保存镜像")
            print("  load       加载镜像")
            print("  tag        为镜像添加标签")
            print("  inspect    检查容器或镜像")
            print("  top        显示容器进程")
            print("  stats      显示容器统计")
            print("  cp         复制文件")
            print("  diff       显示文件系统变更")
            print("  commit     从容器创建镜像")
            print("  export     导出容器")
            print("  import     导入镜像")
            print("  history    显示镜像历史")
            print("  info       显示系统信息")
            print("  version    显示版本信息")
            print("  help       显示此帮助信息")
            print("  network    网络管理")
            print("  volume     卷管理")
            print("  system     系统管理")
        return True

    def _get_dir_size(self, path):
        """获取目录大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size

    def network_create(self, name, driver="bridge"):
        """创建网络"""
        logger.info(f"创建网络: {name} (驱动: {driver})")
        try:
            networks_file = os.path.join(self.cache_dir, 'networks.json')
            networks = {}
            if os.path.exists(networks_file):
                with open(networks_file, 'r') as f:
                    networks = json.load(f)
            
            if name in networks:
                logger.error(f"网络 {name} 已存在")
                return False
            
            network_id = self._generate_container_id()
            networks[name] = {
                'id': network_id,
                'name': name,
                'driver': driver,
                'created': datetime.now().isoformat(),
                'containers': []
            }
            
            with open(networks_file, 'w') as f:
                json.dump(networks, f, indent=2)
            
            logger.info(f"网络 {name} 创建成功")
            return True
        except Exception as e:
            logger.error(f"创建网络失败: {e}")
            return False

    def network_ls(self):
        """列出网络"""
        logger.info("列出网络")
        try:
            networks_file = os.path.join(self.cache_dir, 'networks.json')
            if not os.path.exists(networks_file):
                print("没有找到网络")
                return True
            
            with open(networks_file, 'r') as f:
                networks = json.load(f)
            
            print(f"{'网络ID':<12} {'名称':<20} {'驱动':<10} {'作用域':<10}")
            print("-" * 60)
            
            for name, network in networks.items():
                print(f"{network['id']:<12} {name:<20} {network['driver']:<10} {'local':<10}")
            
            return True
        except Exception as e:
            logger.error(f"列出网络失败: {e}")
            return False

    def network_rm(self, name):
        """删除网络"""
        logger.info(f"删除网络: {name}")
        try:
            networks_file = os.path.join(self.cache_dir, 'networks.json')
            if not os.path.exists(networks_file):
                logger.error(f"网络 {name} 不存在")
                return False
            
            with open(networks_file, 'r') as f:
                networks = json.load(f)
            
            if name not in networks:
                logger.error(f"网络 {name} 不存在")
                return False
            
            # 检查网络是否被容器使用
            if networks[name]['containers']:
                logger.error(f"网络 {name} 正在被容器使用，无法删除")
                return False
            
            del networks[name]
            
            with open(networks_file, 'w') as f:
                json.dump(networks, f, indent=2)
            
            logger.info(f"网络 {name} 删除成功")
            return True
        except Exception as e:
            logger.error(f"删除网络失败: {e}")
            return False

    def volume_create(self, name):
        """创建卷"""
        logger.info(f"创建卷: {name}")
        try:
            volumes_file = os.path.join(self.cache_dir, 'volumes.json')
            volumes = {}
            if os.path.exists(volumes_file):
                with open(volumes_file, 'r') as f:
                    volumes = json.load(f)
            
            if name in volumes:
                logger.error(f"卷 {name} 已存在")
                return False
            
            volume_id = self._generate_container_id()
            volume_path = os.path.join(self.cache_dir, 'volumes', name)
            os.makedirs(volume_path, exist_ok=True)
            
            volumes[name] = {
                'id': volume_id,
                'name': name,
                'path': volume_path,
                'created': datetime.now().isoformat(),
                'containers': []
            }
            
            with open(volumes_file, 'w') as f:
                json.dump(volumes, f, indent=2)
            
            logger.info(f"卷 {name} 创建成功")
            return True
        except Exception as e:
            logger.error(f"创建卷失败: {e}")
            return False

    def volume_ls(self):
        """列出卷"""
        logger.info("列出卷")
        try:
            volumes_file = os.path.join(self.cache_dir, 'volumes.json')
            if not os.path.exists(volumes_file):
                print("没有找到卷")
                return True
            
            with open(volumes_file, 'r') as f:
                volumes = json.load(f)
            
            print(f"{'卷名':<20} {'驱动':<10} {'挂载点':<50}")
            print("-" * 80)
            
            for name, volume in volumes.items():
                print(f"{name:<20} {'local':<10} {volume['path']:<50}")
            
            return True
        except Exception as e:
            logger.error(f"列出卷失败: {e}")
            return False

    def volume_rm(self, name):
        """删除卷"""
        logger.info(f"删除卷: {name}")
        try:
            volumes_file = os.path.join(self.cache_dir, 'volumes.json')
            if not os.path.exists(volumes_file):
                logger.error(f"卷 {name} 不存在")
                return False
            
            with open(volumes_file, 'r') as f:
                volumes = json.load(f)
            
            if name not in volumes:
                logger.error(f"卷 {name} 不存在")
                return False
            
            # 检查卷是否被容器使用
            if volumes[name]['containers']:
                logger.error(f"卷 {name} 正在被容器使用，无法删除")
                return False
            
            # 删除卷目录
            volume_path = volumes[name]['path']
            if os.path.exists(volume_path):
                import shutil
                shutil.rmtree(volume_path)
            
            del volumes[name]
            
            with open(volumes_file, 'w') as f:
                json.dump(volumes, f, indent=2)
            
            logger.info(f"卷 {name} 删除成功")
            return True
        except Exception as e:
            logger.error(f"删除卷失败: {e}")
            return False

    def system_prune(self, all_resources=False):
        """清理未使用的资源"""
        logger.info("清理未使用的资源")
        try:
            cleaned = 0
            
            # 清理停止的容器
            containers = self._load_containers()
            for container_id, container in list(containers.items()):
                if not self._is_process_running(container.get('pid', 0)):
                    logger.info(f"清理停止的容器: {container_id}")
                    del containers[container_id]
                    cleaned += 1
            
            self._save_containers(containers)
            
            # 清理未使用的镜像（可选）
            if all_resources:
                logger.info("清理未使用的镜像")
                # 这里可以添加镜像清理逻辑
            
            logger.info(f"清理完成，共清理 {cleaned} 个资源")
            return True
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
            return False

    def push(self, image_url, tag="latest"):
        """推送镜像到Docker Registry
        
        注意：在proot环境下，此功能受到限制，主要用于概念性演示
        """
        logger.info(f"推送镜像: {image_url}:{tag}")
        
        try:
            # 检查镜像是否存在（使用runner的缓存检查方法）
            if not self.runner._is_image_cached(image_url):
                logger.error(f"镜像 {image_url} 不存在，请先使用 docker pull 下载")
                return False
            
            # 获取镜像的缓存路径
            cache_path = self.runner._get_image_cache_path(image_url)
            logger.info(f"找到镜像文件: {cache_path}")
            
            # 检查认证信息
            config = self._load_config()
            auths = config.get('auths', {})
            
            # 确定registry服务器
            if '/' in image_url.split(':')[0]:
                registry = image_url.split('/')[0]
            else:
                registry = "index.docker.io"
            
            # 查找对应的认证信息
            username = None
            password = None
            for server, creds in auths.items():
                server_name = urlparse(server).hostname or server
                if server_name == registry or (server_name == "index.docker.io" and registry == "index.docker.io"):
                    username = creds.get('username')
                    password = creds.get('password')
                    break
            
            if not username or not password:
                logger.error(f"未找到 {registry} 的认证信息，请先使用 docker login 登录")
                return False
            
            logger.info(f"使用认证信息推送到 {registry}")
            
            # 在proot环境下，实际的推送功能受到限制
            # 这里主要提供概念性演示和错误检查
            logger.warning("注意：在proot环境下，实际的镜像推送功能受到限制")
            logger.info("此命令主要用于验证镜像存在性和认证信息")
            
            # 模拟推送过程
            logger.info(f"镜像 {image_url}:{tag} 已准备好推送")
            logger.info("在标准Docker环境中，镜像将被推送到远程仓库")
            
            return True
            
        except Exception as e:
            logger.error(f"推送镜像失败: {e}")
            return False

def create_parser():
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog='docker',
        description='Docker风格的proot容器管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 拉取镜像
  %(prog)s pull alpine:latest
  %(prog)s pull nginx:alpine

  # 运行容器
  %(prog)s run alpine:latest
  %(prog)s run -d nginx:alpine
  %(prog)s run -it alpine:latest /bin/sh
  %(prog)s run -e "API_KEY=123" -v /host:/container alpine:latest /bin/sh

  # 查看容器
  %(prog)s ps
  %(prog)s ps -a

  # 查看镜像
  %(prog)s images

  # 停止和删除容器
  %(prog)s stop <container_id>
  %(prog)s rm <container_id>

  # 附加到运行中的容器
  %(prog)s attach <container_id>

  # 在运行中的容器中执行命令
  %(prog)s exec <container_id> ls -l
  %(prog)s exec -it <container_id> /bin/sh

  # 删除镜像
  %(prog)s rmi alpine:latest
        """
    )

    parser.add_argument(
        '--cache-dir',
        help='指定缓存目录路径'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )

    subparsers = parser.add_subparsers(dest='subcommand', help='可用命令', required=True)

    # login 命令
    login_parser = subparsers.add_parser('login', help='登录到Docker Registry')
    login_parser.add_argument('server', nargs='?', default=None, help='Registry服务器地址 (默认为Docker Hub)')
    login_parser.add_argument('-u', '--username', help='用户名')
    login_parser.add_argument('-p', '--password', help='密码')

    # pull 命令
    pull_parser = subparsers.add_parser('pull', help='拉取镜像')
    pull_parser.add_argument('image', help='镜像URL')
    pull_parser.add_argument('--force', action='store_true', help='强制重新下载')
    pull_parser.add_argument('-q', '--quiet', action='store_true', help='静默模式，仅显示镜像ID')

    # push 命令
    push_parser = subparsers.add_parser('push', help='推送镜像到Docker Registry')
    push_parser.add_argument('image', help='镜像名称')
    push_parser.add_argument('-t', '--tag', default='latest', help='镜像标签 (默认: latest)')

    # run 命令
    run_parser = subparsers.add_parser('run', help='运行容器')
    run_parser.add_argument('image', help='镜像URL')
    run_parser.add_argument('--name', help='为容器指定一个名称')
    run_parser.add_argument('command', nargs='*', help='要执行的命令')
    run_parser.add_argument('-d', '--detach', action='store_true', help='后台运行')
    run_parser.add_argument('-it', '--interactive-tty', action='store_true', help='交互式运行容器 (分配伪TTY并保持stdin打开)')
    run_parser.add_argument('-e', '--env', action='append', default=[], help='环境变量 (KEY=VALUE)')
    run_parser.add_argument('-v', '--volume', dest='bind', action='append', default=[], help='挂载卷 (HOST:CONTAINER)')
    run_parser.add_argument('-w', '--workdir', help='工作目录')
    run_parser.add_argument('--force-download', action='store_true', help='强制重新下载镜像')

    # start 命令
    start_parser = subparsers.add_parser('start', help='启动一个已停止的容器')
    start_parser.add_argument('container', help='容器ID')

    # restart 命令
    restart_parser = subparsers.add_parser('restart', help='重启一个容器')
    restart_parser.add_argument('container', help='容器ID')

    # ps 命令
    ps_parser = subparsers.add_parser('ps', help='列出容器')
    ps_parser.add_argument('-a', '--all', action='store_true', help='显示所有容器（包括已停止的）')

    # logs 命令
    logs_parser = subparsers.add_parser('logs', help='查看容器日志')
    logs_parser.add_argument('container', help='容器ID')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='持续输出日志')

    # images 命令
    subparsers.add_parser('images', help='列出镜像')

    # rmi 命令
    rmi_parser = subparsers.add_parser('rmi', help='删除镜像')
    rmi_parser.add_argument('image', help='镜像URL')

    # stop 命令
    stop_parser = subparsers.add_parser('stop', help='停止容器')
    stop_parser.add_argument('container', help='容器ID')

    # rm 命令
    rm_parser = subparsers.add_parser('rm', help='删除容器')
    rm_parser.add_argument('container', help='容器ID')
    rm_parser.add_argument('-f', '--force', action='store_true', help='强制删除运行中的容器')
    
    # attach 命令
    attach_parser = subparsers.add_parser('attach', help='附加到运行中的容器并查看输出')
    attach_parser.add_argument('container', help='容器ID')
    
    # exec 命令
    exec_parser = subparsers.add_parser('exec', help='在运行中的容器中执行命令')
    exec_parser.add_argument('container', help='容器ID')
    exec_parser.add_argument('command', nargs='*', help='要执行的命令')
    exec_parser.add_argument('-it', '--interactive-tty', action='store_true', help='交互式运行容器 (分配伪TTY并保持stdin打开)')

    # build 命令
    build_parser = subparsers.add_parser('build', help='构建Docker镜像')
    build_parser.add_argument('context', help='构建上下文路径')
    build_parser.add_argument('-t', '--tag', help='镜像标签')
    build_parser.add_argument('-f', '--file', help='Dockerfile路径')

    # save 命令
    save_parser = subparsers.add_parser('save', help='保存镜像到tar文件')
    save_parser.add_argument('image', help='镜像名称')
    save_parser.add_argument('-o', '--output', required=True, help='输出文件路径')

    # load 命令
    load_parser = subparsers.add_parser('load', help='从tar文件加载镜像')
    load_parser.add_argument('-i', '--input', required=True, help='输入文件路径')

    # tag 命令
    tag_parser = subparsers.add_parser('tag', help='为镜像添加标签')
    tag_parser.add_argument('source_image', help='源镜像')
    tag_parser.add_argument('target_image', help='目标镜像')

    # inspect 命令
    inspect_parser = subparsers.add_parser('inspect', help='检查容器或镜像的详细信息')
    inspect_parser.add_argument('target', help='容器ID或镜像名称')

    # top 命令
    top_parser = subparsers.add_parser('top', help='显示容器中运行的进程')
    top_parser.add_argument('container', help='容器ID')

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示容器的资源使用统计')
    stats_parser.add_argument('container', nargs='?', help='容器ID (可选，不指定则显示所有容器)')

    # cp 命令
    cp_parser = subparsers.add_parser('cp', help='在容器和主机之间复制文件')
    cp_parser.add_argument('source', help='源路径')
    cp_parser.add_argument('dest', help='目标路径')

    # diff 命令
    diff_parser = subparsers.add_parser('diff', help='显示容器文件系统的变更')
    diff_parser.add_argument('container', help='容器ID')

    # commit 命令
    commit_parser = subparsers.add_parser('commit', help='从容器创建新镜像')
    commit_parser.add_argument('container', help='容器ID')
    commit_parser.add_argument('repository', help='镜像仓库名称')
    commit_parser.add_argument('tag', nargs='?', default='latest', help='镜像标签 (默认: latest)')

    # export 命令
    export_parser = subparsers.add_parser('export', help='导出容器文件系统到tar文件')
    export_parser.add_argument('container', help='容器ID')
    export_parser.add_argument('-o', '--output', required=True, help='输出文件路径')

    # import 命令
    import_parser = subparsers.add_parser('import', help='从tar文件导入镜像')
    import_parser.add_argument('file', help='tar文件路径')
    import_parser.add_argument('repository', help='镜像仓库名称')
    import_parser.add_argument('tag', nargs='?', default='latest', help='镜像标签 (默认: latest)')

    # history 命令
    history_parser = subparsers.add_parser('history', help='显示镜像的历史记录')
    history_parser.add_argument('image', help='镜像名称')

    # info 命令
    subparsers.add_parser('info', help='显示系统信息')

    # version 命令
    subparsers.add_parser('version', help='显示版本信息')

    # help 命令
    help_parser = subparsers.add_parser('help', help='显示帮助信息')
    help_parser.add_argument('command', nargs='?', help='要显示帮助的命令')

    # network 命令组
    network_parser = subparsers.add_parser('network', help='网络管理')
    network_subparsers = network_parser.add_subparsers(dest='network_command', required=True)
    
    network_create_parser = network_subparsers.add_parser('create', help='创建网络')
    network_create_parser.add_argument('name', help='网络名称')
    network_create_parser.add_argument('--driver', default='bridge', help='网络驱动 (默认: bridge)')
    
    network_subparsers.add_parser('ls', help='列出网络')
    
    network_rm_parser = network_subparsers.add_parser('rm', help='删除网络')
    network_rm_parser.add_argument('name', help='网络名称')

    # volume 命令组
    volume_parser = subparsers.add_parser('volume', help='卷管理')
    volume_subparsers = volume_parser.add_subparsers(dest='volume_command', required=True)
    
    volume_create_parser = volume_subparsers.add_parser('create', help='创建卷')
    volume_create_parser.add_argument('name', help='卷名称')
    
    volume_subparsers.add_parser('ls', help='列出卷')
    
    volume_rm_parser = volume_subparsers.add_parser('rm', help='删除卷')
    volume_rm_parser.add_argument('name', help='卷名称')

    # system 命令组
    system_parser = subparsers.add_parser('system', help='系统管理')
    system_subparsers = system_parser.add_subparsers(dest='system_command', required=True)
    
    system_prune_parser = system_subparsers.add_parser('prune', help='清理未使用的资源')
    system_prune_parser.add_argument('-a', '--all', action='store_true', help='清理所有未使用的资源')

    return parser

def main():
    """主函数"""
    parser = create_parser()
    args, unknown = parser.parse_known_args()

    # Handle the command part for 'run' and 'exec'
    if args.subcommand in ['run', 'exec']:
        # Combine the command parts that argparse might have split.
        # `args.command` will have any command parts found before an unknown option.
        # `unknown` will have any arguments that were not recognized.
        # For `run` and `exec`, these are part of the command to be executed.
        args.command.extend(unknown)
    elif unknown:
        # For other subcommands, unknown arguments are an error.
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 如果没有指定命令，显示帮助
    if not args.subcommand:
        parser.print_help()
        return

    # 创建CLI实例
    cli = DockerCLI(cache_dir=args.cache_dir)

    try:
        if args.subcommand == 'login':
            success = cli.login(args.server, args.username, args.password)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'pull':
            success = cli.pull(args.image, force=args.force, quiet=args.quiet)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'push':
            success = cli.push(args.image, args.tag)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'run':
            # 在调用run之前加载凭证并附加到kwargs
            config = cli._load_config()
            auths = config.get('auths', {})
            username, password = None, None
            for server, creds in auths.items():
                server_name = urlparse(server).hostname or server
                if server_name in args.image or (server_name == "index.docker.io" and '/' not in args.image.split(':')[0]):
                    username = creds.get('username')
                    password = creds.get('password')
                    break
            
            container_id = cli.run(
                args.image,
                command=args.command,
                name=args.name,
                env=args.env,
                bind=args.bind,
                workdir=args.workdir,
                detach=args.detach,
                interactive=args.interactive_tty,
                force_download=args.force_download,
                username=username,
                password=password
            )
            sys.exit(0 if container_id else 1)

        elif args.subcommand == 'start':
            success = cli.start(args.container)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'restart':
            success = cli.restart(args.container)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'ps':
            cli.ps(all_containers=args.all)

        elif args.subcommand == 'logs':
            success = cli.logs(args.container, follow=args.follow)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'images':
            cli.images()

        elif args.subcommand == 'rmi':
            success = cli.rmi(args.image)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'stop':
            success = cli.stop(args.container)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'rm':
            success = cli.rm(args.container, force=args.force)
            sys.exit(0 if success else 1)
            
        elif args.subcommand == 'attach':
            success = cli.attach(args.container)
            sys.exit(0 if success else 1)
            
        elif args.subcommand == 'exec':
            success = cli.exec(args.container, args.command, interactive=args.interactive_tty)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'build':
            success = cli.build(args.context, args.tag, args.file)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'save':
            success = cli.save(args.image, args.output)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'load':
            success = cli.load(args.input)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'tag':
            success = cli.tag(args.source_image, args.target_image)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'inspect':
            success = cli.inspect(args.target)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'top':
            success = cli.top(args.container)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'stats':
            success = cli.stats(args.container)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'cp':
            success = cli.cp(args.source, args.dest)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'diff':
            success = cli.diff(args.container)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'commit':
            success = cli.commit(args.container, args.repository, args.tag)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'export':
            success = cli.export(args.container, args.output)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'import':
            success = cli.import_(args.file, args.repository, args.tag)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'history':
            success = cli.history(args.image)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'info':
            success = cli.info()
            sys.exit(0 if success else 1)

        elif args.subcommand == 'version':
            success = cli.version()
            sys.exit(0 if success else 1)

        elif args.subcommand == 'help':
            success = cli.help(args.command)
            sys.exit(0 if success else 1)

        elif args.subcommand == 'network':
            if args.network_command == 'create':
                success = cli.network_create(args.name, args.driver)
            elif args.network_command == 'ls':
                success = cli.network_ls()
            elif args.network_command == 'rm':
                success = cli.network_rm(args.name)
            else:
                logger.error(f"未知的网络命令: {args.network_command}")
                success = False
            sys.exit(0 if success else 1)

        elif args.subcommand == 'volume':
            if args.volume_command == 'create':
                success = cli.volume_create(args.name)
            elif args.volume_command == 'ls':
                success = cli.volume_ls()
            elif args.volume_command == 'rm':
                success = cli.volume_rm(args.name)
            else:
                logger.error(f"未知的卷命令: {args.volume_command}")
                success = False
            sys.exit(0 if success else 1)

        elif args.subcommand == 'system':
            if args.system_command == 'prune':
                success = cli.system_prune(args.all)
            else:
                logger.error(f"未知的系统命令: {args.system_command}")
                success = False
            sys.exit(0 if success else 1)

        else:
            logger.error(f"未知命令: {args.subcommand}")
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
