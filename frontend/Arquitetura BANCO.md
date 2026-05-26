Arquitetura do redesign (opção 1): Timeline/Highlights baseados em public.alertas_ativos
Como você escolheu a opção 1, o frontend vai alimentar:

Stats/Header com contagens agregadas
HighlightCards (“histórias”) a partir de alertas do período
EventTimeline a partir de alertas ordenados por tempo
Isso evita calcular “picos” a partir de texto e reduz custo/complexidade.

Esquemas do banco (tabelas envolvidas)
1) public.alertas_ativos
Usada para:

“Atividade de Alertas (24h/48h)”
“Destaques do dia”
Timeline (eventos)
Campos relevantes:

created_at (timestamptz)
tipo (text)
severidade (text)
mensagem (text)
metadados (jsonb) (opcional para montar topWords/palavras-chave se existir)
lido (boolean)
organization_id (uuid) (multi-tenant)
2) public.candidatos
Usada para:

“Monit. Ativos/Alvos”
Perfil do candidato (bio/partido etc.) quando o usuário clica num card/detalhe
Campos relevantes (exemplos):

username
nome_completo, bio, partido, cargo, estado
status_monitoramento
posts_avaliados_count, comentarios_totais_count, comentarios_odio_count (se você quiser usar como “contas envolvidas”)
3) public.comentarios (opcional)
Na opção 1, não é obrigatória para Timeline/Highlights. Você só usa se quiser complementar stats “posts analisados” com base real.

Campos relevantes:

data_coleta
is_hate
candidato_id
4) public.metricas_diarias (opcional)
Usada se o header/insight quiser “índice de resiliência” já agregado por dia.

Endpoints sugeridos (camada de API/Edge Function)
Mesmo que você chame direto via Supabase client, na prática é melhor criar 3 endpoints para manter o frontend simples e padronizar filtros por tenant:

GET /api/dashboard/stats?period=24h|48h
GET /api/dashboard/highlights?period=24h
GET /api/dashboard/timeline?period=24h|7d|30d&limit=...
Abaixo estão as consultas SQL que esses endpoints devem executar.

1) NewsHeader (stats)
1.1 Total de alertas no período (todayAlerts / “Atividade de Alertas”)
Parâmetro: :period_hours (ex.: 24 ou 48)

SELECT COUNT(*)::int AS alerts_count
FROM public.alertas_ativos a
WHERE a.created_at >= NOW() - (make_interval(hours => :period_hours))
  AND (:organization_id::uuid IS NULL OR a.organization_id = :organization_id);
Se o seu UI for “Atividade de Alertas (48h)” e a copy mencionar “pulsos”, você pode também criar a variante de “não lidos”.

1.2 Alertas não lidos (se o texto “SEM PULSOS…” depender de lido=false)
SELECT COUNT(*)::int AS unread_alerts_count
FROM public.alertas_ativos a
WHERE a.created_at >= NOW() - (make_interval(hours => :period_hours))
  AND COALESCE(a.lido, false) = false
  AND (:organization_id::uuid IS NULL OR a.organization_id = :organization_id);
1.3 “Candidatos monitorados / Alvos ativos”
SELECT COUNT(*)::int AS candidates_monitored
FROM public.candidatos c
WHERE c.status_monitoramento = 'ATIVO'
  AND (:organization_id::uuid IS NULL OR c.organization_id = :organization_id);
1.4 “Volume analisado / novos posts” (opcional, já que a opção 1 usa alertas)
Se você ainda quiser mostrar volume real por janela (24h):

SELECT COUNT(*)::int AS volume_analisado
FROM public.comentarios cm
WHERE cm.data_coleta >= NOW() - (make_interval(hours => :period_hours))
  AND (:organization_id::uuid IS NULL OR cm.organization_id = :organization_id);
1.5 “Índice de Resiliência” (opcional, vem de metricas_diarias)
SELECT COALESCE(md.resiliencia, 0)::numeric AS indice_resiliencia
FROM public.metricas_diarias md
ORDER BY md.data DESC
LIMIT 1;
2) HighlightCards (destaques/jornalístico) — baseado em alertas
2.1 Carregar “histórias” (top N) do período
Você pode mapear:

title = derivado de tipo + severidade
summary = mensagem
severity = severidade
timestamp = created_at
alertCount = quantidade de alertas semelhantes (mesmo tipo+severidade) ou 1
Consulta recomendada: agrupar por “tipo+severidade+métrica textual” quando fizer sentido.

Versão simples (cada alerta vira um card)
SELECT
  a.id,
  a.created_at AS timestamp,
  a.tipo,
  a.severidade,
  a.mensagem,
  a.metadados,
  a.lido
FROM public.alertas_ativos a
WHERE a.created_at >= NOW() - (make_interval(hours => :period_hours))
  AND (:organization_id::uuid IS NULL OR a.organization_id = :organization_id)
