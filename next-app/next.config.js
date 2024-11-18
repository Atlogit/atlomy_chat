/** @type {import('next').NextConfig} */
module.exports = {
  // Disable any experimental features
  experimental: {},
  
  // Configure rewrites to proxy API requests to the FastAPI backend
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8081';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },

  // Add environment configuration for client-side access
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8081',
  },

  // Explicitly disable any potentially problematic optimizations
  swcMinify: false,
  
  // Minimal webpack configuration
  webpack: (config) => {
    return config;
  }
}
