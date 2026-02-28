#!/bin/bash
# EXO Team tmux Split Panes Setup
#
# Layout:
# ┌────────────────────────────────────────────────────────────────────┐
# │                        GLM: Coordinator                            │
# ├─────────────────────┬─────────────────────┬────────────────────────┤
# │        Elon         │        Ryan         │       Cynthia          │
# │   PM/Architect      │   Full-Stack Dev    │   QA/Testing           │
# └─────────────────────┴─────────────────────┴────────────────────────┘

SESSION_NAME="claude-work"
PROJECT_ROOT="/Users/hendrix/AgentSpace/NexusOps"

# Kill existing session if exists
tmux kill-session -t $SESSION_NAME 2>/dev/null

# Create new session with GLM (main coordinator)
tmux new-session -d -s $SESSION_NAME -c $PROJECT_ROOT -x 200 -y 50

# Rename first window to GLM
tmux rename-window -t $SESSION_NAME:0 "GLM"
tmux send-keys -t $SESSION_NAME:0 "echo '🟢 GLM - Executive Lead (Coordinator)'" C-m
tmux send-keys -t $SESSION_NAME:0 "echo '任务: 总控协调、质量门禁、最终汇总'" C-m
tmux send-keys -t $SESSION_NAME:0 "echo ''" C-m
tmux send-keys -t $SESSION_NAME:0 "cd $PROJECT_ROOT && claude" C-m

# Split window horizontally (creates Ryan pane on right)
tmux split-window -h -t $SESSION_NAME:0 -c $PROJECT_ROOT

# Split right pane vertically (creates Cynthia below Ryan)
tmux split-window -v -t $SESSION_NAME:0 -c $PROJECT_ROOT

# Split left pane vertically (creates Elon below GLM)
tmux split-window -v -t $SESSION_NAME:0 -c $PROJECT_ROOT

# Now we have 4 panes: GLM (top-left), Elon (bottom-left), Ryan (top-right), Cynthia (bottom-right)
# Need to adjust layout

# Pane 0: GLM (top-left) - already has claude
# Pane 1: Ryan (top-right)
# Pane 2: Cynthia (bottom-right)
# Pane 3: Elon (bottom-left)

# Send commands to each pane
# Ryan pane
tmux send-keys -t $SESSION_NAME:0.1 "echo '🔵 Ryan - Full-Stack Developer'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo '任务: Gateway、Agent 开发、代码质量'" C-m
tmux send-keys -t $SESSION_NAME:0.1 "echo ''" C-m
tmux send-keys -t $SESSION_NAME:0.1 "cd $PROJECT_ROOT && claude" C-m

# Cynthia pane
tmux send-keys -t $SESSION_NAME:0.2 "echo '🟣 Cynthia - QA Engineer'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo '任务: 测试基础设施、E2E测试、质量门禁'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo ''" C-m
tmux send-keys -t $SESSION_NAME:0.2 "cd $PROJECT_ROOT && claude" C-m

# Elon pane
tmux send-keys -t $SESSION_NAME:0.3 "echo '🟡 Elon - PM/Architect'" C-m
tmux send-keys -t $SESSION_NAME:0.3 "echo '任务: PRD/Spec、架构方向、里程碑规划'" C-m
tmux send-keys -t $SESSION_NAME:0.3 "echo ''" C-m
tmux send-keys -t $SESSION_NAME:0.3 "cd $PROJECT_ROOT && claude" C-m

# Set pane titles
tmux select-pane -t $SESSION_NAME:0.0 -T "GLM (Coordinator)"
tmux select-pane -t $SESSION_NAME:0.1 -T "Ryan (Developer)"
tmux select-pane -t $SESSION_NAME:0.2 -T "Cynthia (QA)"
tmux select-pane -t $SESSION_NAME:0.3 -T "Elon (PM)"

# Adjust pane sizes (GLM gets more space as coordinator)
tmux resize-pane -t $SESSION_NAME:0.0 -y 15
tmux resize-pane -t $SESSION_NAME:0.3 -y 15

# Select GLM pane as active
tmux select-pane -t $SESSION_NAME:0.0

# Attach to session
tmux attach-session -t $SESSION_NAME
