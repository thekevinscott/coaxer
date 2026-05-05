import { describe, expect, it } from "vitest";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import type { z } from "zod";

import { CoaxedPrompt } from "../../src/index.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FIXTURE_ROOT = resolve(__dirname, "../__fixtures__/prompts");

describe("CoaxedPrompt.responseFormat", () => {
  describe("type mapping", () => {
    it.each([
      ["bool_classifier", true],
      ["bool_classifier", false],
    ])("bool output accepts %s = %s", (fixture, value) => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/${fixture}`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ is_positive: value })).not.toThrow();
    });

    it("int output accepts integers", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/int_extractor`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ count: 42 })).not.toThrow();
    });

    it("int output rejects non-integers", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/int_extractor`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ count: 1.5 })).toThrow();
    });

    it("float output accepts numbers", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/float_extractor`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ measurement: 1.5 })).not.toThrow();
      expect(() => schema.parse({ measurement: 42 })).not.toThrow();
    });

    it("str output accepts strings", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/str_extractor`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ summary: "hello" })).not.toThrow();
    });

    it("str output rejects non-strings", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/str_extractor`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ summary: 42 })).toThrow();
    });
  });

  describe("enum output", () => {
    it("accepts listed values", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ is_collection: "yes" })).not.toThrow();
      expect(() => schema.parse({ is_collection: "no" })).not.toThrow();
    });

    it("rejects values outside the enum", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ is_collection: "maybe" })).toThrow();
    });
  });

  describe("output_name", () => {
    it("uses the meta.json output_name as the field key", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`);
      const schema = p.responseFormat() as z.ZodObject<z.ZodRawShape>;
      expect(Object.keys(schema.shape)).toEqual(["is_collection"]);
    });

    it("defaults to `output` when meta.json lacks output_name", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/no_output_name`);
      const schema = p.responseFormat() as z.ZodObject<z.ZodRawShape>;
      expect(Object.keys(schema.shape)).toEqual(["output"]);
    });
  });

  describe("unsupported types", () => {
    it("throws for bytes outputs", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/bytes_unsupported`);
      expect(() => p.responseFormat()).toThrow();
    });

    it("throws for unknown output types", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/unknown_type`);
      expect(() => p.responseFormat()).toThrow(/unknown/i);
    });

    it("throws when an enum output has no values", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_empty_values`);
      expect(() => p.responseFormat()).toThrow(/non-empty|values/i);
    });
  });

  describe("str output with values list", () => {
    it("treats `str` + `values` as an enum (legacy Python shape)", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/str_with_values`);
      const schema = p.responseFormat();
      expect(() => schema.parse({ category: "alpha" })).not.toThrow();
      expect(() => schema.parse({ category: "delta" })).toThrow();
    });
  });

  describe("caching", () => {
    it("returns the same schema instance on repeated calls", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/bool_classifier`);
      expect(p.responseFormat()).toBe(p.responseFormat());
    });
  });
});
