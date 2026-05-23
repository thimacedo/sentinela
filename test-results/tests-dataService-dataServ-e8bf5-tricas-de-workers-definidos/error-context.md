# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\dataService.test.js >> dataService - Worker Metrics >> deve ter os métodos de métricas de workers definidos
- Location: tests\dataService.test.js:4:9

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('dataService - Worker Metrics', () => {
  4  |     test('deve ter os métodos de métricas de workers definidos', async ({ page }) => {
  5  |         // Vai para uma página em branco e injeta as dependências mínimas ou vai para a home
> 6  |         await page.goto('http://localhost:3000'); // Assume o servidor dev está rodando
     |                    ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  7  |         
  8  |         const methodsExist = await page.evaluate(() => {
  9  |             // No contexto do navegador, o dataService deve estar disponível se o bundle carregou
  10 |             // Mas como é um módulo, talvez não esteja no window. 
  11 |             // Vamos tentar importar ou verificar se o app.js já o exportou para o window para debug
  12 |             return typeof window.dataService !== 'undefined' &&
  13 |                    typeof window.dataService.getWorkersMetrics === 'function' &&
  14 |                    typeof window.dataService.getWorkersCredits === 'function';
  15 |         });
  16 |         
  17 |         // Se não estiver no window, vamos injetar um script que importa o serviço
  18 |         if (!methodsExist) {
  19 |             const injectedExists = await page.evaluate(async () => {
  20 |                 const { dataService } = await import('./src/services/dataService.js');
  21 |                 return typeof dataService.getWorkersMetrics === 'function' &&
  22 |                        typeof dataService.getWorkersCredits === 'function';
  23 |             });
  24 |             expect(injectedExists).toBe(true);
  25 |         } else {
  26 |             expect(methodsExist).toBe(true);
  27 |         }
  28 |     });
  29 | });
  30 | 
```