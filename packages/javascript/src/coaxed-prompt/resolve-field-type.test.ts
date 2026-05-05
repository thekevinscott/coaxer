import { describe, expect, it } from "vitest";

import { resolveFieldType, type MetaField } from "./resolve-field-type.js";

function field(overrides: Partial<MetaField> & { type: string }): MetaField {
  return { desc: null, values: null, ...overrides };
}

describe("resolveFieldType", () => {
  describe("scalar types", () => {
    it.each([
      ["bool", true],
      ["bool", false],
    ])("bool accepts %s", (_t, value) => {
      expect(() => resolveFieldType(field({ type: "bool" })).parse(value)).not.toThrow();
    });

    it("int accepts integers", () => {
      expect(() => resolveFieldType(field({ type: "int" })).parse(42)).not.toThrow();
    });

    it("int rejects non-integers", () => {
      expect(() => resolveFieldType(field({ type: "int" })).parse(1.5)).toThrow();
    });

    it("float accepts numbers", () => {
      expect(() => resolveFieldType(field({ type: "float" })).parse(1.5)).not.toThrow();
    });

    it("str accepts strings", () => {
      expect(() => resolveFieldType(field({ type: "str" })).parse("hello")).not.toThrow();
    });
  });

  describe("enum / values", () => {
    it("enum with values accepts listed values", () => {
      const schema = resolveFieldType(field({ type: "enum", values: ["a", "b"] }));
      expect(() => schema.parse("a")).not.toThrow();
    });

    it("enum with values rejects unlisted values", () => {
      const schema = resolveFieldType(field({ type: "enum", values: ["a", "b"] }));
      expect(() => schema.parse("c")).toThrow();
    });

    it("enum without values throws at construction", () => {
      expect(() => resolveFieldType(field({ type: "enum", values: null }))).toThrow(/non-empty/i);
    });

    it("str + values is treated as an enum (legacy Python shape)", () => {
      const schema = resolveFieldType(field({ type: "str", values: ["a", "b"] }));
      expect(() => schema.parse("a")).not.toThrow();
      expect(() => schema.parse("c")).toThrow();
    });
  });

  describe("unsupported / unknown types", () => {
    it("bytes throws", () => {
      expect(() => resolveFieldType(field({ type: "bytes" }))).toThrow(/bytes/i);
    });

    it("unknown types throw with a clear message", () => {
      expect(() => resolveFieldType(field({ type: "wat" }))).toThrow(/unknown.*wat/i);
    });
  });
});
