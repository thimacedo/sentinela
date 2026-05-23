# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\link_tester.spec.ts >> SENTINELA | Next.js Edition - Link & Routing Tests >> deve navegar por todas as abas sem erros
- Location: tests\link_tester.spec.ts:8:9

# Error details

```
TimeoutError: page.waitForSelector: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('h1:has-text("WAR ROOM")') to be visible

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
  5  | test.describe('SENTINELA | Next.js Edition - Link & Routing Tests', () => {
  6  |     test.setTimeout(60000);
  7  | 
  8  |     test('deve navegar por todas as abas sem erros', async ({ page }) => {
  9  |         await page.goto(`${PRODUCTION_URL}/dashboard`);
  10 | 
  11 |         // Aguarda carregamento inicial
> 12 |         await page.waitForSelector('h1:has-text("WAR ROOM")', { timeout: 30000 });
     |                    ^ TimeoutError: page.waitForSelector: Timeout 30000ms exceeded.
  13 | 
  14 |         // Lista de abas a serem testadas (textos em uppercase)
  15 |         const tabs = [
  16 |             { text: 'FORENSE' },
  17 |             { text: 'ALVOS' },
  18 |             { text: 'DOSSIÊS' },
  19 |             { text: 'ALERTAS' },
  20 |             { text: 'REDE' },
  21 |             { text: 'FILA' },
  22 |             { text: 'GERAL' } // Volta ao início
  23 |         ];
  24 | 
  25 |         for (const t of tabs) {
  26 |             console.log(`Testando aba: ${t.text}`);
  27 |             
  28 |             // Clica na aba pelo texto contido nela
  29 |             const tabButton = page.locator(`button[role="tab"]:has-text("${t.text}")`);
  30 |             await expect(tabButton).toBeVisible();
  31 |             await tabButton.click();
  32 |             
  33 |             // Verifica se a aba ficou no estado ativo
  34 |             await expect(page.locator('button[role="tab"][data-state="active"]')).toContainText(t.text);
  35 |             
  36 |             // Pequeno delay para transição visual
  37 |             await page.waitForTimeout(500);
  38 |         }
  39 | 
  40 |         // Verifica se há erros críticos no console
  41 |         const errors: string[] = [];
  42 |         page.on('pageerror', error => errors.push(error.message));
  43 |         page.on('console', msg => {
  44 |             if (msg.type() === 'error') errors.push(msg.text());
  45 |         });
  46 | 
  47 |         expect(errors.filter(e => e.includes('Failed to load') || e.includes('TypeError'))).toHaveLength(0);
  48 |         console.log('Navegação concluída com sucesso! Todas as abas do Next.js estão operacionais.');
  49 |     });
  50 | });
  51 | 
```