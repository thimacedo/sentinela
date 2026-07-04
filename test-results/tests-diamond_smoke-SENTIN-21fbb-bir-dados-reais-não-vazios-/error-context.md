# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\diamond_smoke.spec.ts >> SENTINELA | Next.js Edition - Smoke Tests >> deve carregar o painel e exibir dados reais (não vazios)
- Location: tests\diamond_smoke.spec.ts:7:9

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "WAR ROOM"
Error: strict mode violation: locator('h1') resolved to 2 elements:
    1) <h1 class="text-brand-primary font-bold text-lg tracking-tighter">…</h1> aka getByRole('heading', { name: 'SENTINELAAI' })
    2) <h1 class="text-2xl sm:text-3xl md:text-4xl font-extrabold text-text-main tracking-tight leading-snug">…</h1> aka getByRole('heading', { name: 'Visão Tática Global' })

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('h1')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - complementary [ref=e3]:
      - generic [ref=e4]:
        - heading "SENTINELAAI" [level=1] [ref=e5]
        - button "Recolher menu" [ref=e6]:
          - img [ref=e7]
      - navigation [ref=e9]:
        - button "INÍCIO" [ref=e10]:
          - img [ref=e11]
          - generic [ref=e14]: INÍCIO
        - button "ANÁLISE" [ref=e15]:
          - img [ref=e16]
          - generic [ref=e18]: ANÁLISE
        - button "ESTATÍSTICAS" [ref=e19]:
          - img [ref=e20]
          - generic [ref=e22]: ESTATÍSTICAS
        - button "CANDIDATOS" [ref=e23]:
          - img [ref=e24]
          - generic [ref=e29]: CANDIDATOS
        - button "ALERTAS" [ref=e30]:
          - img [ref=e31]
          - generic [ref=e33]: ALERTAS
        - button "REDE" [ref=e34]:
          - img [ref=e35]
          - generic [ref=e38]: REDE
        - button "RELATÓRIOS" [ref=e39]:
          - img [ref=e40]
          - generic [ref=e43]: RELATÓRIOS
      - generic [ref=e44]:
        - generic [ref=e45]:
          - generic [ref=e47]: Aporte de Inteligência
          - button "Restaurar Aporte" [ref=e51]
        - generic [ref=e54]: Monitor Ativo
        - generic [ref=e55]:
          - generic [ref=e56]:
            - generic [ref=e57]: Alertas (24h)
            - generic [ref=e58]: ...
          - generic [ref=e59]:
            - generic [ref=e60]: Monitorados
            - generic [ref=e61]: ...
          - generic [ref=e62]:
            - generic [ref=e63]: Amostragem
            - generic [ref=e64]: ...
          - generic [ref=e66]:
            - generic [ref=e67]: Resiliência
            - generic [ref=e68]: 0%
        - generic [ref=e70]: OBSERVATÓRIO CÍVICO
    - main [ref=e71]:
      - main [ref=e74]:
        - generic [ref=e78]:
          - generic [ref=e79]:
            - img [ref=e80]
            - text: "Status: Monitoramento Ativo"
          - heading "Visão Tática Global" [level=1] [ref=e82]
          - paragraph [ref=e83]: Observatório de Discurso Cívico em tempo real. Padrões de comportamento anômalo e ações coordenadas detectadas via Protocolo PASA.
        - generic [ref=e84]:
          - generic [ref=e85]:
            - heading "📅 Linha do Tempo" [level=2] [ref=e86]: 📅 Linha do Tempo
            - generic [ref=e88]:
              - button "24h" [ref=e89] [cursor=pointer]
              - button "7d" [ref=e90] [cursor=pointer]
              - button "30d" [ref=e91] [cursor=pointer]
          - paragraph [ref=e92]: Histórico e picos de ocorrência em ordem cronológica (Últimas 24 Horas)
          - paragraph [ref=e94]: Nenhum evento detectado no radar para este período.
        - generic [ref=e99]:
          - generic [ref=e100]:
            - heading "📰 Destaques Recentes" [level=2] [ref=e101]
            - link "Ver tudo →" [ref=e102] [cursor=pointer]:
              - /url: /alertas
          - paragraph [ref=e104]: Carregando destaques...
        - generic "Espaço Publicitário" [ref=e105]:
          - insertion
        - generic [ref=e106]:
          - generic [ref=e107]:
            - generic [ref=e108]: 🔬
            - heading "Análises e Insights" [level=2] [ref=e109]
          - generic [ref=e110]:
            - generic [ref=e113]:
              - img [ref=e115]
              - generic [ref=e118]:
                - generic [ref=e119]:
                  - heading "Padrão de Discurso" [level=3] [ref=e120]
                  - generic [ref=e121]: TENDÊNCIA
                - paragraph [ref=e122]: Análise volumétrica da hostilidade detectada nos alvos ativos.
                - generic [ref=e123]:
                  - paragraph [ref=e124]: Saúde do Discurso
                  - paragraph [ref=e125]: 0%
                - paragraph [ref=e127]:
                  - strong [ref=e128]: "Insight Analítico:"
                  - text: A tendência indica estabilidade com picos isolados de hostilidade ad hominem.
                - generic [ref=e129]:
                  - generic [ref=e130]:
                    - generic [ref=e131]: "CONFIANÇA:"
                    - generic [ref=e132]: 94%
                  - text: "0"
                - link "Explorar dados completos →" [ref=e133] [cursor=pointer]:
                  - /url: /analise
            - generic [ref=e136]:
              - img [ref=e138]
              - generic [ref=e140]:
                - generic [ref=e141]:
                  - heading "Comportamento Coordenado" [level=3] [ref=e142]
                  - generic [ref=e143]: PADRÃO
                - paragraph [ref=e144]: Detecção de mensagens idênticas ou altamente similares em massa.
                - paragraph [ref=e146]:
                  - strong [ref=e147]: "Insight Analítico:"
                  - text: Monitoramento Solenya v71.0 ativo. Buscando padrões de automação.
                - generic [ref=e148]:
                  - generic [ref=e149]:
                    - generic [ref=e150]: "CONFIANÇA:"
                    - generic [ref=e151]: 88%
                  - text: "0"
                - link "Explorar dados completos →" [ref=e152] [cursor=pointer]:
                  - /url: /analise
        - generic [ref=e153]:
          - generic [ref=e154]:
            - generic [ref=e155]:
              - generic [ref=e156]: 👤
              - heading "Perfis em Destaque" [level=2] [ref=e157]
            - paragraph [ref=e158]: Use as setas para explorar →
          - paragraph [ref=e162]: Carregando perfis...
        - generic [ref=e163]:
          - generic [ref=e164]:
            - img [ref=e165]
            - heading "📖 Sobre Este Observatório" [level=3] [ref=e167]
          - generic [ref=e168]:
            - generic [ref=e169]:
              - generic [ref=e170]:
                - paragraph [ref=e171]:
                  - text: O
                  - strong [ref=e172]: Sentinela
                  - text: monitora padrões de discurso em redes sociais para promover transparência e alimentar o debate democrático brasileiro.
                - paragraph [ref=e173]: Nossa plataforma identifica tendências de ódio, hostilidade e desinformação, fornecendo dados técnicos para a sociedade civil e órgãos de controle.
              - generic [ref=e174]:
                - heading "O Que Fazemos" [level=4] [ref=e175]:
                  - img [ref=e176]
                  - text: O Que Fazemos
                - list [ref=e179]:
                  - listitem [ref=e180]:
                    - generic [ref=e181]: ✓
                    - text: Coleta autônoma de posts públicos em redes sociais
                  - listitem [ref=e182]:
                    - generic [ref=e183]: ✓
                    - text: Identificação de padrões de discurso de ódio e violência
                  - listitem [ref=e184]:
                    - generic [ref=e185]: ✓
                    - text: Relatórios analíticos com classificação semântica MCA v2.2
                  - listitem [ref=e186]:
                    - generic [ref=e187]: ✓
                    - text: Alertas em tempo real sobre picos anormais de hostilidade
            - generic [ref=e188]:
              - generic [ref=e189]:
                - heading "Limitações Importantes" [level=4] [ref=e190]:
                  - img [ref=e191]
                  - text: Limitações Importantes
                - list [ref=e193]:
                  - listitem [ref=e194]:
                    - generic [ref=e195]: ⚠️
                    - text: Não substitui análise humana — ferramenta de pesquisa
                  - listitem [ref=e196]:
                    - generic [ref=e197]: ⚠️
                    - text: Baseado em posts públicos — não detecta contas privadas
                  - listitem [ref=e198]:
                    - generic [ref=e199]: ⚠️
                    - text: Classificação por IA — sujeita a falsos positivos
                  - listitem [ref=e200]:
                    - generic [ref=e201]: ⚠️
                    - text: Não visa julgamento político, apenas transparência de dados
              - generic [ref=e202]:
                - heading "Metodologia Técnica" [level=4] [ref=e203]:
                  - img [ref=e204]
                  - text: Metodologia Técnica
                - generic [ref=e207]:
                  - paragraph [ref=e208]:
                    - strong [ref=e209]: "Coleta:"
                    - text: Motores Playwright v2 / Zyte
                  - paragraph [ref=e210]:
                    - strong [ref=e211]: "Processamento:"
                    - text: Análise semântica Híbrida (Mistral/Ollama)
                  - paragraph [ref=e212]:
                    - strong [ref=e213]: "Protocolo:"
                    - text: PASA v70.4 — Critérios de Análise
                  - paragraph [ref=e214]:
                    - strong [ref=e215]: "Frequência:"
                    - text: Ciclos de 24h com Autopilot L3
          - generic [ref=e216]:
            - paragraph [ref=e217]: 📚 Explore nossa documentação técnica para entender os algoritmos.
            - generic [ref=e218]:
              - link "Documentação" [ref=e219] [cursor=pointer]:
                - /url: /metodologia
              - link "Publicações" [ref=e220] [cursor=pointer]:
                - /url: /dossies
        - generic "Espaço Publicitário" [ref=e221]:
          - insertion
        - generic [ref=e224]:
          - generic [ref=e225]: 💎
          - heading "Inteligência Ilimitada" [level=3] [ref=e226]
          - paragraph [ref=e227]: Dossiês completos, análise de grafos de influência e relatórios em tempo real com validade técnica.
          - generic [ref=e228]:
            - button "Adquirir Créditos de Inteligência" [ref=e229]
            - paragraph [ref=e230]: Opere na rede a partir de 1.000 CI
        - generic [ref=e231]:
          - generic [ref=e232]:
            - generic [ref=e233]: S
            - paragraph [ref=e234]: SentinelaDemocrática
          - paragraph [ref=e235]: Tecnologia de vigilância cívica para a transparência do processo democrático brasileiro.
          - generic [ref=e236]:
            - link "Termos" [ref=e237] [cursor=pointer]:
              - /url: /termos
            - link "Metodologia" [ref=e238] [cursor=pointer]:
              - /url: /metodologia
            - link "LGPD" [ref=e239] [cursor=pointer]:
              - /url: /lgpd
            - link "Privacidade" [ref=e240] [cursor=pointer]:
              - /url: /privacidade
            - link "GitHub" [ref=e241] [cursor=pointer]:
              - /url: https://github.com/THIAGO/sentinela
  - alert [ref=e242]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const PRODUCTION_URL = 'https://asentinela.vercel.app';
  4  | 
  5  | test.describe('SENTINELA | Next.js Edition - Smoke Tests', () => {
  6  | 
  7  |     test('deve carregar o painel e exibir dados reais (não vazios)', async ({ page }) => {
  8  |         // Aumenta o timeout para lidar com o cold start
  9  |         test.setTimeout(60000);
  10 | 
  11 |         await page.goto(PRODUCTION_URL);
  12 | 
  13 |         // 1. Verifica o Título
  14 |         await expect(page).toHaveTitle(/Sentinela/);
  15 | 
  16 |         // 2. Verifica se a estrutura básica do War Room está presente
> 17 |         await expect(page.locator('h1')).toContainText('WAR ROOM');
     |                                          ^ Error: expect(locator).toContainText(expected) failed
  18 | 
  19 |         // 3. Valida se os cards de estatísticas carregaram
  20 |         const statCards = page.locator('.bg-black\\/50');
  21 |         await expect(statCards.first()).toBeVisible({ timeout: 15000 });
  22 |         
  23 |         // Verifica se há textos de KPI esperados
  24 |         const pageContent = await page.innerText('body');
  25 |         expect(pageContent).toContain('VOLUME ANALISADO');
  26 |         expect(pageContent).toContain('ÍNDICE DE RESILIÊNCIA');
  27 |     });
  28 | 
  29 |     test('deve acessar o dashboard completo e carregar abas', async ({ page }) => {
  30 |         test.setTimeout(60000);
  31 |         await page.goto(`${PRODUCTION_URL}/dashboard`);
  32 | 
  33 |         // Aguarda carregar o título do dashboard
  34 |         await expect(page.locator('h1')).toContainText('WAR ROOM');
  35 | 
  36 |         // Verifica a presença de triggers das abas
  37 |         const tabsTrigger = page.locator('button[role="tab"]');
  38 |         const count = await tabsTrigger.count();
  39 |         console.log(`Total de abas encontradas: ${count}`);
  40 |         expect(count).toBeGreaterThan(0);
  41 | 
  42 |         // Garante que o texto da aba Geral está ativo por padrão
  43 |         const activeTab = page.locator('button[role="tab"][data-state="active"]');
  44 |         await expect(activeTab).toContainText('GERAL');
  45 |     });
  46 | 
  47 | });
  48 | 
```