# Sugestões de Refatoração para o Frontend (Next.js)

## Observações Gerais
- O código está funcional, mas pode ser melhorado em termos de manutenção, legibilidade e reaproveitamento.
- Alguns arquivos contêm muita lógica e JSX misturado, dificultando a leitura.
- Uso de tipos `any` em vários locais reduz a segurança de tipos do TypeScript.
- Cores, labels e constantes estão definidas dentro dos componentes, dificultando reutilização.
- Alguns componentes são grandes e poderiam ser divididos em partes menores.

## Arquivo Principal: `src/app/page.tsx`
### Pontos de Atenção
1. **Componente monolítico**  
   - A página `Home` contém toda a lógica de carregamento, estado e renderização de abas.  
   - Sugestão: Extrair cada aba (War Room, Forensic Analysis, etc.) para componentes separados já é feito, mas a lógica de loading e estado ainda está na página. Considerar mover a busca de dados para um custom hook ou usar React Query/SWR para melhor gerenciamento de estado e cache.

2. **Uso de `any` em `DashboardData`**  
   - Os campos `comentarios`, `candidatos`, `dossies`, `alerts`, `workerRuns` são do tipo `any`.  
   - Sugestão: Definir interfaces ou tipos específicos para esses arrays com base nos modelos do Prisma (ex: `Comentario`, `Candidato`, etc.) e importar de `@/types` ou gerar a partir do schema.

3. **Efeito de seed automático**  
   - O efeito que verifica se `data.stats.totalComent === 0` e chama `seedData()` pode causar múltiplas chamadas se o dados forem limpos durante a execução.  
   - Sugestão: Adicionar um estado de `hasSeeded` ou usar uma flag no localStorage para evitar re‑seed desnecessário.

4. **Evento global `openCommentDetail`**  
   - O uso de `window.addEventListener` para comunicação entre abas funciona, mas pode ser substituído por um estado global (Context API ou Zustand) para melhor integração com React.

## Componentes de Gráficos e KPI (`src/components/sentinela/WarRoom.tsx`)
### Pontos de Atenção
1. **Componente `KPICard` interno**  
   - Embora seja um bom exemplo de composição, está definido dentro do arquivo. Se for usado apenas aqui, está ok; mas caso seja necessário em outras páginas, mover para `components/ui/kpi-card.tsx`.

2. **Repetição de lógica de gráficos**  
   - Cada gráfico (linha, barra, pizza) tem muita configuração repetida (estilos, tooltips, containers).  
   - Sugestão: Criar componentes reutilizáveis como `LineChartWrapper`, `BarChartWrapper`, `PieChartWrapper` que recebam `data`, `config` e devolvam o `<ResponsiveContainer>`.

3. **Estilos inline e objetos de estilo**  
   - Muitos atributos `style={{ ... }}` são usados para cores e dimensões.  
   - Sugestão: Sempre que possível, usar classes Tailwind ou variáveis CSS (ex: `--chart-color-1`) para facilitar tema e ajustes.

4. **Formatação de números e porcentagens**  
   - Funções `fmt` e `pct` são úteis, mas estão definidas dentro do componente.  
   - Sugestão: Mover para um arquivo de utils (`utils/formatters.ts`) e exportar.

5. **Uso de arrays mutáveis diretamente na render**  
   - Filtros como `candidatos.filter(...)` e `comentarios.filter(...)` são executados a cada render.  
   - Sugestão: Memoizar com `useMemo` baseado nas dependências relevantes (`candidatos`, `comentarios`).

6. **Tipos de props**  
   - A prop `data` do `WarRoom` é do tipo `DashboardData` (mesmo da página), que contém `any`.  
   - Sugestão: Definir tipos mais específicos para cada seção (ex: `WarRoomData`) ou usar os mesmos tipos refinados.

## Arquivos de API (`src/app/api/*/route.ts`)
### Pontos de Atenção
1. **Lógica de negócio nas rotas**  
   - As rotas contém agregações e processamento de dados diretamente.  
   - Sugestão: Extrair para uma camada de serviço (ex: `services/dashboardService.ts`) que contenha funções como `getDashboardData()`, `getTimeline()`, etc., tornando as rotas apenas responsáveis por chamar o serviço e tratar erros.

2. **Uso de `any` na resposta**  
   - Embora o retorno seja `Response.json(...)`, o tipo interno não é explicitado.  
   - Sugestão: Definir uma interface `DashboardResponse` que corresponda ao objeto retornado e usar em `Response.json<DashboardResponse>(data)`.

3. **Consultas potencialmente pesadas**  
   - Alguns `take: 2000` ou `take: 500` podem trazer muitos dados se o banco crescer.  
   - Sugestão: Paginar ou agregar diretamente no banco (already doing aggregation in memory, could be done via Prisma aggregation groupBy).

4. **Falta de tratamento de parcial falhas**  
   - Se uma das consultas falhar, todo o endpoint retorna 500.  
   - Sugestão: Tentar buscar o máximo possível e retornar dados parciais com avisos, ou usar transações quando apropriado.

## Recomendações de Arquitetura
- **Camada de serviço**: Separar lógica de acesso a dados e regras de negócio das camadas de controle (API) e apresentação (components).
- **Gerenciamento de estado global**: Considerar usar Zustand ou Jotai para estados que precisam ser compartilhados entre abas (como dados do dashboard, filtros selecionados).
- **Tipagem forte**: Eliminar `any` gradualmente, gerando tipos a partir do schema Prisma usando ferramentas como `prisma-zod-generator` ou criando interfaces manualmente.
- **Componentização**: Dividir componentes grandes em unidades menores e reutilizáveis (KPI cards, gráficos, tabelas).
- **Performance**: Utilizar `useMemo`, `useCallback` e lazy loading onde houver listas grandes ou cálculos custosos.

## Próximos Passos
- Avaliar a aplicação dessas sugestões em sprints futuras, começando pelos pontos de maior impacto (tipos, extração de serviços, componentização de gráficos).
- Manter o estilo atual (Tailwind, framer-motion, shadcn/ui) para consistência visual.

---
*Este documento contém apenas sugestões. Nenhuma alteração foi aplicada ao código-fonte neste momento.*