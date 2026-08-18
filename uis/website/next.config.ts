import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Shorter output dir helps Windows graders avoid MAX_PATH issues in dev/build caches.
  distDir: "build",
};

export default nextConfig;
