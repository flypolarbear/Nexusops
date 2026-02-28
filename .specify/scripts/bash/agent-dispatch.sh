#!/bin/bash
# =============================================================================
# Agent Dispatch Script for OMO × Spec-Kit Bridge
# =============================================================================
# 
# Usage: agent-dispatch.sh <command> <phase> [activity]
#
# Returns the recommended agent for a given Spec-Kit command phase.
# Sisyphus calls this script to determine which specialist agent to dispatch.
#
# Examples:
#   ./agent-dispatch.sh speckit.plan research      # → librarian
#   ./agent-dispatch.sh speckit.plan architecture  # → oracle
#   ./agent-dispatch.sh speckit.plan review        # → momus
#   ./agent-dispatch.sh speckit.specify clarify    # → metis
#   ./agent-dispatch.sh speckit.implement frontend # → visual-engineering
#
# Exit codes:
#   0 - Success, outputs agent name
#   1 - Invalid arguments
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Agent Mapping Table
# Format: "command:phase[:activity]" -> "agent"
# -----------------------------------------------------------------------------
dispatch_agent() {
    local command="$1"
    local phase="$2"
    local activity="${3:-}"
    
    # Build key - if phase is "-" or empty, skip it
    local key
    if [ -z "$phase" ] || [ "$phase" = "-" ]; then
        key="${command}:${activity}"
    elif [ -n "$activity" ]; then
        key="${command}:${phase}:${activity}"
    else
        key="${command}:${phase}"
    fi
    
    case "$key" in
        # speckit.specify
        "speckit.specify:specify")           echo "sisyphus" ;;
        "speckit.specify:clarify")           echo "metis" ;;
        
        # speckit.clarify
        "speckit.clarify:all")               echo "metis" ;;
        
        # speckit.plan
        "speckit.plan:research")             echo "librarian" ;;
        "speckit.plan:architecture")         echo "oracle" ;;
        "speckit.plan:task_planning")        echo "prometheus" ;;
        "speckit.plan:planning")             echo "prometheus" ;;
        "speckit.plan:review")               echo "momus" ;;
        "speckit.plan:docs")                 echo "writing" ;;
        "speckit.plan:documentation")        echo "writing" ;;
        
        # speckit.tasks
        "speckit.tasks:decompose")           echo "sisyphus" ;;
        "speckit.tasks:analyze")             echo "momus" ;;
        
        # speckit.implement (phase can be "-" for direct activity dispatch)
        "speckit.implement:frontend")        echo "visual-engineering" ;;
        "speckit.implement:ui")              echo "visual-engineering" ;;
        "speckit.implement:complex")         echo "ultrabrain" ;;
        "speckit.implement:logic")           echo "ultrabrain" ;;
        "speckit.implement:quick")           echo "quick" ;;
        "speckit.implement:fix")             echo "quick" ;;
        "speckit.implement:review")          echo "oracle" ;;
        "speckit.implement:docs")            echo "writing" ;;
        
        # spec (magic command - full workflow)
        "spec:all")                          echo "sisyphus" ;;
        "spec:specify")                      echo "sisyphus" ;;
        "spec:plan")                        echo "sisyphus" ;;
        "spec:tasks")                       echo "sisyphus" ;;
        
        # Default fallback
        *)                                    echo "sisyphus" ;;
    esac
}

# -----------------------------------------------------------------------------
# Help message
# -----------------------------------------------------------------------------
show_help() {
    cat << EOF
Agent Dispatch Script - OMO × Spec-Kit Bridge

Usage: $(basename "$0") <command> <phase> [activity]

Arguments:
  command   Spec-Kit command (speckit.specify, speckit.plan, speckit.tasks, speckit.implement)
  phase     Phase within the command (research, architecture, review, etc.)
  activity  Optional activity sub-type (frontend, complex, quick, etc.)

Available Mappings:

  Command               Phase          Activity      Agent
  ──────────────────────────────────────────────────────────
  speckit.specify       specify        -             sisyphus
  speckit.specify       clarify        -             metis
  speckit.clarify       all            -             metis
  speckit.plan          research       -             librarian
  speckit.plan          architecture   -             oracle
  speckit.plan          review         -             momus
  speckit.plan          docs           -             writing
  speckit.tasks         decompose      -             sisyphus
  speckit.tasks         analyze        -             momus
  speckit.implement     -              frontend      visual-engineering
  speckit.implement     -              complex       ultrabrain
  speckit.implement     -              quick         quick
  speckit.implement     -              review        oracle

Examples:
  $(basename "$0") speckit.plan research
  $(basename "$0") speckit.implement - frontend
  $(basename "$0") speckit.plan review

EOF
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    if [ $# -lt 2 ]; then
        echo "Error: Missing required arguments" >&2
        echo "Usage: $(basename "$0") <command> <phase> [activity]" >&2
        exit 1
    fi
    
    local command="$1"
    local phase="$2"
    local activity="${3:-}"
    
    dispatch_agent "$command" "$phase" "$activity"
}

main "$@"
