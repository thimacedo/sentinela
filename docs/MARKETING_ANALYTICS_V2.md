# Plano Diretor: Inteligência Visual e Marketing (v2.0)
_Gatilhos de Venda e Panorama Analítico_

Este documento especifica a estratégia de visualização de dados do Sentinela, com foco em conversão, percepção de valor e antecipação de crises políticas.

## 1. Filosofia
Não mostramos apenas dados; nós vendemos a **interpretação do perigo**. Gráficos devem evocar urgência (para vendas individuais) ou autoridade (para planos corporativos).

## 2. Gráficos Individuais (Gatilhos de Urgência)
Utilizados nos dashboards de alvos específicos e na capa dos Dossiês (PDF).

| Gráfico | Tipo | Propósito | Gatilho Psicológico |
| :--- | :--- | :--- | :--- |
| **Velocidade de Infecção** | Fluxograma / Área | Mostrar a rapidez com que ataques se espalham. | **Prova de Coordenação (Bots)** |
| **Termômetro Jurídico** | Gauge (0-100) | Medir a densidade de "Rigor Criminal". | **Medo Jurídico / Calúnia** |
| **Mapa de Vulnerabilidade** | Treemap / Barras | Destacar qual pilar da imagem está sendo atacado. | **Direcionamento Tático** |

## 3. Gráficos Gerais (Panorama do Corpus)
Utilizados no "War Room" global e para clientes Tier Corporativo.

| Gráfico | Tipo | Propósito | Gatilho Psicológico |
| :--- | :--- | :--- | :--- |
| **Resiliência Democrática** | Heatmap Geográfico | Mostrar concentração de hostilidade por Estado. | **Autoridade Nacional** |
| **O Iceberg** | Barras Sobrepostas | Comparar comentários visíveis vs. "Ódio Velado" detectado pela IA. | **Exclusividade da Ferramenta** |
| **Correlação Partidária** | Dispersão (Bolhas) | Benchmark de ataques entre partidos. | **Competição / Proteção** |

## 4. Gráficos de ROI e Caixa (Tesouraria)

| Gráfico | Tipo | Propósito | Gatilho Psicológico |
| :--- | :--- | :--- | :--- |
| **Economia Tática** | Donut | Custo Humano vs. Custo Sentinela (CI). | **Retorno sobre Investimento** |
| **Burn Rate de Munição** | Linha (Step) | Histórico de consumo de Créditos de Inteligência (CI). | **Prevenção / Recarga** |

## 5. Implementação no Motor de Dossiês (PDF)
O `ReportGenerator` (`processing/report_generator.py`) será atualizado para incluir representações visuais nativas (via primitivas de desenho do PDF ou geração de imagens), transformando o relatório de texto em uma peça executiva visualmente irrefutável. As adições incluem:
1.  **Barra de Risco Jurídico:** Indicador visual de severidade criminal logo na primeira página.
2.  **Distribuição de Vulnerabilidade:** Blocos coloridos representando as categorias do MCA v2.2.
3.  **Selo de Economia Forense:** Um bloco indicando quantas horas humanas foram poupadas pela IA.

---
_Status: Em Implementação (v86.1)_