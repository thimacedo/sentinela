# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\frontend_crawler.spec.ts >> SENTINELA | Frontend Crawler & Button Tester >> Deve renderizar a rota /rede sem erros críticos no console
- Location: tests\frontend_crawler.spec.ts:22:13

# Error details

```
Error: expect(received).toHaveLength(expected)

Expected length: 0
Received length: 2
Received array:  ["Failed to load resource: the server responded with a status of 404 (Not Found)", "Failed to load resource: the server responded with a status of 404 (Not Found)"]
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
      - generic [ref=e47]:
        - generic [ref=e48]:
          - heading "Análise de Rede" [level=1] [ref=e49]
          - paragraph [ref=e50]: Mapeamento de comportamentos coordenados e clusters de influência. Identifique redes artificiais e padrões de automação no discurso digital.
        - generic [ref=e52]:
          - generic [ref=e53]:
            - generic [ref=e54]:
              - heading "Tendências e Redes Coordenadas" [level=2] [ref=e55]:
                - img [ref=e56]
                - text: Tendências e Redes Coordenadas
              - paragraph [ref=e59]: Mapeamento de Influência e Narrativas
            - generic [ref=e60]:
              - img [ref=e61]
              - generic [ref=e67]: Módulo Solenya v71.0
          - table [ref=e69]:
            - rowgroup [ref=e70]:
              - row "Identificação do Cluster Perfis Suspeitos Detecção Nível de Risco" [ref=e71]:
                - columnheader "Identificação do Cluster" [ref=e72]
                - columnheader "Perfis Suspeitos" [ref=e73]
                - columnheader "Detecção" [ref=e74]
                - columnheader "Nível de Risco" [ref=e75]
            - rowgroup [ref=e76]:
              - row "MAPEANDO CONEXÕES OCULTAS..." [ref=e77]:
                - cell "MAPEANDO CONEXÕES OCULTAS..." [ref=e78]
          - generic [ref=e79]: Algoritmo de Detecção de Padrões Coordenados Ativo
  - button "Open Next.js Dev Tools" [ref=e85] [cursor=pointer]:
    - img [ref=e86]
  - alert [ref=e89]
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