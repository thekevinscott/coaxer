#!/usr/bin/env node
import { spawn } from "node:child_process";

const child = spawn("coax", process.argv.slice(2), { stdio: "inherit" });
child.on("exit", (code) => process.exit(code ?? 0));
