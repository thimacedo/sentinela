# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\frontend_crawler.spec.ts >> SENTINELA | Frontend Crawler & Button Tester >> Deve renderizar a rota /alertas sem erros críticos no console
- Location: tests\frontend_crawler.spec.ts:22:13

# Error details

```
Error: expect(received).toBeLessThan(expected)

Expected: < 400
Received:   500
```

# Page snapshot

```yaml
- generic:
  - generic [active]:
    - generic [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]:
          - navigation [ref=e6]:
            - button "previous" [disabled] [ref=e7]:
              - img "previous" [ref=e8]
            - generic [ref=e10]:
              - generic [ref=e11]: 1/
              - text: "1"
            - button "next" [disabled] [ref=e12]:
              - img "next" [ref=e13]
          - img
        - generic [ref=e15]:
          - link "Next.js 16.2.6 (stale) Turbopack" [ref=e16] [cursor=pointer]:
            - /url: https://nextjs.org/docs/messages/version-staleness
            - img [ref=e17]
            - generic "There is a newer version (16.2.10) available, upgrade recommended!" [ref=e19]: Next.js 16.2.6 (stale)
            - generic [ref=e20]: Turbopack
          - img
      - generic [ref=e21]:
        - dialog "Runtime Error" [ref=e22]:
          - generic [ref=e25]:
            - generic [ref=e26]:
              - generic [ref=e27]:
                - generic [ref=e29]: Runtime Error
                - generic [ref=e30]:
                  - button "Copy Error Info" [ref=e31] [cursor=pointer]:
                    - img [ref=e32]
                  - button "No related documentation found" [disabled] [ref=e34]:
                    - img [ref=e35]
                  - button "Attach Node.js inspector" [ref=e37] [cursor=pointer]:
                    - img [ref=e38]
              - generic [ref=e47]: "An unexpected Turbopack error occurred. Please see the output of `next dev` for more details."
            - generic [ref=e50]:
              - paragraph [ref=e51]:
                - text: Call Stack
                - generic [ref=e52]: "2"
              - button "Show 2 ignore-listed frame(s)" [ref=e53] [cursor=pointer]:
                - text: Show 2 ignore-listed frame(s)
                - img [ref=e54]
          - generic [ref=e56]: "1"
          - generic [ref=e57]: "2"
        - contentinfo [ref=e58]:
          - region "Error feedback" [ref=e59]:
            - paragraph [ref=e60]:
              - link "Was this helpful?" [ref=e61] [cursor=pointer]:
                - /url: https://nextjs.org/telemetry#error-feedback
            - button "Mark as helpful" [ref=e62] [cursor=pointer]:
              - img [ref=e63]
            - button "Mark as not helpful" [ref=e66] [cursor=pointer]:
              - img [ref=e67]
    - generic [ref=e73] [cursor=pointer]:
      - button "Open Next.js Dev Tools" [ref=e74]:
        - img [ref=e75]
      - generic [ref=e78]:
        - button "Open issues overlay" [ref=e79]:
          - generic [ref=e80]:
            - generic [ref=e81]: "0"
            - generic [ref=e82]: "1"
          - generic [ref=e83]: Issue
        - button "Collapse issues badge" [ref=e84]:
          - img [ref=e85]
  - alert [ref=e87]
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
> 47 |             expect(response?.status()).toBeLessThan(400);
     |                                        ^ Error: expect(received).toBeLessThan(expected)
  48 |             
  49 |             if (filteredErrors.length > 0) {
  50 |                 console.error(`Erros na rota ${route}:`, filteredErrors);
  51 |             }
  52 |             expect(filteredErrors).toHaveLength(0);
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