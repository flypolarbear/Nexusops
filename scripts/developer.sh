#!/bin/bash
# Developer Agent - 使用 GLM-5 进行主要开发工作
# 用法: ./scripts/developer.sh

export ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
export ANTHROPIC_AUTH_TOKEN="18e011007bcc4e739772ba09304ac7a4.eQUiHtkmJsoIcBKW"
export ANTHROPIC_MODEL="GLM-5"
export ANTHROPIC_SMALL_FAST_MODEL="GLM-4.7-Air"

# 启动 Claude Code
cd "$(dirname "$0")/.."
command claude "$@"
