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
        <script async custom-element="amp-auto-ads" src="https://cdn.ampproject.org/v0/amp-auto-ads-0.1.js"></script>
      </head>
      <body className={`${inter.className} antialiased bg-bg-main text-text-main`}>
        <div dangerouslySetInnerHTML={{ __html: '<amp-auto-ads type="adsense" data-ad-client="ca-pub-1827611269042960"></amp-auto-ads>' }} />
        <Script 
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1827611269042960" 
          strategy="afterInteractive"
          crossOrigin="anonymous" 
        />
        <ClientLayoutWrapper>
          {children}
        </ClientLayoutWrapper>
      </body>
    </html>
  )
}
