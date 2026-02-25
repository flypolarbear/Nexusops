#!/bin/bash
# Architect Agent - 使用 Claude Opus 进行架构设计和代码审查
# 用法: ./scripts/architect.sh

export ANTHROPIC_BASE_URL="https://api.aigocode.com"
export ANTHROPIC_AUTH_TOKEN="sk-aa0900390638b428fa81b2b963230dcd83b82155c6e737e5fdcb36eb27ac5c7f"

# 启动 Claude Code，使用 opus 模型
cd "$(dirname "$0")/.."
command claude --model opus "$@"
