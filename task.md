# Checklist de Correções operacionais e Relatórios (v83.6)

- `[x]` Mitigar os 13 alertas de erros operacionais no `core/instagram_scraper_v2.py`:
  - `[x]` Adicionar verificação contínua de `page.is_closed()` nos loops de posts.
  - `[x]` Implementar `try-except` com timeout de clique explícito de 10s em `open_post_modal`.
  - `[x]` Evitar screenshots redundantes e chamadas em páginas ou browsers já fechados.
  - `[x]` Validar a compilação do scraper e rodar testes de integridade localmente.
- `[x]` Refinar a experiência e integração dos Relatórios Comerciais:
  - `[x]` Exportar interface `Report` no Next.js `/relatorios/page.tsx` para suporte TypeScript.
  - `[x]` Integrar o componente `BuyButton` em `ReportCard.tsx`.
  - `[x]` Criar visualizador de markdown `/relatorios/visualizar` compatível com exportação estática Next.js.
  - `[x]` Viabilizar exportação a PDF client-side integrada através de `window.print()` estilizado.
  - `[x]` Resolver erro de tipagem no componente global do AdSense (`AdSenseSlot.tsx`) para sucesso no build.
  - `[x]` Configurar exportação estática (`force-static` e mock 200 no GET) na API route para passar na compilação SSG.
- `[x]` Validar build do frontend em produção (`npm run build`) -> Build concluído com sucesso.
- `[x]` Registrar descobertas técnicas e status atualizado em `STATE.md`.
- `[x]` Realizar commit e push imediato no branch ativo.
