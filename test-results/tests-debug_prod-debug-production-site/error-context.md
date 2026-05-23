# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\debug_prod.spec.ts >> debug production site
- Location: tests\debug_prod.spec.ts:5:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.innerText: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('#kpi-monitorados')

```

# Page snapshot

```yaml
- main [ref=e3]:
  - paragraph [ref=e4]:
    - generic [ref=e5]:
      - strong [ref=e6]: "404"
      - text: ": NOT_FOUND"
    - generic [ref=e7]:
      - text: "Code:"
      - code [ref=e8]: "`DEPLOYMENT_NOT_FOUND`"
    - generic [ref=e9]:
      - text: "ID:"
      - code [ref=e10]: "`gru1::nckzb-1779564618421-c822d771c429`"
  - link "This deployment cannot be found. For more information and troubleshooting, see our documentation." [ref=e11] [cursor=pointer]:
    - /url: https://vercel.com/docs/errors/DEPLOYMENT_NOT_FOUND
    - generic [ref=e12]: This deployment cannot be found. For more information and troubleshooting, see our documentation.
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const PRODUCTION_URL = 'https://sentinela-democratica-ruby.vercel.app';
  4  | 
  5  | test('debug production site', async ({ page }) => {
  6  |     page.on('console', msg => console.log(`BROWSER CONSOLE: ${msg.text()}`));
  7  |     page.on('requestfailed', request => console.log(`REQUEST FAILED: ${request.url()} - ${request.failure()?.errorText}`));
  8  |     page.on('response', response => {
  9  |         if (response.status() >= 400) {
  10 |             console.log(`RESPONSE ERROR: ${response.status()} ${response.url()}`);
  11 |         }
  12 |     });
  13 | 
  14 |     await page.goto(PRODUCTION_URL);
  15 |     await page.waitForLoadState('networkidle');
  16 | 
  17 |     const title = await page.title();
  18 |     console.log(`Page Title: ${title}`);
  19 | 
  20 |     const kpiMonitorados = page.locator('#kpi-monitorados');
> 21 |     const text = await kpiMonitorados.innerText();
     |                                       ^ Error: locator.innerText: Test timeout of 30000ms exceeded.
  22 |     console.log(`KPI Monitorados current text: ${text}`);
  23 | 
  24 |     // Screenshot for visual check
  25 |     await page.screenshot({ path: 'debug_production.png' });
  26 | });
  27 | 
```