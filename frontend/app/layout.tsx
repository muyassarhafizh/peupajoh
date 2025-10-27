import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import './globals.css'
import { Navigation } from '@/components/navigation'

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'peupajoh.ai',
  description: 'PeuPajoh.ai - AI-powered chatbot as your nutritionist',
  generator: 'peupajoh.ai',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans antialiased`}>
        <Navigation />
        {children}
      </body>
    </html>
  )
}
