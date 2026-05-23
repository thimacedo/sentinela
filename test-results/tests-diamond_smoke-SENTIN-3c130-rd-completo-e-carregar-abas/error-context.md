# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\diamond_smoke.spec.ts >> SENTINELA | Next.js Edition - Smoke Tests >> deve acessar o dashboard completo e carregar abas
- Location: tests\diamond_smoke.spec.ts:29:9

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "WAR ROOM"
Received string:    "404"
Timeout: 5000ms

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('h1')
    9 × locator resolved to <h1 class="next-error-h1">404</h1>
      - unexpected value "404"

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - heading "404" [level=1] [ref=e4]
    - heading "This page could not be found." [level=2] [ref=e6]
  - alert [ref=e7]
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
  17 |         await expect(page.locator('h1')).toContainText('WAR ROOM');
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
> 34 |         await expect(page.locator('h1')).toContainText('WAR ROOM');
     |                                          ^ Error: expect(locator).toContainText(expected) failed
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