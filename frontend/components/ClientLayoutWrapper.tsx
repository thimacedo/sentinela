'use client'

import Sidebar from '@/components/Sidebar'
import Providers from "@/components/Providers"

export default function ClientLayoutWrapper({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-main">
      {/* Sidebar - Pushes content automatically in flex */}
      <Sidebar />
      
      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Top subtle gradient or header placeholder if needed */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-brand-primary/5 via-transparent to-transparent pointer-events-none" />
        
        {/* Scrollable content container */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 md:p-10 relative z-10">
          <Providers>
            {children}
          </Providers>
        </div>
      </main>
    </div>
  )
}
