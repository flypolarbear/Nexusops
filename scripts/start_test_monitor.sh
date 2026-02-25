#!/bin/bash
# Start the Test Monitor Agent
#
# Usage:
#   ./scripts/start_test_monitor.sh [--interval SECONDS] [--port PORT]
#
# Default: interval=60s, port=8765
#
# Web Dashboard: http://localhost:8765/dashboard
# JSON Status: http://localhost:8765/status
# Test History: http://localhost:8765/history

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "  NexusOps Test Monitor Agent"
echo "=========================================="
echo ""
echo "This agent will:"
echo "  1. Monitor task_list.json for changes"
echo "  2. Run tests when tasks complete"
echo "  3. Provide web dashboard at http://localhost:8765/dashboard"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the Python agent
python3 scripts/test_monitor_agent.py "$@"
