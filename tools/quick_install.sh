#!/bin/bash
#
# WorkflowProgram Plugin 实验性快速安装
# 一键执行构建 + 用户目录覆盖复制
#

set -e

cd "$(dirname "$0")/.."

echo "步骤 1/2: 构建 Plugin..."
python3 tools/build_plugin.py

echo ""
echo "步骤 2/2: 安装到用户目录..."
bash tools/install_dev.sh
