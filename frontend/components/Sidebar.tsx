'use client'

import { usePathname, useRouter } from 'next/navigation'
import { 
  Home, 
  Users, 
  ShieldAlert, 
  Globe, 
  FileText,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Activity
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
    path: '/analise',
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
    path: '/relatorios',
    icon: FileText
  },
  {
    id: 'financeiro',
    label: 'GOD MODE',
    path: '/admin/financeiro',
    icon: Activity
  },
]

import { useUIStore } from '@/src/store/useUIStore'
import { useWallet } from '@/hooks/useWallet'
import { useDashboardStats } from '@/hooks/useDashboardData'

export default function Sidebar() {
  const { isCollapsed, setIsCollapsed, toggleSidebar } = useUIStore()
  const { balance, loading: walletLoading } = useWallet()
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
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

        {/* Footer Info & Global KPIs */}
        {!isCollapsed && (
          <div className="p-4 border-t border-border-main bg-bg-card/50 overflow-y-auto custom-scrollbar">
            {/* Wallet Balance */}
            <div className="mb-4 bg-bg-main border border-border-main rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest flex items-center gap-1">
                  Aporte Tático
                </span>
                {walletLoading ? (
                  <span className="w-10 h-4 bg-border-main rounded animate-pulse"></span>
                ) : (
                  <span className={`text-xs font-black font-mono ${balance > 0 ? 'text-brand-primary' : 'text-red-500'}`}>
                    ⚡ {balance.toLocaleString('pt-BR')} CI
                  </span>
                )}
              </div>
              <div className="w-full bg-border-main rounded-full h-1 mb-3 overflow-hidden">
                <div className={`h-1 transition-all duration-1000 ${balance > 0 ? 'bg-brand-primary' : 'bg-red-500'}`} style={{ width: balance > 0 ? '100%' : '10%' }}></div>
              </div>
              <button 
                onClick={() => router.push('/planos')}
                className={`w-full py-1.5 rounded text-[10px] font-black uppercase tracking-widest transition-all border ${
                  balance === 0 
                    ? 'bg-red-500/10 text-red-500 border-red-500/20 hover:bg-red-500 hover:text-white' 
                    : 'bg-brand-primary/10 text-brand-primary border-brand-primary/20 hover:bg-brand-primary hover:text-white'
                }`}
              >
                {balance === 0 ? 'Restaurar Aporte' : 'Aumentar Aporte'}
              </button>
            </div>

            {/* Indicator Ativo */}
            <div className="flex items-center gap-2 mb-6">
              <div className="w-2 h-2 bg-brand-primary rounded-full animate-pulse" />
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest">
                Monitor Ativo
              </span>
            </div>

            {/* Global KPIs (Movi do Topo para cá) */}
            <div className="space-y-4 mb-6 pt-4 border-t border-border-main/30">
                <div className="flex flex-col">
                    <span className="text-[9px] font-bold text-text-muted uppercase tracking-tighter mb-1">Alertas (24h)</span>
                    <span className="text-lg font-black text-text-main font-mono leading-none tracking-tighter">
                        {statsLoading ? '...' : (stats?.total_alertas || 0).toLocaleString('pt-BR')}
                    </span>
                </div>
                <div className="flex flex-col">
                    <span className="text-[9px] font-bold text-text-muted uppercase tracking-tighter mb-1">Monitorados</span>
                    <span className="text-lg font-black text-text-main font-mono leading-none tracking-tighter">
                        {statsLoading ? '...' : (stats?.total_monitorados || 0)}
                    </span>
                </div>
                <div className="flex flex-col">
                    <span className="text-[9px] font-bold text-text-muted uppercase tracking-tighter mb-1">Amostragem</span>
                    <span className="text-lg font-black text-text-main font-mono leading-none tracking-tighter">
                        {statsLoading ? '...' : `${((stats?.total_amostra || 0) / 1000).toFixed(1)}k`}
                    </span>
                </div>
                
                {/* Resiliência */}
                <div className="mt-4 p-3 bg-brand-primary/5 border border-brand-primary/20 rounded-lg">
                    <div className="flex justify-between items-center mb-1.5">
                        <span className="text-[9px] font-bold text-brand-primary uppercase">Resiliência</span>
                        <span className="text-xs font-black text-brand-primary font-mono">{stats?.resiliencia || 0}%</span>
                    </div>
                    <div className="w-full bg-brand-primary/20 rounded-full h-1 overflow-hidden">
                        <div 
                            className="bg-brand-primary h-1 transition-all duration-1000" 
                            style={{ width: `${stats?.resiliencia || 0}%` }}
                        />
                    </div>
                </div>
            </div>

            <div className="text-[9px] font-mono text-text-muted opacity-50 text-center border-t border-border-main/30 pt-4">
              OBSERVATÓRIO CÍVICO
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
