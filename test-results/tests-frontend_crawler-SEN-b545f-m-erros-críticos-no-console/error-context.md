# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\frontend_crawler.spec.ts >> SENTINELA | Frontend Crawler & Button Tester >> Deve renderizar a rota /rede sem erros críticos no console
- Location: tests\frontend_crawler.spec.ts:22:13

# Error details

```
Error: page.waitForTimeout: Target page, context or browser has been closed
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
> 35 |             await page.waitForTimeout(2000);
     |                        ^ Error: page.waitForTimeout: Target page, context or browser has been closed
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