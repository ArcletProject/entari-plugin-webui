import DOMPurify from "dompurify";

const tagLike = /<[^>]+>/;

export function isHtml(content: string): boolean {
  return tagLike.test(content);
}

export function renderPlainText(content: string): string {
  return content
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

/** 仅转义 HTML 特殊字符，保留换行符 */
export function escapeHtml(content: string): string {
  return content
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** 将已转义文本的换行符转成 <br>，用于 v-html 展示 */
export function nl2br(content: string): string {
  return content.replace(/\n/g, "<br>");
}

export function renderContent(content: string): string {
  if (isHtml(content)) {
    return DOMPurify.sanitize(content, {
      ALLOWED_TAGS: [
        "p",
        "br",
        "b",
        "i",
        "em",
        "strong",
        "a",
        "img",
        "span",
        "div",
        "ul",
        "ol",
        "li",
        "code",
        "pre",
      ],
      ALLOWED_ATTR: ["src", "alt", "title", "href", "target", "class", "style"],
    });
  }
  return renderPlainText(content);
}
