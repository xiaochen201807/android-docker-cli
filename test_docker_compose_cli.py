import unittest
import os
import sys
import subprocess
import shutil
import yaml

class TestDockerComposeCLI(unittest.TestCase):
    """
    对 docker_compose_cli.py 进行集成测试。
    """
    TEST_IMAGE = "swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/alpine:latest"
    TEST_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".docker_proot_cache_test_compose")
    DOCKER_CLI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docker_cli.py')
    COMPOSE_CLI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docker_compose_cli.py')
    COMPOSE_FILE_PATH = "docker-compose.test.yml"

    @classmethod
    def setUpClass(cls):
        """在所有测试开始前，准备环境。"""
        # 清理并创建测试缓存目录
        if os.path.exists(cls.TEST_CACHE_DIR):
            shutil.rmtree(cls.TEST_CACHE_DIR)
        os.makedirs(cls.TEST_CACHE_DIR)

        # 创建一个临时的 docker-compose 文件
        compose_config = {
            'version': '1.0',
            'services': {
                'app': {
                    'image': cls.TEST_IMAGE,
                    'container_name': 'compose-test-app',
                    'command': "sh -c 'echo App started && sleep 300'"
                },
                'db': {
                    'image': cls.TEST_IMAGE,
                    'container_name': 'compose-test-db',
                    'command': "sh -c 'echo DB started && sleep 300'"
                }
            }
        }
        with open(cls.COMPOSE_FILE_PATH, 'w') as f:
            yaml.dump(compose_config, f)

        # 先拉取镜像，避免重复下载影响测试速度
        cmd = [sys.executable, cls.DOCKER_CLI_PATH, "--cache-dir", cls.TEST_CACHE_DIR, "pull", cls.TEST_IMAGE]
        subprocess.run(cmd, capture_output=True)


    @classmethod
    def tearDownClass(cls):
        """在所有测试结束后，清理环境。"""
        if os.path.exists(cls.TEST_CACHE_DIR):
            shutil.rmtree(cls.TEST_CACHE_DIR)
        if os.path.exists(cls.COMPOSE_FILE_PATH):
            os.remove(cls.COMPOSE_FILE_PATH)

    def _run_compose_command(self, command):
        """执行 docker_compose_cli.py 命令。"""
        cmd = [sys.executable, self.COMPOSE_CLI_PATH, "-f", self.COMPOSE_FILE_PATH] + command
        # 在 compose 命令中注入测试缓存目录，需要修改 compose 脚本或通过环境变量
        # 简单起见，我们依赖 docker_cli.py 能找到正确的 compose 文件
        # 为了让 docker_cli.py 使用正确的缓存，我们需要修改 docker_compose_cli.py
        # 这里我们暂时用一个 hacky 的方法，通过修改 docker_cli.py 的路径来传递参数
        
        # 正确的方法是修改 docker_compose_cli.py 以接受 --cache-dir
        # 但为了不修改原代码，我们在这里用一个包装脚本
        docker_cli_wrapper_content = f"""#!/usr/bin/env python3
import sys
import subprocess
DOCKER_CLI_PATH = '{self.DOCKER_CLI_PATH}'
cmd = [sys.executable, DOCKER_CLI_PATH, '--cache-dir', '{self.TEST_CACHE_DIR}'] + sys.argv[1:]
sys.exit(subprocess.run(cmd).returncode)
"""
        wrapper_path = "docker_cli_wrapper.py"
        with open(wrapper_path, "w") as f:
            f.write(docker_cli_wrapper_content)
        os.chmod(wrapper_path, 0o755)

        original_docker_cli_path = self.COMPOSE_CLI_PATH.replace('docker_compose_cli.py', 'docker_cli.py')
        
        # Monkey patch the DOCKER_CLI_PATH in the compose script for the test
        with open(self.COMPOSE_CLI_PATH, 'r') as f:
            original_compose_script = f.read()
        
        modified_compose_script = original_compose_script.replace(
            "DOCKER_CLI_PATH = os.path.join(SCRIPT_DIR, 'docker_cli.py')",
            f"DOCKER_CLI_PATH = os.path.join(SCRIPT_DIR, '{wrapper_path}')"
        )
        
        with open(self.COMPOSE_CLI_PATH, 'w') as f:
            f.write(modified_compose_script)

        print(f"\nExecuting: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Restore original compose script
        with open(self.COMPOSE_CLI_PATH, 'w') as f:
            f.write(original_compose_script)
        os.remove(wrapper_path)

        self.assertEqual(result.returncode, 0, f"Compose 命令执行失败: {result.stdout}")
        return result

    def test_compose_up_and_down(self):
        """测试 docker-compose up 和 docker-compose down"""
        # Up
        result_up = self._run_compose_command(["up", "-d"])
        self.assertIn("Starting service: app", result_up.stdout)
        self.assertIn("Starting service: db", result_up.stdout)

        # Check with ps
        ps_cmd = [sys.executable, self.DOCKER_CLI_PATH, "--cache-dir", self.TEST_CACHE_DIR, "ps"]
        result_ps = subprocess.run(ps_cmd, capture_output=True, text=True)
        self.assertIn("compose-test-app", result_ps.stdout)
        self.assertIn("compose-test-db", result_ps.stdout)
        self.assertIn("running", result_ps.stdout)

        # Down
        result_down = self._run_compose_command(["down"])
        self.assertIn("Stopping service: app", result_down.stdout)
        self.assertIn("Removing service: app", result_down.stdout)
        self.assertIn("Stopping service: db", result_down.stdout)
        self.assertIn("Removing service: db", result_down.stdout)

        # Check with ps -a
        psa_cmd = [sys.executable, self.DOCKER_CLI_PATH, "--cache-dir", self.TEST_CACHE_DIR, "ps", "-a"]
        result_psa = subprocess.run(psa_cmd, capture_output=True, text=True)
        self.assertNotIn("compose-test-app", result_psa.stdout)
        self.assertNotIn("compose-test-db", result_psa.stdout)


if __name__ == '__main__':
    unittest.main()