import { describe, expect, it } from "vitest";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

import { CoaxedPrompt, MissingVariableError } from "../../src/index.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FIXTURE_ROOT = resolve(__dirname, "../__fixtures__/prompts");

describe("CoaxedPrompt", () => {
  describe("loading", () => {
    it("reads prompt.jinja from the artifact directory", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`);
      expect(`${p}`).toContain("{{ readme }}");
      expect(`${p}`).toContain("{{ stars }}");
    });

    it("throws an informative error when prompt.jinja is missing from the directory", () => {
      expect(() => new CoaxedPrompt(`${FIXTURE_ROOT}/missing_template`)).toThrow(
        /prompt\.jinja|template|ENOENT|missing/i,
      );
    });
  });

  describe("toString coercion", () => {
    it("returns the raw template via template-literal interpolation", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/bool_classifier`);
      expect(`${p}`).toContain("{{ text }}");
      expect(`${p}`).toContain("Respond with the predicted output.");
    });

    it("returns the raw template via String() coercion", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/bool_classifier`);
      expect(String(p)).toContain("{{ text }}");
    });
  });

  describe("rendering", () => {
    it("substitutes variables into the template", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`);
      const filled = p({ readme: "# awesome-skills", stars: 521 });
      expect(filled).toContain("# awesome-skills");
      expect(filled).toContain("521");
      expect(filled).not.toContain("{{ readme }}");
      expect(filled).not.toContain("{{ stars }}");
    });

    it("merges call-time vars with bound defaults; call-time wins", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`, {
        readme: "default-readme",
        stars: 0,
      });
      const filled = p({ stars: 999 });
      expect(filled).toContain("default-readme");
      expect(filled).toContain("999");
      expect(filled).not.toContain("\n0\n");
    });

    it("throws MissingVariableError when a required variable is absent", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`);
      expect(() => p({ readme: "x" })).toThrow(MissingVariableError);
    });

    it("includes the missing variable name in the error", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`);
      try {
        p({ readme: "x" });
        expect.fail("expected MissingVariableError");
      } catch (err) {
        expect(err).toBeInstanceOf(MissingVariableError);
        expect((err as Error).message).toContain("stars");
      }
    });
  });

  describe("fields", () => {
    it("lists the input variable names from the template", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/enum_classifier`);
      expect([...p.fields].sort()).toEqual(["readme", "stars"]);
    });

    it("returns the same array reference on repeated access (cached)", () => {
      const p = new CoaxedPrompt(`${FIXTURE_ROOT}/bool_classifier`);
      expect(p.fields).toBe(p.fields);
    });
  });
});
