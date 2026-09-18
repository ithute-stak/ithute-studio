import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  transpilePackages: ["@ithute/document-editor", "@ithute/document-schema", "@ithute/template-engine"],
};
export default nextConfig;
