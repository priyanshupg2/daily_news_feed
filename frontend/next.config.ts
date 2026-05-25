import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // The design system lives one level up at ../design-system. Widen the
  // Turbopack filesystem root so layout.tsx can import its CSS directly.
  turbopack: {
    root: path.join(__dirname, ".."),
  },
};

export default nextConfig;
