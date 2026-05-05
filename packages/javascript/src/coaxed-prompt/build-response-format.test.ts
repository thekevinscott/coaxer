import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { describe, expect, it } from "vitest";
import { z } from "zod";

import { buildResponseFormat } from "./build-response-format.js";

function writeMeta(meta: unknown): string {
  const dir = mkdtempSync(join(tmpdir(), "build-response-format-"));
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "meta.json"), JSON.stringify(meta));
  return dir;
}

describe("buildResponseFormat", () => {
  it("uses meta.output_name as the field key", () => {
    const dir = writeMeta({
      output_name: "is_curated",
      fields: { inputs: {}, output: { type: "bool" } },
    });
    const schema = buildResponseFormat(dir) as z.ZodObject<z.ZodRawShape>;
    expect(Object.keys(schema.shape)).toEqual(["is_curated"]);
  });

  it("defaults to `output` when meta.json lacks output_name", () => {
    const dir = writeMeta({
      fields: { inputs: {}, output: { type: "bool" } },
    });
    const schema = buildResponseFormat(dir) as z.ZodObject<z.ZodRawShape>;
    expect(Object.keys(schema.shape)).toEqual(["output"]);
  });

  it("attaches the output's `desc` to the field schema", () => {
    const dir = writeMeta({
      fields: {
        inputs: {},
        output: { type: "bool", desc: "Whether the repo is curated" },
      },
    });
    const schema = buildResponseFormat(dir);
    const json = z.toJSONSchema(schema) as { properties: Record<string, { description?: string }> };
    expect(json.properties.output?.description).toBe("Whether the repo is curated");
  });

  it("throws when meta.json is missing", () => {
    expect(() => buildResponseFormat("/no/such/dir")).toThrow();
  });
});
