import { spawnSync } from "node:child_process";
import { mkdtempSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";
import { query } from "@anthropic-ai/claude-agent-sdk";

import { CoaxedPrompt } from "../../src/index.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, "..", "..");
const BIN = join(PACKAGE_ROOT, "dist", "bin.js");
const FIXTURE = join(__dirname, "labels", "sentiment");
const REPO_ROOT = resolve(PACKAGE_ROOT, "..", "..");

function locateCoaxOnPath(): string {
  if (process.env.COAXER_E2E_COAX_BIN_DIR) return process.env.COAXER_E2E_COAX_BIN_DIR;
  for (const venv of [".venv-313", ".venv"]) {
    const candidate = join(REPO_ROOT, venv, "bin", "coax");
    if (existsSync(candidate)) return dirname(candidate);
  }
  return "";
}

describe("end-to-end: JS bin → real coax → CoaxedPrompt → real LLM", () => {
  it("compiles a label folder and the rendered prompt elicits a usable response", async () => {
    if (!existsSync(BIN)) {
      throw new Error(`dist/bin.js missing — run \`npm run build\` before the e2e suite.`);
    }

    const out = mkdtempSync(join(tmpdir(), "coaxer-e2e-"));

    const coaxDir = locateCoaxOnPath();
    const augmentedPath = coaxDir
      ? `${coaxDir}:${process.env.PATH ?? ""}`
      : (process.env.PATH ?? "");

    const distill = spawnSync("node", [BIN, FIXTURE, "--out", out], {
      encoding: "utf-8",
      env: { ...process.env, PATH: augmentedPath },
    });
    expect(distill.status, `coax stderr: ${distill.stderr}`).toBe(0);

    const p = new CoaxedPrompt(out);
    expect(p.fields).toContain("text");

    const filled = p({
      text: "I cannot believe how good this is — best purchase of the year.",
    });
    expect(filled).toContain("best purchase of the year");

    const allowed = ["positive", "negative", "neutral"];
    let assistantText = "";
    for await (const message of query({
      prompt: `${filled}\n\nReply with exactly one word, lowercase: ${allowed.join(", ")}. No tools, no explanation.`,
      options: {
        systemPrompt:
          "You are a sentiment classifier. Reply with exactly one word from the user's allowed set. Do not use any tools.",
        disallowedTools: [
          "Read",
          "Write",
          "Edit",
          "Bash",
          "BashOutput",
          "Glob",
          "Grep",
          "Task",
          "WebFetch",
          "WebSearch",
          "TodoWrite",
          "NotebookEdit",
          "Skill",
        ],
        settingSources: [],
      },
    })) {
      if (message.type === "assistant") {
        for (const block of message.message.content) {
          if (block.type === "text") assistantText += block.text;
        }
      }
    }

    const lowered = assistantText.toLowerCase();
    expect(
      allowed.some((v) => lowered.includes(v)),
      assistantText,
    ).toBe(true);
  });
});
