import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Shorter output dir helps Windows graders avoid MAX_PATH issues in dev/build caches.
  distDir: "build",
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
