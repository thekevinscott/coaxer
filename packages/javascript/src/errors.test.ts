import { describe, expect, it } from "vitest";

import { MissingVariableError } from "./errors.js";

describe("MissingVariableError", () => {
  it("includes the missing variable name in the message", () => {
    const err = new MissingVariableError("readme");
    expect(err.message).toContain("readme");
  });

  it("identifies as MissingVariableError via the name field", () => {
    expect(new MissingVariableError("x").name).toBe("MissingVariableError");
  });

  it("is an Error so existing catch-blocks still match", () => {
    expect(new MissingVariableError("x")).toBeInstanceOf(Error);
  });
});
