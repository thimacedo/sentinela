import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://asentinela.vercel.app';

test.describe('SENTINELA | Next.js Edition - Link & Routing Tests', () => {
    test.setTimeout(60000);

    test('deve navegar por todas as abas sem erros', async ({ page }) => {
        await page.goto(`${PRODUCTION_URL}/dashboard`);

        // Aguarda carregamento inicial
        await page.waitForSelector('h1:has-text("WAR ROOM")', { timeout: 30000 });

        // Lista de abas a serem testadas (textos em uppercase)
        const tabs = [
            { text: 'FORENSE' },
            { text: 'ALVOS' },
            { text: 'DOSSIÊS' },
            { text: 'ALERTAS' },
            { text: 'REDE' },
            { text: 'FILA' },
            { text: 'GERAL' } // Volta ao início
        ];

        for (const t of tabs) {
            console.log(`Testando aba: ${t.text}`);
            
            // Clica na aba pelo texto contido nela
            const tabButton = page.locator(`button[role="tab"]:has-text("${t.text}")`);
            await expect(tabButton).toBeVisible();
            await tabButton.click();
            
            // Verifica se a aba ficou no estado ativo
            await expect(page.locator('button[role="tab"][data-state="active"]')).toContainText(t.text);
            
            // Pequeno delay para transição visual
            await page.waitForTimeout(500);
        }

        // Verifica se há erros críticos no console
        const errors: string[] = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', msg => {
            if (msg.type() === 'error') errors.push(msg.text());
        });

        expect(errors.filter(e => e.includes('Failed to load') || e.includes('TypeError'))).toHaveLength(0);
        console.log('Navegação concluída com sucesso! Todas as abas do Next.js estão operacionais.');
    });
});
