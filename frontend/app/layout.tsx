import type { Metadata } from 'next'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { Navbar } from '@/components/Navbar'
import { Footer } from '@/components/Footer'
import { AnimationInit } from '@/components/AnimationInit'

export const metadata: Metadata = {
  title: 'AIPFL-IDS | AI Powered Federated Learning IDS',
  description: 'AI Powered Federated Learning Intrusion Detection System for Secure IoT Networks',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" />
      </head>
      <body>
        <ThemeProvider>
          <Navbar />
          <main>
            <AnimationInit>{children}</AnimationInit>
          </main>
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  )
}
