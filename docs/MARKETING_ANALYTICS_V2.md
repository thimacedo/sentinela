# Plano Diretor: Inteligência Visual Estratégica (Foco no Cliente v2.1)
_Gráficos como Produtos de Inteligência e Gatilhos de Venda_

Este documento especifica a estratégia de visualização de dados do Sentinela voltada **exclusivamente para o cliente final** (Gestores de Campanha, Agências, Políticos e Departamentos Jurídicos). 

## 1. Filosofia de Produto
Para o cliente, gráficos de economia de tokens são irrelevantes. O que importa é a **compreensão do campo de batalha**. Nossos gráficos devem responder a três dores primárias:
1. "Estou sofrendo um ataque natural ou orquestrado?" (Autenticidade)
2. "Qual o impacto real desse ataque na minha imagem?" (Dano)
3. "Tenho material legal para derrubar essas contas?" (Jurídico)

## 2. Gráficos de Venda: "Threat Intelligence" (Para Dossiês e Painel do Cliente)

### A. O Termômetro de Organização (Dispersão Temporal / Scatter)
*   **Aparência:** Bolhas de comentários ao longo de uma linha do tempo (eixo X) agrupadas por autor ou categoria (eixo Y).
*   **O que Mostra:** Picos irreais de hostilidade em curtíssimo espaço de tempo.
*   **O Gatilho:** **Prova de Orquestração.** Visualmente prova ao cliente que "100 comentários em 3 minutos" não é orgânico. Vende a necessidade de derrubar a rede.

### B. Matriz de Contágio Narrativo (Sankey / Fluxo)
*   **Aparência:** Fluxo que liga um "Tema" (ex: Voto Impresso) -> "Alvo" -> "Categoria de Ataque" (Rigor Criminal).
*   **O que Mostra:** Como uma narrativa específica se transforma em um tipo de ataque.
*   **O Gatilho:** **Direcionamento Tático.** "Seus adversários estão usando a pauta X para acusá-lo de crime Y." Permite que a equipe de RP responda na mesma moeda.

### C. A "Impressão Digital" do Ataque (Radar Chart / Aranha)
*   **Aparência:** Gráfico poligonal (já implementado no TrendChart).
*   **O que Mostra:** O perfil do ataque segundo o Protocolo MCA v2.2.
*   **O Gatilho:** **Avaliação de Dano.** Mostra se o ataque tenta destruir a "Honra" (Ad Hominem) ou o "Mandato" (Institucional).

### D. Mapa de Risco Jurídico (Funil de Evidências / Pyramid)
*   **Aparência:** Uma pirâmide invertida. Topo: Total de Comentários. Meio: Ódio. Base: Imputações Criminais Claras.
*   **O que Mostra:** O "suco" da coleta. O que realmente pode virar processo.
*   **O Gatilho:** **Gatilho Jurídico.** É o gráfico que o advogado do candidato quer ver. "Filtramos 50.000 mensagens inúteis e entregamos as 45 perfeitas para um processo de Calúnia."

## 3. O Panorama Global (Para a Página "/alvos" e Visão Geral)

### A. Mapa Termal Geográfico (Brasil)
*   **Aparência:** Mapa do Brasil colorizado por temperatura de hostilidade.
*   **O que Mostra:** Se os ataques contra o candidato X em SP estão, na verdade, vindo de IPs/Contas baseadas no RJ (Indicativo de milícia digital importada).

### B. O Hub de Ameaças (Grafo de Nós / React Force Graph)
*   **Aparência:** Constelação de nós interligados. Alvos no centro, atacantes em órbita.
*   **O que Mostra:** A detecção do `NetworkMiner`.
*   **O Gatilho:** Mostra que contas idênticas atacam o candidato A e o candidato B, provando uma rede de mercenários.

## 4. Remoção do "Ruído Interno"
Gráficos de "Economia de Horas", "Custo do Servidor" ou "Burn Rate" devem ser restritos estritamente ao painel **`/admin`** (acesso God Mode), pois não agregam valor à narrativa política do cliente.

## 5. Próxima Etapa de Implementação
1. Modificar o PDF do `ReportGenerator` para substituir o selo de "Economia Forense" pela **"Matriz de Risco Jurídico"**.
2. Criar os endpoints específicos para alimentar o **Grafo de Nós** e a **Dispersão Temporal**.