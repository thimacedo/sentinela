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
    <div className="space-y-6">
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
