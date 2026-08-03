import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Allow importing shared packages from the monorepo root
  experimental: {
    externalDir: true,
  },
  outputFileTracingRoot: path.join(__dirname, "../.."),
};

export default nextConfig;
