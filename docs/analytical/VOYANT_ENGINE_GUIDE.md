# 📘 MANUAL TÉCNICO: MOTOR LÉXICO DETERMINÍSTICO & SUBAGENTE VOYANT (v92.3)
**Agente:** SaVoyant (sa-voyant-01)
**Engine:** Voyant Tools (Trombone API)
**Codinome:** Forensic Linguist Bridge
**Status:** OPERACIONAL

---

## 1. Visão Geral
O Voyant Tools evoluiu de um microserviço de triagem para um **Subagente autônomo (SaVoyant)**. Ele não apenas descarta lotes neutros, mas agora atua como um analista pericial que cruza estatísticas léxicas (TF-IDF, N-gramas) com as regras de ouro da **Bíblia Linguística Forense PASA**.

---

## 2. Inteligência e Raciocínio (SaVoyant)
O subagente opera sob o loop de recompensas do Orchestrator e utiliza as seguintes bases de conhecimento:
- **BIBLIA_LINGUISTICA_FORENSE_PASA.md**: Regras para detecção de sarcasmo, ironia e falsos alertas de violência.
- **Monitoramento de Ódio e Violência.md**: Matrizes de monitoramento de extremismo e milícias digitais.
- **HOSTILE_LEXICON**: Dicionário proprietário de ~50 termos gatilhos para violência, xenofobia e ataques institucionais.

### 2.1 Fluxo de Trabalho (Ciclo)
1. **Extração Léxica**: Consulta o Trombone para obter TF-IDF e frequências relativas do lote.
2. **Filtragem Rápida (Fast-Drop)**: Se a agressividade léxica for < 8%, o lote é processado localmente como `NEUTRO`.
3. **Análise de Insight**: Se houver picos de interesse, o SaVoyant cruza os dados com a Bíblia Linguística e gera um `linguistic_insight` no banco de dados.

---

## 3. Arquitetura de Dados
Os resultados e insights são persistidos na tabela `system_events` com o tipo `linguistic_insight`.

**Exemplo de Metadados de Insight:**
```json
{
    "titulo": "Alerta de Xenofobia Regionalizada",
    "resumo": "Detectado pico de termos discriminatórios contra nordestinos em contexto eleitoral.",
    "severidade": 85,
    "categoria_mca": "ODIO_IDENTITARIO",
    "relevancia": 0.95
}
```

---

## 4. Integração no Dashboard
- **Ciclos do Sistema**: Agora exibe o total de ciclos reais processados pelos workers ativos.
- **KPIs de IA**: Mostra o status real do VoyantServer (porta 8888).
- **Gestão de Chaves**: Permite excluir e desativar provedores de IA de forma segura.

---

## 5. Manutenção e SRE
O VoyantServer deve ser iniciado manualmente ou via script de boot:
```powershell
java -Djava.awt.headless=true -Xmx1024m -jar tools/voyant/VoyantServer.jar headless=true
```

### 5.1 Recompensas (XP)
- **Ciclo de Triagem**: +5.0 XP.
- **Geração de Insight Crítico**: +15.0 XP.

---
_Sentinela Intelligence Governance — v92.3_