const SLOT_RE = /\{\{\s*([A-Za-z_][A-Za-z0-9_]*)/g;

export function extractFields(template: string): readonly string[] {
  const seen = new Set<string>();
  for (const match of template.matchAll(SLOT_RE)) {
    const name = match[1];
    if (name) seen.add(name);
  }
  return Object.freeze([...seen]);
}
