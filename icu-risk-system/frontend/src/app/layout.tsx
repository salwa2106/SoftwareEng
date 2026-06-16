import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/Navbar'

export const metadata: Metadata = {
  title: 'ICU Risk Prediction System',
  description: 'Academic demonstration of ICU patient risk monitoring. NOT for clinical use.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="min-h-screen">
          {children}
        </main>
        <footer className="bg-white border-t border-gray-200 mt-12 py-6">
          <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
            <p className="font-medium text-red-600">
              FOR ACADEMIC DEMONSTRATION ONLY. NOT FOR CLINICAL USE.
            </p>
            <p className="mt-1">
              This system uses synthetic/sample data. Risk scores are rule-based and not clinically validated.
            </p>
          </div>
        </footer>
      </body>
    </html>
  )
}
