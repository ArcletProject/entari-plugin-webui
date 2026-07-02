<template>
  <div
    class="markdown-body"
    :data-color-mode="isDark ? 'dark' : 'light'"
    :data-dark-theme="'github-markdown-dark'"
    :data-light-theme="'github-markdown-light'"
    v-html="renderedHtml"
  ></div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue";
import { marked } from "marked";
import { createHighlighterCore } from "shiki/core";
import { createJavaScriptRegexEngine } from "shiki/engine/javascript";
import githubDark from "@shikijs/themes/github-dark";
import githubLight from "@shikijs/themes/github-light";
import "github-markdown-css/github-markdown-light.css";
import githubMarkdownDarkCss from "github-markdown-css/github-markdown-dark.css?inline";

const props = defineProps<{ source?: string }>();

const isDark = ref(document.documentElement.classList.contains("dark"));
const renderedHtml = ref("");

const observer = new MutationObserver(() => {
  isDark.value = document.documentElement.classList.contains("dark");
});

// Inject the dark theme CSS scoped to our data-color-mode attribute so it
// overrides github-markdown-light.css when the app is in dark mode.
const darkStyleEl = document.createElement("style");
darkStyleEl.textContent = githubMarkdownDarkCss.replace(
  /\.markdown-body/g,
  '.markdown-body[data-color-mode="dark"]'
);
document.head.appendChild(darkStyleEl);

onMounted(() => {
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
});

onUnmounted(() => {
  observer.disconnect();
  darkStyleEl.remove();
});

// Common readme/programming languages loaded on demand.
const langLoaders: Record<string, () => Promise<{ default: any }>> = {
  bash: () => import("@shikijs/langs/bash"),
  c: () => import("@shikijs/langs/c"),
  cpp: () => import("@shikijs/langs/cpp"),
  css: () => import("@shikijs/langs/css"),
  docker: () => import("@shikijs/langs/docker"),
  go: () => import("@shikijs/langs/go"),
  html: () => import("@shikijs/langs/html"),
  ini: () => import("@shikijs/langs/ini"),
  java: () => import("@shikijs/langs/java"),
  javascript: () => import("@shikijs/langs/javascript"),
  js: () => import("@shikijs/langs/javascript"),
  json: () => import("@shikijs/langs/json"),
  jsx: () => import("@shikijs/langs/jsx"),
  markdown: () => import("@shikijs/langs/markdown"),
  powershell: () => import("@shikijs/langs/powershell"),
  python: () => import("@shikijs/langs/python"),
  py: () => import("@shikijs/langs/python"),
  rust: () => import("@shikijs/langs/rust"),
  rs: () => import("@shikijs/langs/rust"),
  shell: () => import("@shikijs/langs/shell"),
  sh: () => import("@shikijs/langs/shell"),
  sql: () => import("@shikijs/langs/sql"),
  toml: () => import("@shikijs/langs/toml"),
  tsx: () => import("@shikijs/langs/tsx"),
  typescript: () => import("@shikijs/langs/typescript"),
  ts: () => import("@shikijs/langs/typescript"),
  vue: () => import("@shikijs/langs/vue"),
  xml: () => import("@shikijs/langs/xml"),
  yaml: () => import("@shikijs/langs/yaml"),
  yml: () => import("@shikijs/langs/yaml"),
};

const langAliases: Record<string, string> = {
  js: "javascript",
  ts: "typescript",
  py: "python",
  sh: "bash",
  yml: "yaml",
  dockerfile: "docker",
  ps1: "powershell",
  ps: "powershell",
};

const highlighterPromise = createHighlighterCore({
  themes: [githubDark, githubLight],
  langs: [],
  langAlias: langAliases,
  engine: createJavaScriptRegexEngine(),
});

function resolveLang(lang: string): string | undefined {
  const normalized = lang.toLowerCase().trim();
  return langLoaders[normalized] ? normalized : langAliases[normalized];
}

function collectCodeLanguages(tokens: any[], langs: Set<string>) {
  for (const token of tokens) {
    if (token.type === "code" && token.lang) {
      const resolved = resolveLang(token.lang);
      if (resolved) langs.add(resolved);
    }
    if (token.tokens) {
      collectCodeLanguages(token.tokens, langs);
    }
    if (token.items) {
      for (const item of token.items) {
        if (item.tokens) collectCodeLanguages(item.tokens, langs);
      }
    }
  }
}

async function loadLanguages(highlighter: any, source: string) {
  const langs = new Set<string>();
  const tokens = marked.lexer(source);
  collectCodeLanguages(tokens, langs);
  await Promise.all(
    [...langs].map(async (lang) => {
      try {
        const mod = await langLoaders[lang]();
        await highlighter.loadLanguage(mod.default);
      } catch {
        // ignore unsupported languages
      }
    })
  );
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function renderMarkdown() {
  const highlighter = await highlighterPromise;
  const theme = isDark.value ? "github-dark" : "github-light";
  const source = props.source || "";

  await loadLanguages(highlighter, source);

  const renderer = new marked.Renderer();
  renderer.code = ({ text, lang }: any) => {
    const language = (lang && resolveLang(lang)) || lang || "text";
    try {
      return highlighter.codeToHtml(text, { lang: language, theme });
    } catch {
      return `<pre><code>${escapeHtml(text)}</code></pre>`;
    }
  };

  renderedHtml.value = marked.parse(source, { async: false, renderer }) as string;
}

watch([() => props.source, isDark], renderMarkdown, { immediate: true });
</script>
<style scoped>
.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
  padding: 32px;
}

@media (max-width: 767px) {
  .markdown-body {
    padding: 16px;
  }
}
</style>
