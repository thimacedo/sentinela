import React, { useState } from 'react';
import { ShieldAlert, Loader2, Zap } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { useRouter } from 'next/navigation';

interface UnlockOverlayProps {
  balance: number;
  onSuccess: () => void;
}

export default function UnlockOverlay({ balance, onSuccess }: UnlockOverlayProps) {
  const router = useRouter();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleUnlock = async () => {
    if (balance < 850) {
      alert("Aporte Insuficiente. Adquira mais Créditos de Inteligência (CI) para operar o Feed de Alertas em Tempo Real.");
      router.push('/planos');
      return;
    }

    const confirmUnlock = window.confirm("Monitorar a rede em tempo real exige uma carga massiva de processamento. Deseja investir 850 CI para liberar o feed por 24 horas?");
    if (!confirmUnlock) return;

    try {
      setIsProcessing(true);
      const userId = localStorage.getItem('sentinela_user_id');
      
      if (!userId) {
        alert("Sessão inválida. Faça login.");
        return;
      }

      const { data, error } = await supabase.rpc('process_stn_transaction', {
        p_user_id: userId,
        p_amount: -850,
        p_type: 'CONSUMPTION',
        p_session_id: null,
        p_metadata: { action: 'unlock_alerts' }
      });

      if (error) throw error;

      if (data === true) {
        onSuccess();
      } else {
        alert("Falha na transação. Saldo insuficiente.");
      }
    } catch (err) {
      console.error(err);
      alert("Erro ao processar transação.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-bg-card/30 backdrop-blur-[1px] mt-[80px]">
      <div className="bg-bg-main border border-red-500/20 rounded-2xl p-8 max-w-md text-center shadow-2xl flex flex-col items-center animate-in slide-in-from-bottom-4 duration-500">
        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-6">
          <ShieldAlert className="w-8 h-8 text-red-500" />
        </div>
        <h3 className="text-xl font-black text-text-main mb-2">Dados Defasados</h3>
        <p className="text-sm text-text-muted mb-8 leading-relaxed">
          Você está visualizando incidentes com 12 horas de atraso. Para reagir a crises rapidamente, libere o monitoramento em tempo real.
        </p>
        <button 
          onClick={handleUnlock}
          disabled={isProcessing}
          className="w-full py-4 rounded-xl bg-red-600 text-white font-black uppercase tracking-widest text-[10px] hover:bg-red-700 transition-all shadow-lg shadow-red-500/20 flex items-center justify-center gap-2"
        >
          {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4 fill-white" />}
          Liberar Feed em Tempo Real (850 CI)
        </button>
      </div>
    </div>
  );
}
