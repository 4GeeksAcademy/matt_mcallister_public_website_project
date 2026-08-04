import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Allow importing shared packages from the monorepo root
  experimental: {
    externalDir: true,
  },
  outputFileTracingRoot: path.join(__dirname, "../.."),
  webpack: (config) => {
    // packages/trackflow-core uses NodeNext .js import specifiers in .ts sources
    config.resolve.extensionAlias = {
      ...(config.resolve.extensionAlias ?? {}),
      ".js": [".ts", ".tsx", ".js"],
    };
    return config;
  },
};

export default nextConfig;
