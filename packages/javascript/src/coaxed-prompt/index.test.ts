import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { CoaxedPrompt } from "./index.js";
import { MissingVariableError } from "../errors.js";

function makeArtifact(template: string, meta?: object): string {
  const dir = mkdtempSync(join(tmpdir(), "coaxed-prompt-"));
  writeFileSync(join(dir, "prompt.jinja"), template);
  if (meta) writeFileSync(join(dir, "meta.json"), JSON.stringify(meta));
  return dir;
}

describe("CoaxedPrompt", () => {
  it("reads prompt.jinja at construction; toString returns the raw template", () => {
    const dir = makeArtifact("Hello {{ name }}!");
    const p = new CoaxedPrompt(dir);
    expect(`${p}`).toBe("Hello {{ name }}!");
  });

  it("throws when prompt.jinja is missing", () => {
    const dir = mkdtempSync(join(tmpdir(), "coaxed-prompt-missing-"));
    expect(() => new CoaxedPrompt(dir)).toThrow(/prompt\.jinja|ENOENT/i);
  });

  it("substitutes vars on call", () => {
    const dir = makeArtifact("Hi {{ name }}, you have {{ count }} messages.");
    const p = new CoaxedPrompt(dir);
    expect(p({ name: "Ada", count: 3 })).toBe("Hi Ada, you have 3 messages.");
  });

  it("merges bound defaults with call-time vars; call-time wins", () => {
    const dir = makeArtifact("{{ greeting }} {{ name }}");
    const p = new CoaxedPrompt(dir, { greeting: "Hi", name: "default" });
    expect(p({ name: "Ada" })).toBe("Hi Ada");
  });

  it("throws MissingVariableError when a required var is absent", () => {
    const dir = makeArtifact("{{ a }} and {{ b }}");
    const p = new CoaxedPrompt(dir);
    expect(() => p({ a: 1 })).toThrow(MissingVariableError);
  });

  it("p.fields lists template variable names and is cached on the instance", () => {
    const dir = makeArtifact("{{ x }} {{ y }}");
    const p = new CoaxedPrompt(dir);
    expect([...p.fields].sort()).toEqual(["x", "y"]);
    expect(p.fields).toBe(p.fields);
  });

  it("p.responseFormat() reads meta.json and caches the result", () => {
    const dir = makeArtifact("{{ x }}", {
      output_name: "label",
      fields: { inputs: {}, output: { type: "bool" } },
    });
    const p = new CoaxedPrompt(dir);
    const first = p.responseFormat();
    expect(p.responseFormat()).toBe(first);
  });
});
