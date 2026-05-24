import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Fallback para evitar erro durante o build/prerendering no Vercel
// As variáveis REAIS devem ser configuradas no painel do Vercel.
export const supabase = createClient(
    supabaseUrl || 'https://placeholder-project.supabase.co', 
    supabaseAnonKey || 'placeholder-key'
);
