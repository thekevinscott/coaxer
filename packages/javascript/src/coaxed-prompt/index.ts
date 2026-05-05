import { readFileSync } from "node:fs";
import { join } from "node:path";

import nunjucks from "nunjucks";
import type { ZodType } from "zod";

import { MissingVariableError } from "../errors.js";
import { buildResponseFormat } from "./build-response-format.js";
import { extractFields } from "./extract-fields.js";

export interface CoaxedPrompt {
  (vars?: Record<string, unknown>): string;
  readonly fields: readonly string[];
  responseFormat(): ZodType;
  toString(): string;
}

export interface CoaxedPromptConstructor {
  new (path: string, bound?: Record<string, unknown>): CoaxedPrompt;
}

function makeCoaxedPrompt(path: string, bound: Record<string, unknown> = {}): CoaxedPrompt {
  const templateText = readFileSync(join(path, "prompt.jinja"), "utf8");
  const env = new nunjucks.Environment(undefined, { throwOnUndefined: true });

  let cachedFields: readonly string[] | undefined;
  let cachedSchema: ZodType | undefined;

  const fields = (): readonly string[] => {
    if (!cachedFields) cachedFields = extractFields(templateText);
    return cachedFields;
  };

  const instance = ((vars: Record<string, unknown> = {}): string => {
    const merged = { ...bound, ...vars };
    for (const name of fields()) {
      if (merged[name] === undefined) throw new MissingVariableError(name);
    }
    return env.renderString(templateText, merged);
  }) as CoaxedPrompt;

  Object.defineProperty(instance, "fields", {
    get: fields,
    enumerable: true,
  });

  instance.responseFormat = (): ZodType => {
    if (!cachedSchema) cachedSchema = buildResponseFormat(path);
    return cachedSchema;
  };

  instance.toString = (): string => templateText;

  return instance;
}

export const CoaxedPrompt: CoaxedPromptConstructor =
  makeCoaxedPrompt as unknown as CoaxedPromptConstructor;
