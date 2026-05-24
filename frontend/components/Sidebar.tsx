'use client'

import { useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { 
  LayoutDashboard, 
  Target, 
  AlertTriangle, 
  Network, 
  Users, 
  FileText,
  Search,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'

const menuItems = [
  { 
    id: 'panorama', 
    label: 'PANORAMA', 
    path: '/',
    icon: LayoutDashboard 
  },
  { 
    id: 'pericia', 
    label: 'PERÍCIA', 
    path: '/pericia',
    icon: Search 
  },
  { 
    id: 'alvos', 
    label: 'ALVOS', 
    path: '/alvos',
    icon: Target 
  },
  { 
    id: 'alertas', 
    label: 'ALERTAS', 
    path: '/alertas',
    icon: AlertTriangle 
  },
  { 
    id: 'rede', 
    label: 'REDE', 
    path: '/rede',
    icon: Network 
  },
  { 
    id: 'workers', 
    label: 'WORKERS', 
    path: '/workers',
    icon: Users 
  },
  { 
    id: 'dossies', 
    label: 'DOSSIÊS', 
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
          fixed left-0 top-0 h-screen bg-black border-r border-tactical-accent/20
          transition-all duration-300 ease-in-out z-50
          ${isCollapsed ? 'w-16' : 'w-64'}
        `}
      >
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-tactical-accent/20">
          {!isCollapsed && (
            <h1 className="text-tactical-accent font-bold text-xl tracking-wider">
              WAR ROOM
            </h1>
          )}
          <button
            onClick={toggleSidebar}
            className="text-tactical-accent hover:text-tactical-accent/70 transition-colors p-1"
            aria-label={isCollapsed ? 'Expandir menu' : 'Recolher menu'}
          >
            {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="mt-4 px-2">
          {menuItems.map((item) => {
            const isActive = pathname === item.path
            const Icon = item.icon
            
            return (
              <button
                key={item.id}
                onClick={() => router.push(item.path)}
                className={`
                  w-full flex items-center gap-3 px-3 py-3 mb-1
                  font-mono text-sm transition-all duration-200 rounded
                  border-l-2
                  ${isActive 
                    ? 'border-tactical-accent bg-tactical-accent/10 text-tactical-accent shadow-[0_0_10px_rgba(0,255,0,0.3)]' 
                    : 'border-transparent text-tactical-accent/50 hover:text-tactical-accent hover:bg-tactical-accent/5 hover:border-tactical-accent/30'
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
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-tactical-accent/20">
            <div className="space-y-1">
              <div className="text-[10px] font-mono text-tactical-accent/60">
                SISTEMA SENTINELA
              </div>
              <div className="text-[10px] font-mono text-tactical-accent/40">
                PASA v52.4
              </div>
              <div className="text-[9px] font-mono text-tactical-accent/30">
                CENTRAL DE COMANDO OPERACIONAL
              </div>
            </div>
            
            {/* Status Indicator */}
            <div className="mt-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-tactical-accent rounded-full animate-pulse" />
              <span className="text-[9px] font-mono text-tactical-accent/50">
                SISTEMA ATIVO
              </span>
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
