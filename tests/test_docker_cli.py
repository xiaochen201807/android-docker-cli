import unittest
import os
import sys
import subprocess
import shutil
import time
import json

class TestDockerCLI(unittest.TestCase):
    """
    对 docker_cli.py 和相关脚本进行集成测试。
    """
    TEST_IMAGE = "swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/alpine:latest"
    TEST_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".docker_proot_cache_test")
    # We will now run the CLI as a module, so this path is no longer needed.

    @classmethod
    def setUpClass(cls):
        """在所有测试开始前，清理并创建测试缓存目录。"""
        if os.path.exists(cls.TEST_CACHE_DIR):
            shutil.rmtree(cls.TEST_CACHE_DIR)
        os.makedirs(cls.TEST_CACHE_DIR)

    @classmethod
    def tearDownClass(cls):
        """在所有测试结束后，清理测试缓存目录。"""
        if os.path.exists(cls.TEST_CACHE_DIR):
            shutil.rmtree(cls.TEST_CACHE_DIR)

    def _run_command(self, command, expect_success=True):
        """执行 docker_cli.py 命令并返回结果。"""
        # Run as a module to ensure correct package imports
        cmd = [sys.executable, "-m", "android_docker.docker_cli", "--cache-dir", self.TEST_CACHE_DIR] + command
        print(f"\nExecuting: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        if expect_success:
            self.assertEqual(result.returncode, 0, f"命令执行失败: {result.stdout}")
        else:
            self.assertNotEqual(result.returncode, 0, "命令预期失败但成功了。")
            
        return result

    def test_01_pull_image(self):
        """测试 docker pull"""
        result = self._run_command(["pull", self.TEST_IMAGE])
        self.assertIn("镜像拉取成功", result.stdout)

    def test_02_images_list(self):
        """测试 docker images"""
        result = self._run_command(["images"])
        self.assertIn(self.TEST_IMAGE, result.stdout)

    def test_03_run_foreground(self):
        """测试 docker run (前台)"""
        test_string = "Hello from test"
        result = self._run_command(["run", self.TEST_IMAGE, "echo", test_string])
        self.assertIn(test_string, result.stdout)

    def test_04_run_detached_and_ps(self):
        """测试 docker run -d 和 docker ps"""
        container_name = "test-detached"
        self._run_command(["run", "-d", "--name", container_name, self.TEST_IMAGE, "sleep", "10"])
        
        result = self._run_command(["ps"])
        self.assertIn(container_name, result.stdout)
        self.assertIn("running", result.stdout)

        # 清理
        self._run_command(["stop", container_name])
        self._run_command(["rm", container_name])

    def test_05_lifecycle_stop_start_rm(self):
        """测试 docker stop, start, rm"""
        container_name = "test-lifecycle"
        self._run_command(["run", "-d", "--name", container_name, self.TEST_IMAGE, "sleep", "10"])

        # Stop
        self._run_command(["stop", container_name])
        result = self._run_command(["ps", "-a"])
        self.assertIn(container_name, result.stdout)
        self.assertIn("exited", result.stdout)

        # Start
        self._run_command(["start", container_name])
        result = self._run_command(["ps"])
        self.assertIn(container_name, result.stdout)
        self.assertIn("running", result.stdout)

        # RM
        self._run_command(["stop", container_name]) # Must be stopped to be removed without force
        self._run_command(["rm", container_name])
        result = self._run_command(["ps", "-a"])
        self.assertNotIn(container_name, result.stdout)

    def test_06_logs(self):
        """测试 docker logs"""
        container_name = "test-logs"
        log_line_1 = "log line 1"
        log_line_2 = "log line 2"
        self._run_command(["run", "-d", "--name", container_name, self.TEST_IMAGE, "sh", "-c", f"echo {log_line_1}; sleep 1; echo {log_line_2}"])
        
        time.sleep(2) # 等待容器产生日志

        result = self._run_command(["logs", container_name])
        self.assertIn(log_line_1, result.stdout)
        self.assertIn(log_line_2, result.stdout)

        # 清理
        self._run_command(["rm", "-f", container_name])

    def test_07_rmi(self):
        """测试 docker rmi"""
        # 确保没有容器正在使用该镜像
        result = self._run_command(["ps", "-a"])
        if self.TEST_IMAGE in result.stdout:
            print("警告: 在 rmi 测试前发现有残留容器，可能导致测试失败。")

        self._run_command(["rmi", self.TEST_IMAGE])
        result = self._run_command(["images"])
        self.assertNotIn(self.TEST_IMAGE, result.stdout)

    def test_08_run_with_env_vars_after_image(self):
        """测试在镜像名称后传递环境变量"""
        test_env_var = "MY_TEST_VAR"
        test_env_val = "hello_world"
        
        # The command to run inside the container
        # We use `env` to print all environment variables
        command_in_container = ["env"]
        
        # Construct the full command for docker_cli
        cli_command = [
            "run",
            self.TEST_IMAGE,
            "-e", f"{test_env_var}={test_env_val}",
        ]
        cli_command.extend(command_in_container)

        result = self._run_command(cli_command)
        
        # Check if the environment variable is present in the output
        expected_output = f"{test_env_var}={test_env_val}"
        self.assertIn(expected_output, result.stdout)

    def test_09_run_with_volume_mount(self):
        """测试 docker run -v (volume mount)"""
        container_name = "my-nginx"
        nginx_image = "swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/nginx:alpine"
        
        # 首先拉取 nginx 镜像
        self._run_command(["pull", nginx_image])

        # 创建一个本地的 nginx.conf 文件给测试使用
        local_conf_path = os.path.join(self.TEST_CACHE_DIR, "nginx.conf")
        with open(local_conf_path, "w") as f:
            # 使用一个高位端口避免权限问题和端口冲突
            f.write("events {} http { server { listen 8088; server_name localhost; location / { return 200 'volume test ok'; } } }")

        # 准备 run 命令
        # 注意: 我们不能在 python 中直接使用 $(pwd), 需要用 os.getcwd() 替代
        volume_map = f"{local_conf_path}:/etc/nginx/nginx.conf"
        
        run_command = [
            "run", "-d",
            "--name", container_name,
            "-v", volume_map,
            nginx_image
        ]
        
        self._run_command(run_command)

        # 检查容器是否在运行
        result = self._run_command(["ps"])
        self.assertIn(container_name, result.stdout)
        self.assertIn("running", result.stdout)

        # 等待 nginx 启动
        time.sleep(3)

        # 检查日志，确认 nginx 是否因为我们的配置而正常启动
        # Nginx 默认不会输出太多日志，但如果配置错误，这里会有错误信息
        log_result = self._run_command(["logs", container_name])
        self.assertNotIn("nginx: [emerg]", log_result.stdout, "Nginx 配置文件似乎导致了启动错误")

        # 清理
        self._run_command(["stop", container_name])
        self._run_command(["rm", container_name])
        self._run_command(["rmi", nginx_image])


if __name__ == '__main__':
    unittest.main()