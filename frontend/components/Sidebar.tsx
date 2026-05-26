'use client'

import { useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { 
  Home, 
  Users, 
  ShieldAlert, 
  Globe, 
  FileText,
  BarChart3,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

const menuItems = [
  { 
    id: 'inicio', 
    label: 'INÍCIO', 
    path: '/',
    icon: Home 
  },
  { 
    id: 'analise', 
    label: 'ANÁLISE', 
    path: '/pericia',
    icon: BarChart3 
  },
  { 
    id: 'candidatos', 
    label: 'CANDIDATOS', 
    path: '/alvos',
    icon: Users 
  },
  { 
    id: 'alertas', 
    label: 'ALERTAS', 
    path: '/alertas',
    icon: ShieldAlert 
  },
  { 
    id: 'tendencias', 
    label: 'TENDÊNCIAS', 
    path: '/rede',
    icon: Globe 
  },
  { 
    id: 'relatorios', 
    label: 'RELATÓRIOS', 
    path: '/dossies',
    icon: FileText 
  },
]

import { useUIStore } from '@/src/store/useUIStore'

export default function Sidebar() {
  const { isCollapsed, setIsCollapsed, toggleSidebar } = useUIStore()
  const pathname = usePathname()
  const router = useRouter()

  return (
    <>
      {/* Overlay para mobile */}
      {!isCollapsed && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsCollapsed(true)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`
          flex flex-col h-screen bg-bg-main border-r border-border-main
          transition-all duration-300 ease-in-out z-50
          ${isCollapsed ? 'w-16' : 'w-64'}
        `}
      >
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-border-main">
          {!isCollapsed && (
            <h1 className="text-brand-primary font-bold text-lg tracking-tighter">
              SENTINELA<span className="text-text-muted font-light ml-1">AI</span>
            </h1>
          )}
          <button
            onClick={toggleSidebar}
            className="text-text-muted hover:text-brand-primary transition-colors p-1"
            aria-label={isCollapsed ? 'Expandir menu' : 'Recolher menu'}
          >
            {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 mt-4 px-2 space-y-1">
          {menuItems.map((item) => {
            const isActive = pathname === item.path
            const Icon = item.icon
            
            return (
              <button
                key={item.id}
                onClick={() => router.push(item.path)}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5
                  font-medium text-sm transition-all duration-200 rounded-md
                  ${isActive 
                    ? 'bg-brand-primary/10 text-brand-primary' 
                    : 'text-text-muted hover:bg-bg-card hover:text-text-main'
                  }
                `}
                title={item.label}
              >
                <Icon size={18} className="flex-shrink-0" />
                {!isCollapsed && (
                  <span className="truncate">{item.label}</span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Footer Info */}
        {!isCollapsed && (
          <div className="p-4 border-t border-border-main bg-bg-card/50">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 bg-brand-primary rounded-full animate-pulse" />
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest">
                Monitor Ativo
              </span>
            </div>
            <div className="text-[9px] font-mono text-text-muted opacity-50">
              OBSERVATÓRIO CÍVICO
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
