import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Security headers applied to all responses
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-DNS-Prefetch-Control", value: "on" },
        ],
      },
    ];
  },

  // Rewrites: transparent proxy to FastAPI (dev convenience)
  // In production, use the /api/proxy/* Next.js route handlers instead.
  async rewrites() {
    return [];
  },

  images: {
    // Allow institution logo images from common CDN/storage origins
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },

  // Strict mode for catching hydration issues early
  reactStrictMode: true,
};

export default nextConfig;
