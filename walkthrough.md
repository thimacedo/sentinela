# Walkthrough — Inteligência Governança, Furtividade e Controle Financeiro (v86.0)

Esta atualização marca a transição do Sentinela de um sistema de monitoramento para uma **Plataforma de Governança de Inteligência**. Foram implementadas camadas de furtividade profunda, triagem local de IA, detecção de redes coordenadas e controle financeiro atômico.

## Alterações Realizadas

### 1. Governança Financeira & CI (v86.1)
- **Implementação do `TreasurerWorker`**: Um novo worker dedicado à integridade financeira e auditoria de saldos.
- **Transição STN ➔ CI**: O sistema agora utiliza semanticamente **Créditos de Inteligência (CI)** em vez de STN.
- **DRE Diário**: Fechamento automático de caixa (Inflow vs Outflow) gerado a cada 24h.
- **Auditoria de Saldos**: Varredura automática para detectar anomalias ou discrepâncias entre o histórico de transações e o saldo atual do perfil.
- **Catraca de Consumo**: Cobrança obrigatória de **350 CI** por Dossiê Gerado e **500 CI** por Injeção de Alvo, validada via RPC atômica.

### 2. Inteligência Híbrida & Transparência (v85.11)
- **Triagem Local com Ollama**: Integração do Ollama como primeira camada de análise. Dados neutros/lixo são filtrados localmente sem custo de API externa.
- **Parecer Técnico IA**: Inclusão de um campo de justificativa técnica em cada comentário classificado, elevando a transparência forense.
- **Renderização Markdown**: Cards de análise agora suportam tabelas, listas e formatação rica para exibir dossiês e perícias complexas de forma legível.
- **Utility Tasks**: Workers aproveitam o tempo de ociosidade para re-analisar registros de baixa confiança (< 60%) e enriquecer metadados (bio/seguidores) de alvos estratégicos.

### 3. Furtividade Avançada (Stealth Mode v85.10)
- **Fingerprinting Dinâmico**: O scraper agora rotaciona identidades de dispositivos (Windows, macOS, iPhone, Android) e cabeçalhos HTTP (`Sec-Ch-Ua`) a cada ciclo.
- **Viewports Variáveis**: Removida a resolução fixa; o sistema agora simula telas de diversos tamanhos e densidades de pixel.
- **Simulação Humana**: Implementação de Jitter (atrasos aleatórios) e movimentos de mouse não-lineares para mitigar a detecção por algoritmos anti-bot do Instagram.

### 4. Analytics & Redes (v85.13)
- **NetworkMinerWorker**: Ativação da detecção de clusters coordenados utilizando NetworkX.
- **Mapeamento de Clusters**: Identificação automática de comunidades de ataque e contas "Multi-Target".
- **Grafos de Influência**: Alimentação da tabela `redes_coordenadas` para visualização estratégica no frontend.

### 5. Melhorias de UI e UX (v86.0)
- **Radar Grid 2-Colunas**: Refatoração da página de alvos para uma visualização compacta e comparativa.
- **Filtros Avançados**: Adicionada filtragem dinâmica por **Partido**, **Estado (UF)** e **Nível de Risco** em tempo real.
- **Sincronia de URL**: Implementado filtro via Query String (`?target=...`) na página de análise com suporte a redirecionamento automático a partir dos cards de alvos.

---

## Verificação e Resultados

1. **Dossiês Reais Ativos**: O `DossieService` gera agora PDFs reais com selo de integridade **SHA-256**. Testado e validado com cobrança de 350 CI por unidade.
2. **Triagem de Custo Zero**: O Ollama está processando ~55% dos comentários capturados, reduzindo drasticamente o burn rate de créditos Mistral/Groq.
3. **Estabilidade de Build**: Corrigidos erros críticos de compilação no Vercel relacionados ao hook `useState` e ao `Suspense boundary` necessário para o `useSearchParams`.
4. **Alvos VIP Priorizados**: Perfis estratégicos (Lula, Bolsonaro, Nikolas, Erika, Malafaia) foram promovidos a relevância 100.0 e aparecem fixados no topo do radar.
5. **Autopilot Reativado**: Corrigido o bug de "No Target" causado pela trava de validação de identidade. O sistema agora rotaciona todos os ~400 alvos ativos circularmente.
