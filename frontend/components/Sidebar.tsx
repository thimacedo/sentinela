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
    icon: BarChart3,
    badge: { text: 'LIVE', type: 'live' }
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
    icon: Globe,
    badge: { text: 'PRO', type: 'pro' }
  },
  { 
    id: 'relatorios', 
    label: 'RELATÓRIOS', 
    path: '/dossies',
    icon: FileText,
    badge: { text: 'PRO', type: 'pro' }
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
                  w-full flex items-center justify-between px-3 py-2.5
                  font-medium text-sm transition-all duration-200 rounded-md
                  ${isActive 
                    ? 'bg-brand-primary/10 text-brand-primary' 
                    : 'text-text-muted hover:bg-bg-card hover:text-text-main'
                  }
                `}
                title={item.label}
              >
                <div className="flex items-center gap-3 truncate">
                  <Icon size={18} className="flex-shrink-0" />
                  {!isCollapsed && (
                    <span className="truncate">{item.label}</span>
                  )}
                </div>
                {!isCollapsed && 'badge' in item && item.badge && (
                  <span className={`
                    text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider
                    ${(item.badge as any).type === 'live'
                      ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 animate-pulse'
                      : 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20'
                    }
                  `}>
                    {(item.badge as any).text}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Footer Info & Upgrade Widget */}
        {!isCollapsed && (
          <div className="p-4 border-t border-border-main bg-bg-card/30 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-primary/20 border border-brand-primary/30 flex items-center justify-center font-bold text-brand-primary text-xs">
                TM
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-text-main truncate">Thiago Macedo</p>
                <p className="text-[10px] font-medium text-brand-primary uppercase tracking-wider">Plano Gratuito</p>
              </div>
            </div>
            
            <button 
              onClick={() => router.push('/dossies')}
              className="w-full bg-gradient-to-r from-brand-primary to-blue-600 hover:from-brand-primary/95 hover:to-blue-600/95 text-white py-2 px-3 rounded-lg text-xs font-bold transition-all transform hover:-translate-y-0.5 active:translate-y-0 shadow-md shadow-brand-primary/10 text-center flex items-center justify-center gap-1.5 cursor-pointer border-0"
            >
              <span>★ UPGRADE PARA PRO</span>
            </button>
            
            <div className="flex items-center justify-between text-[9px] font-mono text-text-muted opacity-60 pt-2 border-t border-border-main/50">
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                <span>MONITOR ATIVO</span>
              </div>
              <span>v81.0</span>
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
