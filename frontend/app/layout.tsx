import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from '@/components/ui/sonner'
import QueryProvider from '@/components/QueryProvider'

export const metadata: Metadata = {
  title: 'SkillSync AI — Smart Resume Agent',
  description: 'AI-powered resume tailoring and job matching',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          {children}
          <Toaster 
            theme="dark" 
            toastOptions={{
              style: {
                background: '#0F1629',
                border: '1px solid rgba(255,255,255,0.08)',
                color: '#fff'
              }
            }}
          />
        </QueryProvider>
      </body>
    </html>
  )
}