ORDER BY a.created_at DESC
LIMIT :limit;
Versão “card por cluster” (melhor para narrativa: 1 card = N alertas)
Cluster por tipo e severidade e (opcionalmente) por “mensagem normalizada”.

WITH clustered AS (
  SELECT
    a.tipo,
    a.severidade,
    a.mensagem,
    COUNT(*)::int AS alert_count,
    MAX(a.created_at) AS last_event_at
  FROM public.alertas_ativos a
  WHERE a.created_at >= NOW() - (make_interval(hours => :period_hours))
    AND (:organization_id::uuid IS NULL OR a.organization_id = :organization_id)
  GROUP BY a.tipo, a.severidade, a.mensagem
)
SELECT
  tipo,
  severidade,
  mensagem,
  alert_count,
  last_event_at
FROM clustered
ORDER BY last_event_at DESC, alert_count DESC
LIMIT :limit;
TopWords: na opção 1, você só consegue trazer palavras-chave de verdade se elas estiverem em alertas_ativos.metadados (ex.: metadados->'topWords'). Se existir, você pode extrair via SQL (exemplo abaixo).

(Opcional) Extrair palavras-chave de metadados
Se metadados guarda algo como: {"topWords":["ódio","violência"]}:

SELECT
  a.id,
  a.created_at AS timestamp,
  a.severidade,
  a.tipo,
  a.mensagem,
  COALESCE(
    (a.metadados -> 'topWords')::text[],
    ARRAY[]::text[]
  ) AS top_words
FROM public.alertas_ativos a
WHERE a.created_at >= NOW() - (make_interval(hours => :period_hours))
  AND (:organization_id::uuid IS NULL OR a.organization_id = :organization_id)
ORDER BY a.created_at DESC
LIMIT :limit;
3) EventTimeline — linha do tempo a partir de alertas_ativos
3.1 Timeline (24h/7d/30d) com ordenação
SELECT
  a.created_at AS event_time,
  a.tipo,
  a.severidade,
  a.mensagem,
  a.lido,
  a.metadados
FROM public.alertas_ativos a
WHERE a.created_at >= NOW() - (make_interval(hours => :period_hours))
  AND (:organization_id::uuid IS NULL OR a.organization_id = :organization_id)
ORDER BY a.created_at ASC
LIMIT :limit;
Se você quer “timeline sempre completa sem perder performance”, sugiro paginação por cursor:

WHERE a.created_at > :cursor (ou < dependendo do sentido)
ORDER BY created_at ASC/DESC
LIMIT :page_size
4) CandidateProfile (na opção 1, como relacionar alertas a candidatos?)
Importante (limitação da sua opção 1)
Hoje public.alertas_ativos não tem candidato_id/candidato_username como coluna dedicada.

Então, para o CandidateProfile funcionar “quando clico em um destaque”, você tem 2 cenários:

Se os alertas guardam o alvo no metadados (ex.: {"candidato":"joao-silva"}), então dá pra extrair e buscar em public.candidatos.
Caso contrário, o profile do candidato vira genérico/indisponível a partir do destaque de alertas.
4.1 Buscar candidato por username (quando você tiver o username)
SELECT
  c.username,
  c.nome_completo,
  c.bio,
  c.cargo,
  c.partido,
  c.estado,
  c.status_monitoramento,
  c.posts_avaliados_count,
  c.comentarios_totais_count,
  c.comentarios_odio_count,
  c.updated_at,
  c.last_scraped_at
FROM public.candidatos c
WHERE c.username = :candidate_username
  AND (:organization_id::uuid IS NULL OR c.organization_id = :organization_id)
LIMIT 1;
4.2 Alertas recentes do candidato (se desejar detalhar)
Sem coluna de relacionamento direta em alertas_ativos, novamente só funciona via metadados ou outra tabela que associe.

Se metadados tiver candidato_id:

SELECT
  a.id,
  a.created_at,
  a.tipo,
  a.severidade,
  a.mensagem,
  a.lido,
  a.metadados
FROM public.alertas_ativos a
WHERE a.created_at >= NOW() - INTERVAL '30 days'
  AND (a.metadados ->> 'candidato' = :candidate_username)
  AND (:organization_id::uuid IS NULL OR a.organization_id = :organization_id)
ORDER BY a.created_at DESC
LIMIT :limit;
5) Esquema mínimo necessário (se você quiser melhorar a precisão)
Com a opção 1, você não é obrigado a criar tabelas. Porém, para deixar o produto consistente e evitar “profile sem candidato”, recomendo uma extensão do esquema (opcional):

public.alertas_ativos (ideal)
adicionar coluna candidato_username text NULL
e/ou candidato_id normalizado
Se você não quer DDL agora, então padronize:

que alertas_ativos.metadados sempre carregue candidato_username quando aplicável
6) Boas práticas SQL (para endpoints rápidos)
sempre filtrar por organization_id (multi-tenant)
usar índices em alertas_ativos(created_at) e possivelmente alertas_ativos(organization_id, created_at)
limitar LIMIT :limit
preferir ordenação consistente (ASC/DESC) para timeline