/**
 * A same-origin development proxy, so the browser can call FastAPI safely on
 * localhost. Start uvicorn on port 8000 before starting Next.js.
 */
const nextConfig = {
  async rewrites() {
    return [{ source: '/api/:path*', destination: 'http://127.0.0.1:8000/:path*' }];
  },
};
export default nextConfig;
