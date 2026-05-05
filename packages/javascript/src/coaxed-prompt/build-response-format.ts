import { readFileSync } from "node:fs";
import { join } from "node:path";

import { z, type ZodType } from "zod";

import { resolveFieldType, type MetaField } from "./resolve-field-type.js";

interface Meta {
  output_name?: string;
  fields: {
    inputs: Record<string, MetaField>;
    output: MetaField;
  };
}

export function buildResponseFormat(path: string): ZodType {
  const meta = JSON.parse(readFileSync(join(path, "meta.json"), "utf8")) as Meta;
  const outputName = meta.output_name ?? "output";
  const out = meta.fields.output;

  let valueSchema = resolveFieldType(out);
  if (out.desc) {
    valueSchema = valueSchema.describe(out.desc);
  }

  return z.object({ [outputName]: valueSchema });
}
