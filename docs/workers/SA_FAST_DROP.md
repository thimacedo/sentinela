# 🕵️ Subagente: SaFastDrop (Pré-triagem Léxica Local)
**Versão:** PASA v97.6 | **Status:** Ativo em Produção
**Diretório:** `workers/ai/sa_fast_drop.py`
**Mecanismo Interno:** `core/lexical_filter.py` (Python puro)

---

## 1. Missão e Objetivo

O **SaFastDrop** é o subagente especialista em limpeza léxica e pré-triagem determinística do Sentinela. Ele foi projetado na versão `v96.2` para substituir integralmente o subagente legado `SaVoyant` e o servidor Java `VoyantServer.jar`, eliminando o overhead de memória da JVM.

Sua missão é atuar como um **funil de custos de IA**, identificando e descartando comentários inúteis antes que eles alcancem a malha de classificação cloud do `WkClassificaComentarios`:
1.  **Redução de Burn Rate**: Filtra comentários de baixa qualidade léxica (emojis, caracteres especiais repetidos, ruídos de renderização) localmente e com custo zero de tokens.
2.  **Mitigação de Spam/Shadowban**: Identifica mensagens com padrões de spam político coordenado, propagandas de bets, correntes e autopromoção, impedindo que estes poluam o dashboard do operador.
3.  **Processamento Rápido**: Capaz de processar centenas de comentários por segundo devido à sua natureza determinística de strings locais.

---

## 2. Lógica Operacional e Algoritmos

O subagente realiza varreduras em lote de comentários não classificados (`processado_ia = false`) e aplica dois filtros lógicos principais importados de `core/lexical_filter.py`:

```
   [Comentários Não Processados]
                 ↓
      ┌────────────────────┐
      │ is_junk(texto)?    │ ── (Sim) ──➔ Marca como [LIXO] (processado_ia = true)
      └────────────────────┘
                 ↓ (Não)
      ┌────────────────────┐
      │ should_shadowban?  │ ── (Sim) ──➔ Marca como [LIXO] / Spam (processado_ia = true)
      └────────────────────┘
                 ↓ (Não)
      [Mantém processado_ia = false] ──➔ Enviado para [WkClassificaComentarios] (LLM)
```

### 2.1 Detecção de Lixo (`is_junk`)
Descarta de forma determinística comentários com conteúdo vazio ou sem valor semântico. Exemplos:
*   Comentários contendo apenas emojis.
*   Repetições excessivas de uma mesma letra ou pontuação.
*   Mensagens contendo apenas marcações de perfis (`@usuario`) sem texto adicional.

### 2.2 Shadowban Léxico (`should_shadowban`)
Detecta spam de links, golpes de investimento ("plataformas de bet", "robô do pix"), propagandas não autorizadas e xingamentos/ofensas genéricas de baixíssimo calão que não merecem processamento linguístico aprofundado na nuvem.

---

## 3. Integração com Banco de Dados (Supabase)

Ao identificar um comentário como lixo ou spam, o SaFastDrop atualiza o registro no banco remoto do Supabase com os seguintes metadados:
*   `processado_ia` = `true`
*   `categoria_ia` = `"LIXO"`
*   `confianca_ia` = `1.0`
*   `analise_pericial` = `"[SaFastDrop] Descartado por baixa qualidade léxica (lixo)."` ou `"[SaFastDrop] Ocultado por detecção de spam/shadowban."`

Os comentários que **passam** ilesos pelos filtros continuam marcados como `processado_ia = false` para serem classificados posteriormente pelos modelos analíticos.

---

## 4. Configurações e Parâmetros

*   **Tamanho do Lote (`_BATCH_SIZE`)**: `200` comentários por ciclo.
*   **Velocidade Média**: < 0.2s por lote (Python puro sem I/O de rede ou GPU).
*   **Concorrência**: Registrado no orquestrador principal e executado continuamente em background no `main_runner.py`.

---

## 5. Resiliência e Monitoramento

*   **Sem Falhas Críticas**: Sendo um subagente em Python local puro, o SaFastDrop não possui dependências de rede, chaves de API externas ou servidores externos. Ele nunca entra em hibernação por falta de cota ou rede.
*   **Logs**:
    *   Exibe no console o número de comentários descartados por ciclo.
    *   Registra estatísticas de sucesso e volumetria na tabela `worker_metrics`.
