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
          - generic [ref=e46]:
            - generic [ref=e47]: Aporte de Inteligência
            - generic [ref=e48]: ⚡ 0 CI
          - button "Restaurar Aporte" [ref=e51]
        - generic [ref=e54]: Monitor Ativo
        - generic [ref=e55]:
          - generic [ref=e56]:
            - generic [ref=e57]: Alertas (24h)
            - generic [ref=e58]: "3.646"
          - generic [ref=e59]:
            - generic [ref=e60]: Monitorados
            - generic [ref=e61]: "339"
          - generic [ref=e62]:
            - generic [ref=e63]: Amostragem
            - generic [ref=e64]: 64.1k
          - generic [ref=e66]:
            - generic [ref=e67]: Resiliência
            - generic [ref=e68]: 94.3%
        - generic [ref=e71]: OBSERVATÓRIO CÍVICO
    - main [ref=e72]:
      - generic [ref=e75]:
        - heading "404" [level=1] [ref=e76]
        - heading "This page could not be found." [level=2] [ref=e78]
  - alert [ref=e79]
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