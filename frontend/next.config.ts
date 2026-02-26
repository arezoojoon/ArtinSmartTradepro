import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "ui-avatars.com" },
      { protocol: "https", hostname: "**.transparenttextures.com" },
    ],
  },
  // Suppress hydration warnings from browser extensions
  reactStrictMode: true,
};

export default nextConfig;
