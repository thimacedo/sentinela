import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import ClientLayoutWrapper from '@/components/ClientLayoutWrapper'
import Script from 'next/script'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sentinela | Observatório de Discurso Cívico',
  description: 'Transparência em tempo real sobre padrões de discurso de ódio e violência em redes sociais de candidatos e políticos brasileiros.',
  other: {
    'google-adsense-account': 'ca-pub-1827611269042960'
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <head>
        <meta httpEquiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <meta httpEquiv="Pragma" content="no-cache" />
        <meta httpEquiv="Expires" content="0" />
      </head>
      <body className={`${inter.className} antialiased bg-bg-main text-text-main`}>
        {process.env.NEXT_PUBLIC_ADSENSE_ID && (
          <Script 
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${process.env.NEXT_PUBLIC_ADSENSE_ID}`} 
            strategy="lazyOnload"
            crossOrigin="anonymous" 
          />
        )}
        <ClientLayoutWrapper>
          {children}
        </ClientLayoutWrapper>
      </body>
    </html>
  )
}
