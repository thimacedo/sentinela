# Plano de Implementação — Importação de Prioridades Customizadas do CSV (v50.14)

## Descrição do Objetivo
Atualizar a prioridade dos alvos na tabela `fila_coleta` do banco de dados remoto Supabase com base nos valores numéricos definidos pelo operador no arquivo `prioridade_alvos.csv`, forçando o status `"PENDENTE"` em todos os registros para reativar o ciclo completo de raspagem.

## Alterações Propostas

### Scratch

#### [NEW] [update_priorities_from_csv.py](file:///c:/projetos/sentinela/scratch/update_priorities_from_csv.py)
- Script Python temporário para ler o CSV editado pelo operador, extrair a prioridade numérica por `candidato_id` e efetuar o upsert em lote na tabela `fila_coleta` forçando o status `"PENDENTE"`.

---

## Plano de Verificação

### Verificação Estática e Banco
- Executar o script no interpretador Python e verificar o sucesso do carregamento no terminal.
- Validar se a prioridade foi alterada para os candidatos editados (ex: `gabrielcesarrn` prioridade `3`, `baleia.rossi` prioridade `4`, etc.).
