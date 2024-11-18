/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React Strict Mode for additional checks and warnings
  reactStrictMode: true,
  
  // Optimize SWC minification
  swcMinify: true,
  
  // Output configuration for easier deployment
  output: 'standalone',
  
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

  // Webpack configuration to handle potential module resolution issues
  webpack: (config, { isServer }) => {
    // Add fallback for potential missing modules
    config.resolve.fallback = { 
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false
    };

    // Ignore unnecessary files during build
    config.ignoreWarnings = [
      /Failed to parse source map/,
      /Module not found/,
      /Can't resolve/
    ];

    return config;
  },

  // TypeScript configuration
  typescript: {
    ignoreBuildErrors: false
  },

  // Experimental features for performance and optimization
  experimental: {
    optimizePackageImports: ['react', 'react-dom'],
    serverComponentsExternalPackages: ['sharp']
  },

  // Logging configuration
  logging: {
    level: 'verbose'
  }
}

module.exports = nextConfig;
