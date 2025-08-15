#!/bin/bash
#
# 运行项目的所有自动化测试。
#

echo "======================================="
echo "Running tests for docker_cli.py"
echo "======================================="
python3 test_docker_cli.py
if [ $? -ne 0 ]; then
    echo "docker_cli.py tests failed!"
    exit 1
fi

echo ""
echo "======================================="
echo "Running tests for docker_compose_cli.py"
echo "======================================="
python3 test_docker_compose_cli.py
if [ $? -ne 0 ]; then
    echo "docker_compose_cli.py tests failed!"
    exit 1
fi

echo ""
echo "All tests passed successfully!"
exit 0