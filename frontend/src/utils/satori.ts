import DOMPurify from "dompurify";

export interface SatoriElement {
  type: string;
  attrs?: Record<string, any>;
  children?: SatoriElement[];
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function attrValue(value: any): string {
  if (value === null || value === undefined) return "";
  return String(value).replace(/"/g, "&quot;");
}

function renderAttrs(attrs: Record<string, any> | undefined, allowed: string[]): string {
  if (!attrs) return "";
  return allowed
    .filter((key) => attrs[key] !== undefined && attrs[key] !== null)
    .map((key) => ` ${key}="${attrValue(attrs[key])}"`)
    .join("");
}

export function renderSatori(elements: SatoriElement | SatoriElement[] | undefined): string {
  if (!elements) return "";
  const list = Array.isArray(elements) ? elements : [elements];
  return list.map(renderElement).join("");
}

const ALLOWED_TAGS = ["p", "b", "strong", "i", "em", "u", "ins", "s", "del", "spl", "code", "sup", "sub"];

function renderElement(el: SatoriElement): string {
  const { type, attrs, children } = el;

  switch (type) {
    case "text": {
      const text = attrs?.text ?? "";
      return escapeHtml(String(text)).replace(/\n/g, "<br>");
    }
    case "img":
    case "image": {
      const src = attrs?.src ?? "";
      const sanitized = DOMPurify.sanitize(src, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
      return `<img src="${attrValue(sanitized)}"${renderAttrs(attrs, ["alt", "title", "width", "height"])} />`;
    }
    case "at": {
      const name = attrs?.name ?? attrs?.id ?? "";
      return `<span class="satori-at">@${escapeHtml(String(name))}</span>`;
    }
    case "sharp": {
      const name = attrs?.name ?? attrs?.id ?? "";
      return `<span class="satori-sharp">#${escapeHtml(String(name))}</span>`;
    }
    case "a":
    case "link": {
      const href = attrs?.href ?? "";
      const sanitized = DOMPurify.sanitize(href, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
      return `<a href="${attrValue(sanitized)}" target="_blank" rel="noopener noreferrer"${renderAttrs(attrs, ["title"])}>${renderSatori(children)}</a>`;
    }
    case "quote": {
      return `<blockquote class="satori-quote">${renderSatori(children)}</blockquote>`;
    }
    case "br":
    case "newline":
      return "<br>";
    case "face": {
      const name = attrs?.name ?? attrs?.id ?? "";
      return `<span class="satori-face">[${escapeHtml(String(name))}]</span>`;
    }
    case "video":
    case "audio":
    case "file": {
      const src = attrs?.src ?? "";
      const sanitized = DOMPurify.sanitize(src, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
      return `<a href="${attrValue(sanitized)}" target="_blank" rel="noopener noreferrer">[${escapeHtml(type)}]</a>`;
    }
    default: {
      const childHtml = renderSatori(children);
      if (ALLOWED_TAGS.includes(type)) {
        return `<${type}>${childHtml}</${type}>`;
      }
      return `<span class="satori-${escapeHtml(type)}">${childHtml}</span>`;
    }
  }
}

/** 从 Satori elements 提取纯文本（用于简单预览） */
export function extractText(elements: SatoriElement | SatoriElement[] | undefined): string {
  if (!elements) return "";
  const list = Array.isArray(elements) ? elements : [elements];
  return list
    .map((el) => {
      if (el.type === "text") return String(el.attrs?.text ?? "");
      if (el.children) return extractText(el.children);
      return "";
    })
    .join("");
}

export function buildTextElement(text: string): SatoriElement {
  return { type: "text", attrs: { text } };
}
