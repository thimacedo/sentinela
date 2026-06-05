# Protocolo de Metodologia Linguística Analítica (Método Vichi-Sentinela)
**Versão:** 1.0.0
**Referência:** Leonardo Perin Vichi (UFRN) & PASA v16.3
**Escopo:** Normalização, Extração de N-Gramas e Análise de Assinatura Lexical

## 1. Objetivo
Padronizar a extração de métricas estatísticas de texto para apoiar a análise analítica de IA. Este método permite identificar a coordenação de ataques (Astroturfing) e a criação de "impressões digitais" linguísticas de grupos extremistas.

## 2. Padrão de Normalização de Dados (Norm-V)
Antes de qualquer análise (IA ou Estatística), o texto deve passar pela função de normalização baseada em SpaCy (pt_core_news_lg):

- **Remoção Obrigatória:** Stopwords, pontuação, espaços excessivos e números (opcional, dependendo do contexto eleitoral).
- **Lematização:** Ativar USE_LEMMA = True para agrupar variações da mesma palavra (ex: "matar", "matando", "matou" -> "matar").
- **Filtragem POS (Part-of-Speech):** Extração focada em **VERB**, **NOUN** e **ADJ**. Adjetivos são os principais portadores de carga ofensiva no discurso de ódio.

## 3. Extração de Assinaturas (N-Gramas Analíticos)
Todos os workers de coleta e processamento devem gerar n-gramas para identificar padrões de repetição:

- **Bigramas (N=2):** Identificação de alvos e adjetivos recorrentes (ex: "político lixo").
- **Trigramas (N=3):** Identificação de slogans de campanha de ódio ou instruções de ataques (ex: "vamos quebrar tudo").
- **Fronteira de Sentença:** A extração de n-gramas **NUNCA** deve cruzar a fronteira de um ponto final ou interrogação, para manter a coesão sintática.

## 4. Detecção de Coordenação (Limiares Estatísticos)
O sistema sinaliza um **Ataque Coordenado** quando os seguintes limiares são atingidos:

| Métrica | Condição de Alerta | Ação do Sistema |
| :--- | :--- | :--- |
| **Densidade Lexical** | Repetição de >5 bigramas idênticos entre perfis distintos. | Marcação como "Suspeita de Bot". |
| **Sincronia de N-Gramas** | Trigramas idênticos em janelas < 300 segundos. | Elevação para "Risco Crítico". |
| **Frequência de Adjetivos** | Concentração de >40% de adjetivos de carga semântica no lote. | Ativação do Worker de Inteligência Profunda. |

## 5. Fluxo de Trabalho Integrado
1. **Worker de Coleta:** Extrai texto bruto.
2. **Worker Vichi (Metodologia):** Aplica Normalização e gera N-Gramas + POS Tags.
3. **Worker de Inteligência (IA):** Recebe o texto limpo + as estatísticas de repetição.
4. **Agente de Relatório:** Utiliza as nuvens de palavras e frequências para embasamento analítico.

## 6. Interface de Comunicação entre Agentes
Ao solicitar uma análise baseada neste método, utilize a estrutura:
`json
{
  "metodo": "VICHI_SENTINELA",
  "analise": ["NGRAMS", "POS_TAGS"],
  "threshold": "HIGH_SENSITIVITY",
  "data_scope": "LAST_24H"
}
`

---
*Este documento é a base de integridade para a extração de indícios no projeto Sentinela Democrática.*
