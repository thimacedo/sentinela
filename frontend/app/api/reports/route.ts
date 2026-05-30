import { createClient } from '@supabase/supabase-js';
/* eslint-disable @typescript-eslint/no-unused-vars */
import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

export const dynamic = 'force-static';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL as string;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;
const supabase = createClient(supabaseUrl, supabaseKey);

const reportsDir = path.join(process.cwd(), 'public', 'reports');

export async function GET() {
  try {
    // Garante que o diretório exista em tempo de build/execução
    await fs.mkdir(reportsDir, { recursive: true });
    const files = await fs.readdir(reportsDir);
    const reports = files.map((file) => {
      const ext = path.extname(file).substring(1);
      return {
        name: file,
        type: ext,
        url: `/reports/${file}`,
      };
    });
    return NextResponse.json({ reports });
  } catch (error) {
    // Retorna lista vazia com status 200 para evitar quebras no build estático SSG
    return NextResponse.json({ reports: [], error: 'Failed to list reports or directory empty' });
  }
}

export async function POST(request: Request) {
  const { reportName, userId } = await request.json();
  if (!reportName || !userId) {
    return NextResponse.json({ error: 'Missing parameters' }, { status: 400 });
  }

  // 1. Catraca de Cobrança: Deduz 350 CIs do saldo do usuário antes de liberar
  const { data: rpcData, error: rpcError } = await supabase.rpc('process_ci_transaction', {
    p_user_id: userId,
    p_amount: -350,
    p_type: 'CONSUMPTION',
    p_description: `Emissão de Dossiê: ${reportName}`
  });

  if (rpcError || (rpcData && rpcData.success === false)) {
    return NextResponse.json(
      { error: rpcError?.message || rpcData?.message || 'Saldo de CIs insuficiente para emitir o Dossiê.' },
      { status: 402 } // 402 Payment Required
    );
  }

  // 2. Registra compra na tabela "purchases"
  const { data, error } = await supabase.from('purchases').insert({
    user_id: userId,
    report_name: reportName,
    purchased_at: new Date().toISOString(),
  });
  if (error) {
    // Como os CIs já foram descontados, o ideal seria estornar ou logar falha, mas para V1 deixamos o log:
    console.error("[Billing Error] Falha ao registrar purchase no ledger:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  // URL assinada para download direto (bucket público)
  const { data: urlData, error: urlError } = await supabase.storage
    .from('reports')
    .createSignedUrl(reportName, 60 * 60);
  if (urlError) {
    return NextResponse.json({ error: urlError.message }, { status: 500 });
  }
  return NextResponse.json({ downloadUrl: urlData?.signedUrl });
}
