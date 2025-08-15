#!/bin/bash
#
# 运行项目的所有自动化测试。
#

# 获取脚本所在的目录
SCRIPT_DIR=$(dirname "$0")
# 切换到项目根目录
cd "$SCRIPT_DIR/.."

echo "======================================="
echo "Running all tests..."
echo "======================================="

# 将项目根目录添加到 PYTHONPATH，并使用 unittest discover 运行测试
export PYTHONPATH=$(pwd)
python3 -m unittest discover tests

if [ $? -ne 0 ]; then
    echo "Tests failed!"
    exit 1
fi

echo ""
echo "All tests passed successfully!"
exit 0