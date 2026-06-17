import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import ClientLayoutWrapper from '@/components/ClientLayoutWrapper'
import Script from 'next/script'
import { JsonLd } from '@/components/JsonLd'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sentinela | Observatório de Discurso Cívico',
  description: 'Transparência em tempo real sobre padrões de discurso de ódio e violência em redes sociais de candidatos e políticos brasileiros.',
  other: {
    'google-adsense-account': 'ca-pub-1827611269042960'
  }
}

const websiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Sentinela Democrática",
  "url": "https://sentinelademocratica.com.br",
  "description": "Observatório em tempo real de discurso cívico, ódio e violência nas redes sociais da política brasileira.",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://sentinelademocratica.com.br/alvos?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
};

const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Sentinela Democrática",
  "url": "https://sentinelademocratica.com.br",
  "logo": "https://sentinelademocratica.com.br/logo.png",
  "sameAs": [
    "https://twitter.com/sentinelabr",
    "https://www.linkedin.com/company/sentinelademocratica"
  ]
};

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
        <JsonLd data={websiteSchema} />
        <JsonLd data={organizationSchema} />
        <Script 
          src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${process.env.NEXT_PUBLIC_ADSENSE_ID || 'ca-pub-1827611269042960'}`} 
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
