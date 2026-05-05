import { z, type ZodType } from "zod";

export interface MetaField {
  type: string;
  desc?: string | null;
  values?: string[] | null;
}

type Resolver = (field: MetaField) => ZodType;

const RESOLVERS: Record<string, Resolver> = {
  bool: () => z.boolean(),
  int: () => z.number().int(),
  float: () => z.number(),
  str: (f) =>
    f.values && f.values.length > 0 ? z.enum(f.values as [string, ...string[]]) : z.string(),
  enum: (f) => {
    const values = f.values ?? [];
    if (values.length === 0) {
      throw new Error("enum output requires a non-empty `values` list");
    }
    return z.enum(values as [string, ...string[]]);
  },
  bytes: () => {
    throw new Error("Unsupported output type for structured output: bytes");
  },
};

export function resolveFieldType(field: MetaField): ZodType {
  const resolver = RESOLVERS[field.type];
  if (!resolver) throw new Error(`Unknown output type: ${field.type}`);
  return resolver(field);
}
