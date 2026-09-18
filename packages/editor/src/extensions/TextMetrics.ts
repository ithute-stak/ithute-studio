import { Extension } from "@tiptap/core";
export const TextMetrics = Extension.create({
  name: "textMetrics",
  addGlobalAttributes() {
    return [{ types: ["textStyle"], attributes: {
      fontSize: { default: null, parseHTML: (el) => el.style.fontSize || null, renderHTML: (attrs) => attrs.fontSize ? { style: `font-size:${attrs.fontSize}` } : {} },
      lineHeight: { default: null, parseHTML: (el) => el.style.lineHeight || null, renderHTML: (attrs) => attrs.lineHeight ? { style: `line-height:${attrs.lineHeight}` } : {} },
      letterSpacing: { default: null, parseHTML: (el) => el.style.letterSpacing || null, renderHTML: (attrs) => attrs.letterSpacing ? { style: `letter-spacing:${attrs.letterSpacing}` } : {} }
    }}];
  }
});
