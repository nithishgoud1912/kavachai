import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  output: "standalone",
  async headers() {
    const devEval = process.env.NODE_ENV === "development" ? " 'unsafe-eval'" : "";
    return [{ source: "/:path*", headers: [
      { key: "Content-Security-Policy", value: `default-src 'self'; script-src 'self' 'unsafe-inline'${devEval}; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data: blob:; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; frame-src 'self' blob:` },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "no-referrer" },
    ] }];
  },
};
export default nextConfig;
