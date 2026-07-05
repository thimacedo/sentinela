# Sentinela - Guia de Implantacao

## Passos de Implantacao

### 1. URGENTE - Girar Segredo Stripe
- Acesse Stripe Dashboard > Webhooks
- Encontre webhook com segredo exposto
- Clique Roll secret e atualize em producao
- Verifique que antigo segredo nao funciona mais

### 2. Aplicar Migracoes Banco de Dados
- Acesse Supabase Dashboard > SQL Editor
- Execute o arquivo migrations/add_performance_indexes.sql
- Verifique indices criados com SELECT indexname FROM pg_indexes

### 3. Testar em Staging
- git checkout fix/security-types-queries
- npm install
- npm run build
- npm run lint

### 4. Deploy para Producao
- Revise PR #4 no GitHub
- Aprove e merge para main
- Deploy automático ou manual

### 5. Monitorar Performance
- Supabase Dashboard para query performance
- Grafana/Prometheus para métricas
- Logs da aplicação para erros

## Checklist

### Urgente
- [ ] Segredo do Stripe girado em producao
- [ ] Arquivo price.env deletado do repositorio

### Alta Prioridade
- [ ] Migracoes de banco executadas
- [ ] Indices criados no Supabase
- [ ] Funcoes RPC criadas

### Media Prioridade
- [ ] Testes em staging passam
- [ ] Deploy para producao realizado
- [ ] Performance monitorada

## Solucao de Problemas

### Erro de Conexao com Supabase
Teste conexao manualmente com supabase client

### Erro de Sintaxe SQL
Verifique se indices foram criados corretamente

### Performance nao melhorou
Analise queries com EXPLAIN ANALYZE

## Contatos e Referencias
- Autor: Thiago Macedo
- Repositorio: https://github.com/thimacedo/sentinela
- PR: https://github.com/thimacedo/sentinela/pull/4