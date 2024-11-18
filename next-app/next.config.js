/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static exports if needed
  // output: 'export',
  
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

  // Remove deprecated swcMinify option
  // Use SWC for compilation by default in Next.js 15+
  
  // Optional: Configure webpack if needed
  webpack: (config) => {
    return config;
  }
}

module.exports = nextConfig
