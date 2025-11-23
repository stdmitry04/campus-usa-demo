import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [],
  eslint: {
    ignoreDuringBuilds: true
  }
};
export default nextConfig;
