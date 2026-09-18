import type { Metadata } from "next";
import "./globals.css";
import "./studio-theme.css";
import "@ithute/document-editor/styles.css";

export const metadata: Metadata = {
  title: "Ithute Document Studio",
  description: "Create, automate and render professional documents.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
