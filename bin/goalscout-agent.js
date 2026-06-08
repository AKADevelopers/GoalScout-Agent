#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..");
const args = ["-m", "football_live_agent.cli", ...process.argv.slice(2)];
const env = {
  ...process.env,
  PYTHONPATH: process.env.PYTHONPATH
    ? `${packageRoot}${path.delimiter}${process.env.PYTHONPATH}`
    : packageRoot,
};

const candidates = [];

if (process.env.PYTHON) {
  candidates.push({ command: process.env.PYTHON, args: [] });
}

if (process.platform === "win32") {
  candidates.push({ command: "py", args: ["-3"] });
}

candidates.push({ command: "python3", args: [] });
candidates.push({ command: "python", args: [] });

for (const candidate of candidates) {
  const result = spawnSync(candidate.command, [...candidate.args, ...args], {
    env,
    stdio: "inherit",
  });

  if (result.error) {
    if (result.error.code === "ENOENT") {
      continue;
    }
    console.error(`GoalScout Agent could not start Python: ${result.error.message}`);
    process.exit(1);
  }

  if (result.signal) {
    console.error(`GoalScout Agent stopped after signal ${result.signal}.`);
    process.exit(1);
  }

  process.exit(result.status ?? 0);
}

console.error("GoalScout Agent requires Python 3.11 or newer. Install Python, then run this command again.");
process.exit(1);
