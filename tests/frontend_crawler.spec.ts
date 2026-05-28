import { test, expect } from '@playwright/test';

const LOCAL_URL = 'http://localhost:3000';

test.describe('SENTINELA | Frontend Crawler & Button Tester', () => {
    test.setTimeout(120000);

    const routes = [
        '/',
        '/analise',
        '/alvos',
        '/alertas',
        '/rede',
        '/relatorios',
        '/termos',
        '/metodologia',
        '/lgpd',
        '/privacidade'
    ];

    for (const route of routes) {
        test(`Deve renderizar a rota ${route} sem erros críticos no console`, async ({ page }) => {
            const errors: string[] = [];
            page.on('pageerror', error => errors.push(error.message));
            page.on('console', msg => {
                if (msg.type() === 'error') {
                    errors.push(msg.text());
                }
            });

            // Usando domcontentloaded para ser mais rápido e evitar travamento por ads
            const response = await page.goto(`${LOCAL_URL}${route}`, { waitUntil: 'domcontentloaded' });
            
            // Aguarda um pouco para os componentes montarem
            await page.waitForTimeout(2000);
            
            // Ignorar erros conhecidos ou de terceiros (AdSense, falhas de rede de anúncios, extensões)
            const filteredErrors = errors.filter(e => 
                !e.includes('google') && 
                !e.includes('adsbygoogle') &&
                !e.toLowerCase().includes('favicon') &&
                !e.includes('ERR_BLOCKED_BY_CLIENT') &&
                !e.includes('ERR_NAME_NOT_RESOLVED') &&
                !e.includes('A `require()` style import is forbidden') // Ignorar warnings de linter
            );
            
            expect(response?.status()).toBeLessThan(400);
            
            if (filteredErrors.length > 0) {
                console.error(`Erros na rota ${route}:`, filteredErrors);
            }
            expect(filteredErrors).toHaveLength(0);
        });
    }

    test('Deve checar interatividade básica e botões da Navbar/Sidebar', async ({ page }) => {
        await page.goto(LOCAL_URL);
        await page.waitForTimeout(2000);
        
        // Coleta todos os botões visíveis
        const buttonsCount = await page.locator('button').count();
        expect(buttonsCount).toBeGreaterThan(0);
        
        // Coleta todos os links internos
        const links = await page.locator('a[href^="/"]').evaluateAll(anchors => anchors.map(a => a.getAttribute('href')));
        const uniqueLinks = [...new Set(links)];
        
        console.log(`Encontrados ${uniqueLinks.length} links internos e ${buttonsCount} botões.`);
        
        for (const link of uniqueLinks) {
            if (link) {
                const res = await page.request.get(`${LOCAL_URL}${link}`);
                expect(res.status()).toBeLessThan(400);
            }
        }
    });
});
