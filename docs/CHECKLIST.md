# Sentinela - Checklist de Implantacao

## Pre-Deploy
- [ ] Segredo do Stripe girado em producao
- [ ] Backup do banco de dados realizado
- [ ] Ambiente de staging configurado
- [ ] Acesso ao Supabase verificado
- [ ] PR #4 revisado e aprovado

## Deploy
- [ ] Migracoes executadas no Supabase
- [ ] Indices criados (8 indices)
- [ ] Funcoes RPC criadas (2 funcoes)
- [ ] Code checkout na branch fix/security-types-queries
- [ ] Dependencias instaladas (npm install, pip install)
- [ ] Build executado com sucesso (npm run build)
- [ ] Lint executado sem erros (npm run lint)
- [ ] Testes em staging passam

## Pos-Deploy
- [ ] Deploy para producao realizado
- [ ] Aplicacao funcionando normalmente
- [ ] Performance monitorada
- [ ] Logs verificados para erros
- [ ] Time notificado das mudancas

## Verificacoes de Seguranca
- [ ] price.env deletado do repositorio
- [ ] .gitignore atualizado com padroes de .env
- [ ] SQL Injection corrigida em queue_manager.py
- [ ] Nenhum arquivo de credencial no repositorio
- [ ] Code review de seguranca realizado

## Verificacoes Tecnicas
- [ ] Tipos TypeScript centralizados criados
- [ ] Todos os any types removidos do page.tsx
- [ ] Compilacao TypeScript sem erros
- [ ] Otimizacao N+1 query implementada
- [ ] Batch inserts funcionando

## Monitoramento
- [ ] Queries por operacao monitoradas
- [ ] Tempo de resposta monitorado
- [ ] Uso de recursos do Supabase monitorado
- [ ] Erros e warnings monitorados
- [ ] Performance comparada com baseline

---

## Comando Rapido para Verificar Status

### Seguranca
git ls-files | grep price.env
grep -E "^\*\.env|^price\.env" .gitignore
grep -n "f\"last_scraped_at" core/queue_manager.py

### Tecnico
npm run build
npm run lint

### Banco de Dados
SELECT indexname FROM pg_indexes WHERE tablename IN ('fila_coleta', 'candidatos')