#!/bin/bash
#
# WorkflowProgram Plugin 开发安装脚本
#
# 用途：将 dist/plugin/ 临时覆盖复制到用户 Claude Code 配置目录
# 注意：这是实验性开发辅助路径，不属于 WorkflowProgram 的正式安装契约
# 正式、受支持的验证方式是：claude --plugin-dir <dist/plugin>
#

set -e

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$PLUGIN_ROOT/dist/plugin"
CLAUDE_HOME="${HOME}/.claude"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "WorkflowProgram Plugin 实验性开发安装"
echo "=========================================="
echo ""

# 检查构建产物是否存在
if [ ! -d "$DIST_DIR" ]; then
    echo -e "${RED}错误：找不到构建产物 $DIST_DIR${NC}"
    echo "请先运行构建："
    echo "  python3 tools/build_plugin.py"
    exit 1
fi

# 检查目标目录
if [ ! -d "$CLAUDE_HOME" ]; then
    echo -e "${YELLOW}警告：Claude Code 配置目录不存在 $CLAUDE_HOME${NC}"
    echo "创建目录..."
    mkdir -p "$CLAUDE_HOME"
fi

echo "安装源：$DIST_DIR"
echo "安装目标：$CLAUDE_HOME"
echo ""

# 安装函数
install_component() {
    local src="$1"
    local dst="$2"
    local name="$3"

    if [ -d "$src" ]; then
        echo "安装 $name..."

        # 如果目标已存在，备份
        if [ -d "$dst" ]; then
            backup_name="${dst}.backup.$(date +%Y%m%d%H%M%S)"
            echo "  备份现有 $name 到 ${dst##*/}.backup.*"
            mv "$dst" "$backup_name"
        fi

        # 复制新内容
        cp -r "$src" "$dst"
        local count=$(find "$src" -type f | wc -l)
        echo -e "  ${GREEN}✓${NC} 已复制 $count 个文件"
    else
        echo -e "  ${YELLOW}⚠${NC} 跳过 $name（源不存在）"
    fi
}

# 安装各组件
echo "开始安装组件..."
echo "------------------------------------------"

# 1. 安装 Agents（Project 级 Agent）
install_component \
    "$DIST_DIR/agents" \
    "$CLAUDE_HOME/agents" \
    "Agents"

# 2. 安装 Commands（全局命令）
install_component \
    "$DIST_DIR/commands" \
    "$CLAUDE_HOME/commands" \
    "Commands"

# 3. 安装 Skills（全局技能）
install_component \
    "$DIST_DIR/skills" \
    "$CLAUDE_HOME/skills" \
    "Skills"

# 4. 安装 Rules（可选，通常不需要全局安装）
read -p "是否安装 Rules 到用户目录？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    install_component \
        "$DIST_DIR/rules" \
        "$CLAUDE_HOME/rules" \
        "Rules"
fi

# 5. 安装 Scripts（可选）
read -p "是否安装 Scripts 到用户目录？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    install_component \
        "$DIST_DIR/scripts" \
        "$CLAUDE_HOME/scripts" \
        "Scripts"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}安装完成！${NC}"
echo "=========================================="
echo ""
echo "请重启 Claude Code 或使用 /reload 使更改生效"
echo ""
echo "安装后可用命令："
echo "  /workflowprogram-orchestrate   - 总控路由"
echo "  /workflowprogram-develop       - 开发工作流"
echo "  /workflowprogram-audit         - 审计工作流"
echo "  /workflowprogram-iterate       - 迭代工作流"
echo "  /workflowprogram-validate      - 验证工作流"
echo ""
echo "或激活 skill："
echo "  /skill workflowprogram-orchestrate"
echo ""
echo "注意：这是实验性开发安装。"
echo "      它会覆盖用户 ~/.claude 下的对应目录，不属于受支持的正式契约。"
echo "      当前推荐的验证方式是：claude --plugin-dir $DIST_DIR"
echo ""
