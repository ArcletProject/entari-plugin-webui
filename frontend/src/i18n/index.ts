import { createI18n } from "vue-i18n";
import zhCN from "./zh-CN";

const i18n = createI18n({ legacy: false, locale: "zh-CN", messages: { "zh-CN": zhCN } });
// 扩展词条在 useExtensionsManifest 获取后合并（phase-10/11 实现 mergeLocaleMessage）
export default i18n;
