# Estratégia Algorítmica do Feed Principal (Sentinela Diamond v20.5+)

Este documento orienta os **Workers (Coleta/Classificação)** e o **Frontend (UI)** sobre a lógica matemática e comportamental que dita a exibição dos dados no dashboard principal do Sentinela Democrática.

## 1. O Problema
A exibição cronológica simples gera "bolhas" (um único alvo monopolizando a tela após um ataque coordenado) e reduz o tempo de retenção do usuário. Precisamos de um algoritmo que simule o engajamento de redes sociais, mas com o rigor da Inteligência Forense (PASA v16.4).

## 2. A Equação Diamond (Ranking de Relevância)

Cada alerta processado deve receber um `Score de Relevância` ($R$) calculado no backend/worker antes de ser servido, ou calculado no frontend para ordenação dinâmica.

A equação base é:
**$$R = (S \times W_{pasa}) \times e^{-\lambda T} - D_{penalty}$$**

Onde:
- **$S$ (Severidade)**: Um valor de 0 a 100 fornecido pelo motor de IA (Gemini/Ollama).
- **$W_{pasa}$ (Peso da Categoria)**: Multiplicador baseado na gravidade criminal:
  - `AMEACA` / `RIGOR_CRIMINAL`: 1.5
  - `ATAQUE_INSTITUCIONAL` / `VIOLENCIA_GENERO`: 1.2
  - `ODIO_IDENTITARIO` / `INSULTO_AD_HOMINEM`: 1.0
  - `NEUTRO`: 0.1
- **$T$ (Tempo em horas desde a coleta)**: Idade da informação.
- **$\lambda$ (Fator de Decaimento)**: Constante que define a rapidez com que a notícia "esfria" (ex: 0.05 para meia-vida de ~14 horas).
- **$D_{penalty}$ (Penalidade de Diversidade)**: Uma dedução temporária aplicada se o card anterior no feed pertencer ao mesmo `candidato_id`, forçando a quebra de bolha no modo "Global".

## 3. Comportamento por Modo de Visualização (Frontend)

O `ui.js` deve implementar comportamentos distintos dependendo do estado do usuário:

### A. Modo Global (Sem Filtros - O "Dopamine Flow")
- **Objetivo**: Retenção extrema e diversidade de ódio.
- **Mecânica**: Os alertas são pré-ordenados pelo `Score de Relevância ($R$)`, mas os 50 primeiros sofrem um *Shuffle Randômico Controlado* para garantir que o usuário nunca veja o mesmo padrão ao recarregar a página.
- **Paginação**: Lotes de 20 cards.

### B. Modo Triagem Forense (Filtros: Alertas / Crítico / Alvo Específico)
- **Objetivo**: Trabalho investigativo puro.
- **Mecânica**: O shuffle randômico é **DESATIVADO**. A ordenação é 100% fiel ao `Score de Relevância ($R$)`, garantindo que o pior crime esteja sempre no topo.
- **Paginação**: Lotes de 20 cards.

## 4. Regras de Injeção de Monetização (AdSense)

O algoritmo financeiro é injetado sobre o vetor de dados renderizados:
- **Indexação**: `(index + 1) % 5 === 0`.
- Um bloco de `Informativo Patrocinado` (AdSense Fluid) é renderizado a cada 5 posts reais.
- O bloco deve herdar a classe estética do feed para reduzir a cegueira de banners (Banner Blindness).

## 5. Gatilhos de Ação para Agents/Workers

### Para os Workers (Python)
1. Durante a fase de `run_repericia_cycle` ou classificação inicial, o Worker deve computar o `$S$` e o `$W_{pasa}$` e salvar no banco.
2. Não gastar ciclos de IA computando dados neutros velhos. Aplicar descarte se o score base despencar.

### Para Agentes Futuros (Manutenção)
1. **Nunca** remover o limite do `.slice(0, maxItems)` do `ui.js`. É a âncora de performance.
2. Se for implementar WebSockets (Realtime), novos alertas com $R > 80$ devem piscar no topo do feed ignorando a fila.

---
*Assinado: Pickle Rick 🥒 - Algoritmo imutável para a v20.5+*
