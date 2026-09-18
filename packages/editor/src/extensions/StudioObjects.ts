import { Node, mergeAttributes } from "@tiptap/core";

function objectNode(name: string, cssClass: string, defaultLabel: string) {
  return Node.create({
    name, group: "block", atom: true, selectable: true, draggable: true,
    addAttributes() { return { id:{default:null}, label: { default: defaultLabel }, value: { default: "" }, sourceUrl:{default:""}, width: { default: 100 }, align: { default: "center" }, metadata:{default:null} }; },
    parseHTML: () => [{ tag: `div[data-ithute-object="${name}"]` }],
    renderHTML: ({ HTMLAttributes }) => ["div", mergeAttributes(HTMLAttributes, { "data-ithute-object": name, class: cssClass }), HTMLAttributes.label]
  });
}

export const TextBox = Node.create({
  name:"textBox", group:"block", content:"block+", selectable:true, draggable:true, defining:true,
  addAttributes(){return {width:{default:100},align:{default:"left"},border:{default:"1px solid #9aa4b2"},shading:{default:"transparent"}};},
  parseHTML:()=>[{tag:'div[data-ithute-object="textBox"]'}],
  renderHTML:({HTMLAttributes})=>["div",mergeAttributes(HTMLAttributes,{"data-ithute-object":"textBox",class:"ithute-object ithute-text-box"}),0]
});
export const Signature = objectNode("signature", "ithute-object ithute-signature", "Signature");
export const Stamp = objectNode("stamp", "ithute-object ithute-stamp", "Official stamp");
export const QrCode = objectNode("qrCode", "ithute-object ithute-qr", "QR code");
export const Chart = objectNode("chart", "ithute-object ithute-chart", "Chart");
export const Logo = objectNode("logo", "ithute-object ithute-logo", "Logo");
export const Letterhead = objectNode("letterhead", "ithute-object ithute-letterhead", "Letterhead");
