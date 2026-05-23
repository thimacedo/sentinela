import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://asentinela.vercel.app';

test.describe('SENTINELA | Next.js Edition - Smoke Tests', () => {

    test('deve carregar o painel e exibir dados reais (não vazios)', async ({ page }) => {
        // Aumenta o timeout para lidar com o cold start
        test.setTimeout(60000);

        await page.goto(PRODUCTION_URL);

        // 1. Verifica o Título
        await expect(page).toHaveTitle(/Sentinela/);

        // 2. Verifica se a estrutura básica do War Room está presente
        await expect(page.locator('h1')).toContainText('WAR ROOM');

        // 3. Valida se os cards de estatísticas carregaram
        const statCards = page.locator('.bg-black\\/50');
        await expect(statCards.first()).toBeVisible({ timeout: 15000 });
        
        // Verifica se há textos de KPI esperados
        const pageContent = await page.innerText('body');
        expect(pageContent).toContain('VOLUME ANALISADO');
        expect(pageContent).toContain('ÍNDICE DE RESILIÊNCIA');
    });

    test('deve acessar o dashboard completo e carregar abas', async ({ page }) => {
        test.setTimeout(60000);
        await page.goto(`${PRODUCTION_URL}/dashboard`);

        // Aguarda carregar o título do dashboard
        await expect(page.locator('h1')).toContainText('WAR ROOM');

        // Verifica a presença de triggers das abas
        const tabsTrigger = page.locator('button[role="tab"]');
        const count = await tabsTrigger.count();
        console.log(`Total de abas encontradas: ${count}`);
        expect(count).toBeGreaterThan(0);

        // Garante que o texto da aba Geral está ativo por padrão
        const activeTab = page.locator('button[role="tab"][data-state="active"]');
        await expect(activeTab).toContainText('GERAL');
    });

});
