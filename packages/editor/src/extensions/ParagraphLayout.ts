import { Extension } from "@tiptap/core";
export const ParagraphLayout = Extension.create({
  name: "paragraphLayout",
  addGlobalAttributes() {
    return [{ types: ["paragraph", "heading"], attributes: {
      indent: { default: 0, parseHTML: (el) => Number(el.getAttribute("data-indent") || 0), renderHTML: (attrs) => attrs.indent ? { "data-indent": String(attrs.indent), style: `margin-left:${attrs.indent * 24}px` } : {} },
      firstLineIndent: { default: 0, parseHTML: (el) => Number(el.getAttribute("data-first-line-indent") || 0), renderHTML: (attrs) => attrs.firstLineIndent ? { "data-first-line-indent": String(attrs.firstLineIndent), style: `text-indent:${attrs.firstLineIndent}mm` } : {} },
      border: { default: null, parseHTML: (el) => el.getAttribute("data-border"), renderHTML: (attrs) => attrs.border ? { "data-border": attrs.border, style: `border:${attrs.border};padding:4px` } : {} },
      shading: { default: null, parseHTML: (el) => el.getAttribute("data-shading"), renderHTML: (attrs) => attrs.shading ? { "data-shading": attrs.shading, style: `background:${attrs.shading}` } : {} }
    }}];
  }
});
