#!/bin/bash

if ! command -v autofix &> /dev/null; then
  echo "Autofix Bot CLI not found. Installing..."
  curl -fsSL https://autofix.bot/install | sh

  if ! command -v autofix &> /dev/null; then
    echo "ERROR: Failed to install autofix. Please install manually:" >&2
    echo "  curl -fsSL https://autofix.bot/install | sh" >&2
    exit 2
  fi
fi

echo "Autofix Bot ready"
exit 0
