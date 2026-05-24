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
          flex flex-col h-screen bg-slate-950 border-r border-slate-800
          transition-all duration-300 ease-in-out z-50
          ${isCollapsed ? 'w-16' : 'w-64'}
        `}
      >
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          {!isCollapsed && (
            <h1 className="text-emerald-500 font-bold text-lg tracking-tighter">
              SENTINELA<span className="text-slate-500 font-light ml-1">AI</span>
            </h1>
          )}
          <button
            onClick={toggleSidebar}
            className="text-slate-400 hover:text-emerald-500 transition-colors p-1"
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
                    ? 'bg-emerald-500/10 text-emerald-500' 
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
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
          <div className="p-4 border-t border-slate-800 bg-slate-950/50">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                Sistema Ativo
              </span>
            </div>
            <div className="text-[9px] font-mono text-slate-600">
              PASA v54.0 // CORE OPS
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
