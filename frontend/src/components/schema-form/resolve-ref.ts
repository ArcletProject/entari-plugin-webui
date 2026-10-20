export type Schema = Record<string, unknown>;

function unescapeToken(token: string): string {
  return decodeURIComponent(token).replace(/~1/g, "/").replace(/~0/g, "~");
}

function resolvePointer(pointer: string, root: Schema): unknown {
  let node: unknown = root;
  for (const raw of pointer.split("/")) {
    if (!node || typeof node !== "object") return undefined;
    node = (node as Record<string, unknown>)[unescapeToken(raw)];
  }
  return node;
}

/**
 * 按 JSON Pointer 解析 `$ref`（相对整份 schema），并保留引用处覆盖的 title/description。
 */
export function resolveRef(schema: Schema, root: Schema): Schema {
  if (!schema) return {};
  if (!schema.$ref) return schema;
  const ref = schema.$ref;
  if (typeof ref !== "string" || !ref.startsWith("#/")) return schema;
  const target = resolvePointer(ref.slice(2), root);
  if (!target || typeof target !== "object") return schema;
  const def = target as Schema;
  return {
    ...def,
    description: schema.description ?? def.description,
    title: schema.title ?? def.title,
  };
}
