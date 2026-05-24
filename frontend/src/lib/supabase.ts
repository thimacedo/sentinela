import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Diagnóstico em tempo de execução no console do navegador
if (typeof window !== 'undefined') {
    console.log('📡 [SENTINELA] Configurando Supabase Client...');
    console.log('🔗 URL:', supabaseUrl ? 'OK (definida)' : '❌ AUSENTE');
    console.log('🔑 KEY:', supabaseAnonKey ? 'OK (definida)' : '❌ AUSENTE');
}

// Fallback para evitar erro durante o build/prerendering no Vercel
export const supabase = createClient(
    supabaseUrl || 'https://placeholder-project.supabase.co', 
    supabaseAnonKey || 'placeholder-key'
);
