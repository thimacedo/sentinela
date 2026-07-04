# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\final_audit.spec.ts >> AdSense and UI Refinement Final Verification
- Location: tests\final_audit.spec.ts:5:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: 'Tendências no Discurso Político Brasileiro' })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByRole('heading', { name: 'Tendências no Discurso Político Brasileiro' })

```

```yaml
- complementary:
  - heading "SENTINELAAI" [level=1]
  - button "Recolher menu"
  - navigation:
    - button "INÍCIO"
    - button "ANÁLISE"
    - button "ESTATÍSTICAS"
    - button "CANDIDATOS"
    - button "ALERTAS"
    - button "REDE"
    - button "RELATÓRIOS"
  - text: Aporte de Inteligência ⚡ 0 CI
  - button "Restaurar Aporte"
  - text: Monitor Ativo Alertas (24h) 3.646 Monitorados 339 Amostragem 64.1k Resiliência 94.3% OBSERVATÓRIO CÍVICO
- main:
  - main:
    - text: "Status: Monitoramento Ativo"
    - heading "Visão Tática Global" [level=1]
    - paragraph: Observatório de Discurso Cívico em tempo real. Padrões de comportamento anômalo e ações coordenadas detectadas via Protocolo PASA.
    - heading "📅 Linha do Tempo" [level=2]
    - button "24h"
    - button "7d"
    - button "30d"
    - paragraph: Histórico e picos de ocorrência em ordem cronológica (Últimas 24 Horas)
    - paragraph: 13:53
    - heading "CAMPANHA_COORDENADA" [level=4]
    - text: 1 posts
    - paragraph: 167razoesrn...
    - text: "Alvo:"
    - strong: "@allysonbezerra.rn"
    - text: "Risco Calculado:"
    - strong: 50%
    - paragraph: 08:08
    - heading "CAMPANHA_COORDENADA" [level=4]
    - text: 1 posts
    - paragraph: Parabéns meu irmão...
    - text: "Alvo:"
    - strong: "@carlosbrandaooficial"
    - text: "Risco Calculado:"
    - strong: 50%
    - paragraph: 08:08
    - heading "CAMPANHA_COORDENADA" [level=4]
    - text: 1 posts
    - paragraph: Parabéns!!!! Feliz aniversário amigo e irmão. Muitos anos de vida 🙌🙌....
    - text: "Alvo:"
    - strong: "@carlosbrandaooficial"
    - text: "Risco Calculado:"
    - strong: 50%
    - paragraph: 08:08
    - heading "CAMPANHA_COORDENADA" [level=4]
    - text: 1 posts
    - paragraph: Parabéns !!!! Meu amigo tudo de bom pra vc. Felicidades...
    - text: "Alvo:"
    - strong: "@carlosbrandaooficial"
    - text: "Risco Calculado:"
    - strong: 50%
    - paragraph: 08:08
    - heading "CAMPANHA_COORDENADA" [level=4]
    - text: 1 posts
    - paragraph: Parabéns 🎈👏🏼👏🏼👏🏼👏🏼 😍...
    - text: "Alvo:"
    - strong: "@carlosbrandaooficial"
    - text: "Risco Calculado:"
    - strong: 50%
    - heading "Pulso de Hostilidade" [level=2]
    - paragraph: Análise Quantitativa / Último Período
    - text: Live Monitor
    - application: 11h 16h
    - heading "Espectro de Ameaça" [level=2]
    - paragraph: Perfil Qualitativo / MCA v2.2
    - application: AMEACA INSULTO ATAQUE ODIO GENERO CRIME
    - text: 34.2% Densidade de Ódio Ativo Gatilho de Crise
    - heading "Termômetro Nacional" [level=2]
    - paragraph: Concentração de Hostilidade por Estado
    - text: MA alvos 9 SP alvos 2 RN alvos 1 Radar Geográfico
    - paragraph: Mapeamento em tempo real do epicentro dos ataques, permitindo mobilização jurídica e de RP direcionada por região.
    - heading "📰 Destaques Recentes" [level=2]
    - link "Ver tudo →":
      - /url: /alertas
    - article:
      - text: AL
      - paragraph: allysonbezerra.rn
      - paragraph: 04/07/2026, 13:53:28
      - text: Médio
      - heading "Discurso de ódio detectado" [level=3]
      - paragraph: 167razoesrn...
      - text: CAMPANHA_COORDENADA 1 Evento(s) Analisado(s)
      - link "Explorar Dados →":
        - /url: /analise
    - article:
      - text: CA
      - paragraph: carlosbrandaooficial
      - paragraph: 04/07/2026, 08:08:00
      - text: Médio
      - heading "Discurso de ódio detectado" [level=3]
      - paragraph: Parabéns!!!! Feliz aniversário amigo e irmão. Muitos anos de vida 🙌🙌....
      - text: CAMPANHA_COORDENADA 1 Evento(s) Analisado(s)
      - link "Explorar Dados →":
        - /url: /analise
    - article:
      - text: CA
      - paragraph: carlosbrandaooficial
      - paragraph: 04/07/2026, 08:08:00
      - text: Médio
      - heading "Discurso de ódio detectado" [level=3]
      - paragraph: Parabéns meu irmão...
      - text: CAMPANHA_COORDENADA 1 Evento(s) Analisado(s)
      - link "Explorar Dados →":
        - /url: /analise
    - article:
      - text: CA
      - paragraph: carlosbrandaooficial
      - paragraph: 04/07/2026, 08:08:00
      - text: Médio
      - heading "Discurso de ódio detectado" [level=3]
      - paragraph: Parabéns meu amigo Deus abençoe sua vida tudo de bom pra vc e sua família....
      - text: CAMPANHA_COORDENADA 1 Evento(s) Analisado(s)
      - link "Explorar Dados →":
        - /url: /analise
    - article:
      - text: CA
      - paragraph: carlosbrandaooficial
      - paragraph: 04/07/2026, 08:08:00
      - text: Médio
      - heading "Discurso de ódio detectado" [level=3]
      - paragraph: Parabéns meu ami, felicidades!!...
      - text: CAMPANHA_COORDENADA 1 Evento(s) Analisado(s)
      - link "Explorar Dados →":
        - /url: /analise
    - insertion:
      - iframe
    - text: 🔬
    - heading "Análises e Insights" [level=2]
    - heading "Padrão de Discurso" [level=3]
    - text: TENDÊNCIA
    - paragraph: Análise volumétrica da hostilidade detectada nos alvos ativos.
    - paragraph: Saúde do Discurso
    - paragraph: 94.3%
    - paragraph:
      - strong: "Insight Analítico:"
      - text: A tendência indica estabilidade com picos isolados de hostilidade ad hominem.
    - text: "CONFIANÇA: 94% FONTES: 64066 posts"
    - link "Explorar dados completos →":
      - /url: /analise
    - heading "Comportamento Coordenado" [level=3]
    - text: PADRÃO
    - paragraph: Detecção de mensagens idênticas ou altamente similares em massa.
    - paragraph:
      - strong: "Insight Analítico:"
      - text: Monitoramento Solenya v71.0 ativo. Buscando padrões de automação.
    - text: "CONFIANÇA: 88% FONTES: 64066 posts"
    - link "Explorar dados completos →":
      - /url: /analise
    - text: 👤
    - heading "Perfis em Destaque" [level=2]
    - paragraph: Use as setas para explorar →
    - paragraph: Carregando perfis...
    - heading "📖 Sobre Este Observatório" [level=3]
    - paragraph:
      - text: O
      - strong: Sentinela
      - text: monitora padrões de discurso em redes sociais para promover transparência e alimentar o debate democrático brasileiro.
    - paragraph: Nossa plataforma identifica tendências de ódio, hostilidade e desinformação, fornecendo dados técnicos para a sociedade civil e órgãos de controle.
    - heading "O Que Fazemos" [level=4]
    - list:
      - listitem: ✓ Coleta autônoma de posts públicos em redes sociais
      - listitem: ✓ Identificação de padrões de discurso de ódio e violência
      - listitem: ✓ Relatórios analíticos com classificação semântica MCA v2.2
      - listitem: ✓ Alertas em tempo real sobre picos anormais de hostilidade
    - heading "Limitações Importantes" [level=4]
    - list:
      - listitem: ⚠️ Não substitui análise humana — ferramenta de pesquisa
      - listitem: ⚠️ Baseado em posts públicos — não detecta contas privadas
      - listitem: ⚠️ Classificação por IA — sujeita a falsos positivos
      - listitem: ⚠️ Não visa julgamento político, apenas transparência de dados
    - heading "Metodologia Técnica" [level=4]
    - paragraph:
      - strong: "Coleta:"
      - text: Motores Playwright v2 / Zyte
    - paragraph:
      - strong: "Processamento:"
      - text: Análise semântica Híbrida (Mistral/Ollama)
    - paragraph:
      - strong: "Protocolo:"
      - text: PASA v70.4 — Critérios de Análise
    - paragraph:
      - strong: "Frequência:"
      - text: Ciclos de 24h com Autopilot L3
    - paragraph: 📚 Explore nossa documentação técnica para entender os algoritmos.
    - link "Documentação":
      - /url: /metodologia
    - link "Publicações":
      - /url: /dossies
    - insertion
    - text: 💎
    - heading "Inteligência Ilimitada" [level=3]
    - paragraph: Dossiês completos, análise de grafos de influência e relatórios em tempo real com validade técnica.
    - button "Adquirir Créditos de Inteligência"
    - paragraph: Opere na rede a partir de 1.000 CI
    - text: S
    - paragraph: SentinelaDemocrática
    - paragraph: Tecnologia de vigilância cívica para a transparência do processo democrático brasileiro.
    - link "Termos":
      - /url: /termos
    - link "Metodologia":
      - /url: /metodologia
    - link "LGPD":
      - /url: /lgpd
    - link "Privacidade":
      - /url: /privacidade
    - link "GitHub":
      - /url: https://github.com/THIAGO/sentinela
