'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

interface Dossie {
  id: string
  alvo: string
  data_geracao: string
  status: string
}

export default function DossiesPage() {
  const [dossies, setDossies] = useState<Dossie[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDossies()
  }, [])

  async function fetchDossies() {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await supabase
        .from('dossies')
        .select('*')
        .order('data_geracao', { ascending: false })

      if (error) throw error

      setDossies(data || [])
    } catch (err: any) {
      console.error('Erro ao buscar dossiês:', err)
      setError(err.message || 'Erro ao carregar dossiês')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <div className="text-tactical-accent/50 font-mono text-sm animate-pulse">
            RECUPERANDO ARQUIVOS CRIPTOGRAFADOS...
          </div>
          <div className="w-8 h-8 border-2 border-tactical-accent border-t-transparent rounded-full animate-spin mx-auto" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-500/10 border border-red-500/30 rounded p-4">
          <p className="text-red-500 font-mono text-sm">
            ERRO: {error}
          </p>
          <button
            onClick={fetchDossies}
            className="mt-4 px-4 py-2 bg-tactical-accent/10 hover:bg-tactical-accent/20 border border-tactical-accent rounded text-tactical-accent text-sm font-mono transition-colors"
          >
            TENTAR NOVAMENTE
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-10 opacity-60 pointer-events-none select-none">
      {/* Overlay de Congelamento */}
      <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-auto">
        <div className="bg-slate-900 border border-amber-500/50 p-6 rounded-lg shadow-2xl text-center space-y-4 max-w-md mx-4">
          <div className="w-12 h-12 bg-amber-500/20 text-amber-500 rounded-full flex items-center justify-center mx-auto animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path><path d="M5 3v4"></path><path d="M19 17v4"></path><path d="M3 5h4"></path><path d="M17 19h4"></path></svg>
          </div>
          <h2 className="text-xl font-bold text-white uppercase tracking-tight">Módulo em Manutenção</h2>
          <p className="text-slate-400 text-sm leading-relaxed">
            O motor de geração de dossiês forenses está sendo recalibrado para a nova arquitetura PASA v54. 
            Este recurso estará disponível em breve.
          </p>
        </div>
      </div>

      <div className="space-y-6 filter blur-sm">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-tactical-accent">
          DOSSIÊS FORENSES
        </h1>
        <div className="text-xs font-mono text-tactical-accent/40">
          RELATÓRIOS CONSOLIDADOS
        </div>
      </div>

      {/* Table */}
      <div className="border border-tactical-accent/20 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-tactical-accent/10 border-b border-tactical-accent/20">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-mono text-tactical-accent">
                ALVO
              </th>
              <th className="px-4 py-3 text-left text-xs font-mono text-tactical-accent">
                DATA DE GERAÇÃO
              </th>
              <th className="px-4 py-3 text-left text-xs font-mono text-tactical-accent">
                STATUS
              </th>
              <th className="px-4 py-3 text-left text-xs font-mono text-tactical-accent">
                AÇÃO
              </th>
            </tr>
          </thead>
          <tbody>
            {dossies.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center">
                  <p className="text-tactical-accent/50 font-mono text-sm">
                    NENHUM DOSSIÊ ENCONTRADO
                  </p>
                </td>
              </tr>
            ) : (
              dossies.map((dossie) => (
                <tr 
                  key={dossie.id}
                  className="border-b border-tactical-accent/10 hover:bg-tactical-accent/5 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-sm text-tactical-accent">
                    {dossie.alvo}
                  </td>
                  <td className="px-4 py-3 font-mono text-sm text-tactical-accent/70">
                    {new Date(dossie.data_geracao).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`
                      px-2 py-1 rounded text-xs font-mono
                      ${dossie.status === 'ATIVO' 
                        ? 'bg-green-500/20 text-green-500' 
                        : 'bg-yellow-500/20 text-yellow-500'
                      }
                    `}>
                      {dossie.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button className="text-tactical-accent hover:text-tactical-accent/70 text-xs font-mono transition-colors">
                      VISUALIZAR →
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
