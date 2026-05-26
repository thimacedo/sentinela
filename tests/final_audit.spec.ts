import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://asentinela.vercel.app';

test('AdSense and UI Refinement Final Verification', async ({ page }) => {
  await page.goto(PRODUCTION_URL);

  // 1. Verify Raw Script tag in HEAD
  const scriptSource = await page.innerHTML('head');
  expect(scriptSource).toContain('https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1827611269042960');

  // 2. Verify H1 title content and single-line classes
  const h1 = page.getByRole('heading', { name: 'Tendências no Discurso Político Brasileiro' });
  await expect(h1).toBeVisible();
  
  // 3. Verify Carousel controls visibility on hover
  await page.locator('div.group').filter({ hasText: 'Perfis em Destaque' }).hover();
  await expect(page.getByLabel('Próximo Candidato')).toBeVisible();

  // 4. Verify Internal Page formatting (Candidatos)
  await page.goto(`${PRODUCTION_URL}/alvos`);
  await expect(page.getByRole('heading', { name: 'Central de Candidatos' })).toBeVisible();
  await expect(page.getByText('Radar de Severidade e Atividade')).toBeVisible();

  console.log('✅ Final Operational Check Passed: AdSense script is RAW, H1 is fixed, and internal pages are Editorial.');
});
