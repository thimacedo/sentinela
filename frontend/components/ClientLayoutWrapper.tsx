'use client'

import { useUIStore } from '@/src/store/useUIStore'
import Sidebar from '@/components/Sidebar'
import Providers from "@/components/Providers"

export default function ClientLayoutWrapper({
  children,
}: {
  children: React.ReactNode
}) {
  const { isCollapsed } = useUIStore()

  return (
    <>
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <main className={`
        ${isCollapsed ? 'ml-16' : 'ml-64'}
        min-h-screen transition-all duration-300
      `}>
        <div className="p-8">
          <Providers>
            {children}
          </Providers>
        </div>
      </main>
    </>
  )
}
