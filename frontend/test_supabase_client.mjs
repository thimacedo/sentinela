import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

// Carrega as variáveis do .env.local local
const envPath = path.resolve('.env.local');
const envConfig = dotenv.parse(fs.readFileSync(envPath));
for (const k in envConfig) {
  process.env[k] = envConfig[k];
}

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

console.log("Supabase URL:", supabaseUrl);
console.log("Supabase Anon Key Preview:", supabaseAnonKey ? supabaseAnonKey.substring(0, 15) + "..." : "undefined");

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function run() {
  // 1. Total de monitorados
  const { count: monitorados, error: errMon } = await supabase
    .from('candidatos')
    .select('*', { count: 'exact', head: true })
    .eq('status_monitoramento', 'Ativo');
  console.log("Candidatos ativos count:", monitorados, "Error:", errMon);

  // 2. Volume analisado
  const { count: total_amostra, error: errAmostra } = await supabase
    .from('comentarios')
    .select('*', { count: 'exact', head: true });
  console.log("Volume analisado count:", total_amostra, "Error:", errAmostra);

  // 3. Indícios detectados
  const { count: total_alertas, error: errAlertas } = await supabase
    .from('comentarios')
    .select('*', { count: 'exact', head: true })
    .eq('is_hate', true);
  console.log("Indícios detectados count:", total_alertas, "Error:", errAlertas);

  // 4. Teste de listagem da série temporal
  const windowDate = new Date();
  windowDate.setHours(windowDate.getHours() - 48);
  const windowStr = windowDate.toISOString();
  console.log("Window timestamp:", windowStr);

  const { data: comments, error: errComments } = await supabase
    .from('comentarios')
    .select('data_coleta')
    .eq('is_hate', true)
    .gte('data_coleta', windowStr)
    .order('data_coleta', { ascending: true });

  console.log("Comments returned:", comments ? comments.length : 0, "Error:", errComments);
  if (comments && comments.length > 0) {
    console.log("Amostra comentarios:", comments.slice(0, 5));
  }
}

run().catch(console.error);
