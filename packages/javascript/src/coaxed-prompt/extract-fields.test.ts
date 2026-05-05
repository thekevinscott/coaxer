import { describe, expect, it } from "vitest";

import { extractFields } from "./extract-fields.js";

describe("extractFields", () => {
  it("returns an empty array when the template has no slots", () => {
    expect([...extractFields("hello world")]).toEqual([]);
  });

  it("extracts a single slot name", () => {
    expect([...extractFields("hi {{ name }}")]).toEqual(["name"]);
  });

  it("extracts multiple distinct slot names in declaration order", () => {
    const fields = extractFields("a={{ a }} b={{ b }} c={{ c }}");
    expect([...fields]).toEqual(["a", "b", "c"]);
  });

  it("deduplicates repeated names", () => {
    expect([...extractFields("{{ x }} and {{ x }} again")]).toEqual(["x"]);
  });

  it.each([
    ["{{name}}", "name"],
    ["{{   name   }}", "name"],
    ["{{\tname\t}}", "name"],
  ])("tolerates whitespace around the slot name (%s)", (template, expected) => {
    expect([...extractFields(template)]).toEqual([expected]);
  });

  it("ignores names that don't start with a letter or underscore", () => {
    expect([...extractFields("{{ 1bad }}")]).toEqual([]);
  });

  it("returns a frozen array", () => {
    const fields = extractFields("{{ x }}");
    expect(Object.isFrozen(fields)).toBe(true);
  });
});
