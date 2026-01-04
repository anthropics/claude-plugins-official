#!/bin/bash
# Check if ralph loop is active and return status
# Extracted to separate script for Claude Code compatibility (avoids multi-line bash in skill templates)

if [[ -f .claude/ralph-loop.local.md ]]; then
  ITERATION=$(grep '^iteration:' .claude/ralph-loop.local.md | sed 's/iteration: *//')
  echo "FOUND_LOOP=true"
  echo "ITERATION=$ITERATION"
else
  echo "FOUND_LOOP=false"
fi
