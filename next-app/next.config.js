/** @type {import('next').NextConfig} */
module.exports = {
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

  // Explicitly configure compiler options
  compiler: {
    // Remove Babel configuration and use SWC
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Optional: Configure webpack if needed
  webpack: (config) => {
    return config;
  }
}