- alert
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const PRODUCTION_URL = 'https://asentinela.vercel.app';
  4  | 
  5  | test('AdSense and UI Refinement Final Verification', async ({ page }) => {
  6  |   await page.goto(PRODUCTION_URL);
  7  | 
  8  |   // 1. Verify Raw Script tag in HEAD
  9  |   const scriptSource = await page.innerHTML('head');
  10 |   expect(scriptSource).toContain('https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1827611269042960');
  11 | 
  12 |   // 2. Verify H1 title content and single-line classes
  13 |   const h1 = page.getByRole('heading', { name: 'Tendências no Discurso Político Brasileiro' });
> 14 |   await expect(h1).toBeVisible();
     |                    ^ Error: expect(locator).toBeVisible() failed
  15 |   
  16 |   // 3. Verify Carousel controls visibility on hover
  17 |   await page.locator('div.group').filter({ hasText: 'Perfis em Destaque' }).hover();
  18 |   await expect(page.getByLabel('Próximo Candidato')).toBeVisible();
  19 | 
  20 |   // 4. Verify Internal Page formatting (Candidatos)
  21 |   await page.goto(`${PRODUCTION_URL}/alvos`);
  22 |   await expect(page.getByRole('heading', { name: 'Central de Candidatos' })).toBeVisible();
  23 |   await expect(page.getByText('Radar de Severidade e Atividade')).toBeVisible();
  24 | 
  25 |   console.log('✅ Final Operational Check Passed: AdSense script is RAW, H1 is fixed, and internal pages are Editorial.');
  26 | });
  27 | 
```