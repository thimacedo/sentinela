import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://asentinela.vercel.app';

test('debug production site', async ({ page }) => {
    page.on('console', msg => console.log(`BROWSER CONSOLE: ${msg.text()}`));
    page.on('requestfailed', request => console.log(`REQUEST FAILED: ${request.url()} - ${request.failure()?.errorText}`));
    page.on('response', response => {
        if (response.status() >= 400) {
            console.log(`RESPONSE ERROR: ${response.status()} ${response.url()}`);
        }
    });

    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('networkidle');

    const title = await page.title();
    console.log(`Page Title: ${title}`);

    const kpiMonitorados = page.locator('#kpi-monitorados');
    const text = await kpiMonitorados.innerText();
    console.log(`KPI Monitorados current text: ${text}`);

    // Screenshot for visual check
    await page.screenshot({ path: 'debug_production.png' });
});
