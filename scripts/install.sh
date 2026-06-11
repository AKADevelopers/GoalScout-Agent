#!/bin/sh
set -eu

PACKAGE="github:AKADevelopers/GoalScout-Agent"

if ! command -v npm >/dev/null 2>&1; then
  echo "GoalScout Agent install needs npm. Install Node.js first, then run this installer again." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "GoalScout Agent needs Python 3.11 or newer. Install Python first, then run this installer again." >&2
  exit 1
fi

if [ "${GOALSCOUT_INSTALL_DRY_RUN:-}" = "1" ]; then
  echo "npm install -g $PACKAGE"
  exit 0
fi

npm install -g "$PACKAGE"
echo "GoalScout Agent installed. Run: goalscout-agent onboard"
