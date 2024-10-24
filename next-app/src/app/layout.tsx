import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Ancient Medical Texts Analysis',
  description: 'Analysis and management of ancient medical texts',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" data-theme="light">
      <body className="min-h-screen bg-base-200">
        <div className="container mx-auto p-4">
          {children}
        </div>
      </body>
    </html>
  )
}
