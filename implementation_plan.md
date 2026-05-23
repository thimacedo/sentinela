# Plano de Implementação — Geração de Fila de Coleta e CSV de Prioridades (v50.13)

## Descrição do Objetivo
Colocar todos os 338 candidatos atualmente cadastrados como "Ativo" com o status "PENDENTE" na tabela de fila do banco remoto (`fila_coleta`), e gerar um arquivo local `prioridade_alvos.csv` na raiz do projeto para que o operador possa editar as prioridades dos alvos de forma manual e devolvê-lo.

## Alterações Propostas

### Scratch

#### [NEW] [prepare_priority_csv.py](file:///c:/projetos/sentinela/scratch/prepare_priority_csv.py)
- Script Python temporário para buscar candidatos monitorados no Supabase, inseri-los na tabela `fila_coleta` com prioridade padrão `1` e exportar o CSV contendo os dados do candidato e o status.

---

## Plano de Verificação

### Verificação Estática e Banco
- Rodar o script e confirmar que o arquivo `prioridade_alvos.csv` foi gerado e preenchido na pasta raiz `c:\projetos\sentinela\`.
- Validar se a fila do banco possui todos os novos registros em status pendente.
