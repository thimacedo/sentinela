# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\frontend_crawler.spec.ts >> SENTINELA | Frontend Crawler & Button Tester >> Deve renderizar a rota / sem erros críticos no console
- Location: tests\frontend_crawler.spec.ts:22:13

# Error details

```
Error: expect(received).toHaveLength(expected)

Expected length: 0
Received length: 6
Received array:  ["Failed to load resource: the server responded with a status of 400 ()", "Failed to load resource: the server responded with a status of 404 (Not Found)", "Failed to load resource: the server responded with a status of 404 (Not Found)", "Failed to load resource: the server responded with a status of 404 (Not Found)", "Failed to load resource: the server responded with a status of 404 (Not Found)", "Failed to load resource: the server responded with a status of 404 (Not Found)"]
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
        - button "CANDIDATOS" [ref=e19]:
          - img [ref=e20]
          - generic [ref=e25]: CANDIDATOS
        - button "ALERTAS" [ref=e26]:
          - img [ref=e27]
          - generic [ref=e29]: ALERTAS
        - button "TENDÊNCIAS" [ref=e30]:
          - img [ref=e31]
          - generic [ref=e34]: TENDÊNCIAS
        - button "RELATÓRIOS" [ref=e35]:
          - img [ref=e36]
          - generic [ref=e39]: RELATÓRIOS
      - generic [ref=e40]:
        - generic [ref=e43]: Monitor Ativo
        - generic [ref=e44]: OBSERVATÓRIO CÍVICO
    - main [ref=e45]:
      - main [ref=e48]:
        - generic [ref=e49]:
          - generic [ref=e51]:
            - generic [ref=e52]: 📊
            - generic [ref=e53]:
              - generic [ref=e54]:
                - paragraph [ref=e55]: Observatório de Discurso Cívico
                - heading "Tendências no Discurso Político Brasileiro" [level=1] [ref=e56]
              - paragraph [ref=e57]: Acompanhe em tempo real os padrões de discurso de ódio e violência em redes sociais de candidatos e políticos monitorados. Transparência que alimenta a democracia.
          - generic [ref=e58]:
            - generic [ref=e59]:
              - generic [ref=e60]:
                - img [ref=e61]
                - generic [ref=e63]: Alertas Acumulados
              - generic [ref=e64]: ...
              - paragraph [ref=e65]: Casos com ódio identificados
            - generic [ref=e66]:
              - generic [ref=e67]:
                - img [ref=e68]
                - generic [ref=e73]: Monitorados
              - generic [ref=e74]: ...
              - paragraph [ref=e75]: Candidatos sob observação
            - generic [ref=e76]:
              - generic [ref=e77]:
                - img [ref=e78]
                - generic [ref=e81]: Posts Processados
              - generic [ref=e82]: ...k
              - paragraph [ref=e83]: Total coletados
          - generic [ref=e85]:
            - generic [ref=e86]: 🚨
            - generic [ref=e87]:
              - heading "Análise de Resiliência Democrática" [level=3] [ref=e88]
              - paragraph [ref=e89]: O sistema detectou um índice de resiliência de 0% no discurso das redes sociais brasileiras nas últimas 24h.
              - generic [ref=e90]:
                - link "Ver Detalhes" [ref=e91] [cursor=pointer]:
                  - /url: /metodologia
                - button "Compartilhar" [ref=e92]
        - generic [ref=e93]:
          - generic [ref=e94]:
            - heading "Atividade de Hostilidade (24h)" [level=2] [ref=e95]: Atividade de Hostilidade (24h)
            - generic [ref=e97]: Monitoramento Live Ativo
          - generic [ref=e99]: DESSERIALIZANDO SÉRIE TEMPORAL...
        - generic [ref=e100]:
          - generic [ref=e101]:
            - heading "📰 Destaques Recentes" [level=2] [ref=e102]
            - link "Ver tudo →" [ref=e103] [cursor=pointer]:
              - /url: /alertas
          - paragraph [ref=e105]: Carregando destaques...
        - insertion [ref=e107]:
          - iframe [ref=e109]:
            
        - generic [ref=e110]:
          - heading "🔬 Análises e Insights" [level=2] [ref=e111]
          - generic [ref=e112]:
            - generic [ref=e114]:
              - img [ref=e116]
              - generic [ref=e119]:
                - generic [ref=e120]:
                  - heading "Padrão de Discurso" [level=3] [ref=e121]
                  - generic [ref=e122]: TENDÊNCIA
                - paragraph [ref=e123]: Análise volumétrica da hostilidade detectada nos alvos ativos.
                - generic [ref=e124]:
                  - paragraph [ref=e125]: 📊 Saúde do Discurso
                  - paragraph [ref=e126]: 0%
                - paragraph [ref=e128]:
                  - strong [ref=e129]: "💡 Insight:"
                  - text: A tendência indica estabilidade com picos isolados de hostilidade ad hominem.
                - generic [ref=e130]:
                  - generic [ref=e131]:
                    - generic [ref=e132]: "CONFIANÇA:"
                    - generic [ref=e133]: 94%
                  - text: "0"
                - link "Explorar dados completos →" [ref=e134] [cursor=pointer]:
                  - /url: /analise
            - generic [ref=e136]:
              - img [ref=e138]
              - generic [ref=e140]:
                - generic [ref=e141]:
                  - heading "Comportamento Coordenado" [level=3] [ref=e142]
                  - generic [ref=e143]: PADRÃO
                - paragraph [ref=e144]: Detecção de mensagens idênticas ou altamente similares em massa.
                - paragraph [ref=e146]:
                  - strong [ref=e147]: "💡 Insight:"
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
            - heading "📅 Linha do Tempo" [level=2] [ref=e155]: 📅 Linha do Tempo
            - generic [ref=e157]:
              - button "24h" [ref=e158] [cursor=pointer]
              - button "7d" [ref=e159] [cursor=pointer]
              - button "30d" [ref=e160] [cursor=pointer]
          - paragraph [ref=e161]: Histórico e picos de ocorrência em ordem cronológica (Últimas 24 Horas)
          - paragraph [ref=e163]: Nenhum evento detectado no radar para este período.
        - generic [ref=e164]:
          - generic [ref=e165]:
            - heading "👤 Perfis em Destaque" [level=2] [ref=e166]
            - paragraph [ref=e167]: Use as setas para explorar →
          - paragraph [ref=e171]: Carregando perfis...
        - generic [ref=e172]:
          - generic [ref=e173]:
            - img [ref=e174]
            - heading "📖 Sobre Este Observatório" [level=3] [ref=e176]
          - generic [ref=e177]:
            - generic [ref=e178]:
              - generic [ref=e179]:
                - paragraph [ref=e180]:
                  - text: O
                  - strong [ref=e181]: Sentinela
                  - text: monitora padrões de discurso em redes sociais para promover transparência e alimentar o debate democrático brasileiro.
                - paragraph [ref=e182]: Nossa plataforma identifica tendências de ódio, hostilidade e desinformação, fornecendo dados técnicos para a sociedade civil e órgãos de controle.
              - generic [ref=e183]:
                - heading "O Que Fazemos" [level=4] [ref=e184]:
                  - img [ref=e185]
                  - text: O Que Fazemos
                - list [ref=e188]:
                  - listitem [ref=e189]:
                    - generic [ref=e190]: ✓
                    - text: Coleta autônoma de posts públicos em redes sociais
                  - listitem [ref=e191]:
                    - generic [ref=e192]: ✓
                    - text: Identificação de padrões de discurso de ódio e violência
                  - listitem [ref=e193]:
                    - generic [ref=e194]: ✓
                    - text: Relatórios analíticos com classificação semântica MCA v2.2
                  - listitem [ref=e195]:
                    - generic [ref=e196]: ✓
                    - text: Alertas em tempo real sobre picos anormais de hostilidade
            - generic [ref=e197]:
              - generic [ref=e198]:
                - heading "Limitações Importantes" [level=4] [ref=e199]:
                  - img [ref=e200]
                  - text: Limitações Importantes
                - list [ref=e202]:
                  - listitem [ref=e203]:
                    - generic [ref=e204]: ⚠️
                    - text: Não substitui análise humana — ferramenta de pesquisa
                  - listitem [ref=e205]:
                    - generic [ref=e206]: ⚠️
                    - text: Baseado em posts públicos — não detecta contas privadas
                  - listitem [ref=e207]:
                    - generic [ref=e208]: ⚠️
                    - text: Classificação por IA — sujeita a falsos positivos
                  - listitem [ref=e209]:
                    - generic [ref=e210]: ⚠️
                    - text: Não visa julgamento político, apenas transparência de dados
              - generic [ref=e211]:
                - heading "Metodologia Técnica" [level=4] [ref=e212]:
                  - img [ref=e213]
                  - text: Metodologia Técnica
                - generic [ref=e216]:
                  - paragraph [ref=e217]:
                    - strong [ref=e218]: "Coleta:"
                    - text: Motores Playwright v2 / Zyte
                  - paragraph [ref=e219]:
                    - strong [ref=e220]: "Processamento:"
                    - text: Análise semântica Híbrida (Mistral/Ollama)
                  - paragraph [ref=e221]:
                    - strong [ref=e222]: "Protocolo:"
                    - text: PASA v70.4 — Critérios de Análise
                  - paragraph [ref=e223]:
                    - strong [ref=e224]: "Frequência:"
                    - text: Ciclos de 24h com Autopilot L3
          - generic [ref=e225]:
            - paragraph [ref=e226]: 📚 Explore nossa documentação técnica para entender os algoritmos.
            - generic [ref=e227]:
              - link "Documentação" [ref=e228] [cursor=pointer]:
                - /url: /metodologia
              - link "Publicações" [ref=e229] [cursor=pointer]:
                - /url: /dossies
        - generic [ref=e232]:
          - generic [ref=e233]: 💎
          - heading "Inteligência Ilimitada" [level=3] [ref=e234]
          - paragraph [ref=e235]: Dossiês completos, análise de grafos de influência e relatórios em tempo real com validade técnica.
          - generic [ref=e236]:
            - button "Ver Planos de Acesso" [ref=e237]
            - paragraph [ref=e238]: Apoie o observatório a partir de R$ 99/mês
        - generic [ref=e239]:
          - generic [ref=e240]:
            - generic [ref=e241]: S
            - paragraph [ref=e242]: SentinelaDemocrática
          - paragraph [ref=e243]: Tecnologia de vigilância cívica para a transparência do processo democrático brasileiro.
          - generic [ref=e244]:
            - link "Termos" [ref=e245] [cursor=pointer]:
              - /url: /termos
            - link "Metodologia" [ref=e246] [cursor=pointer]:
              - /url: /metodologia
            - link "LGPD" [ref=e247] [cursor=pointer]:
              - /url: /lgpd
            - link "Privacidade" [ref=e248] [cursor=pointer]:
              - /url: /privacidade
            - link "GitHub" [ref=e249] [cursor=pointer]:
              - /url: https://github.com/THIAGO/sentinela
  - button "Open Next.js Dev Tools" [ref=e255] [cursor=pointer]:
    - img [ref=e256]
  - alert [ref=e259]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const LOCAL_URL = 'http://localhost:3000';
  4  | 
  5  | test.describe('SENTINELA | Frontend Crawler & Button Tester', () => {
  6  |     test.setTimeout(120000);
  7  | 
  8  |     const routes = [
  9  |         '/',
  10 |         '/analise',
  11 |         '/alvos',
  12 |         '/alertas',
  13 |         '/rede',
  14 |         '/relatorios',
  15 |         '/termos',
  16 |         '/metodologia',
  17 |         '/lgpd',
  18 |         '/privacidade'
  19 |     ];
  20 | 
  21 |     for (const route of routes) {
  22 |         test(`Deve renderizar a rota ${route} sem erros críticos no console`, async ({ page }) => {
  23 |             const errors: string[] = [];
  24 |             page.on('pageerror', error => errors.push(error.message));
  25 |             page.on('console', msg => {
  26 |                 if (msg.type() === 'error') {
  27 |                     errors.push(msg.text());
  28 |                 }
  29 |             });
  30 | 
  31 |             // Usando domcontentloaded para ser mais rápido e evitar travamento por ads
  32 |             const response = await page.goto(`${LOCAL_URL}${route}`, { waitUntil: 'domcontentloaded' });
  33 |             
  34 |             // Aguarda um pouco para os componentes montarem
  35 |             await page.waitForTimeout(2000);
  36 |             
  37 |             // Ignorar erros conhecidos ou de terceiros (AdSense, falhas de rede de anúncios, extensões)
  38 |             const filteredErrors = errors.filter(e => 
  39 |                 !e.includes('google') && 
  40 |                 !e.includes('adsbygoogle') &&
  41 |                 !e.toLowerCase().includes('favicon') &&
  42 |                 !e.includes('ERR_BLOCKED_BY_CLIENT') &&
  43 |                 !e.includes('ERR_NAME_NOT_RESOLVED') &&
  44 |                 !e.includes('A `require()` style import is forbidden') // Ignorar warnings de linter
  45 |             );
  46 |             
  47 |             expect(response?.status()).toBeLessThan(400);
  48 |             
  49 |             if (filteredErrors.length > 0) {
  50 |                 console.error(`Erros na rota ${route}:`, filteredErrors);
  51 |             }
> 52 |             expect(filteredErrors).toHaveLength(0);
     |                                    ^ Error: expect(received).toHaveLength(expected)
  53 |         });
  54 |     }
  55 | 
  56 |     test('Deve checar interatividade básica e botões da Navbar/Sidebar', async ({ page }) => {
  57 |         await page.goto(LOCAL_URL);
  58 |         await page.waitForTimeout(2000);
  59 |         
  60 |         // Coleta todos os botões visíveis
  61 |         const buttonsCount = await page.locator('button').count();
  62 |         expect(buttonsCount).toBeGreaterThan(0);
  63 |         
  64 |         // Coleta todos os links internos
  65 |         const links = await page.locator('a[href^="/"]').evaluateAll(anchors => anchors.map(a => a.getAttribute('href')));
  66 |         const uniqueLinks = [...new Set(links)];
  67 |         
  68 |         console.log(`Encontrados ${uniqueLinks.length} links internos e ${buttonsCount} botões.`);
  69 |         
  70 |         for (const link of uniqueLinks) {
  71 |             if (link) {
  72 |                 const res = await page.request.get(`${LOCAL_URL}${link}`);
  73 |                 expect(res.status()).toBeLessThan(400);
  74 |             }
  75 |         }
  76 |     });
  77 | });
  78 | 
```