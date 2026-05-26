import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://asentinela.vercel.app';

test('Monetization and Editorial Consistency Check', async ({ page }) => {
  await page.goto(PRODUCTION_URL);

  // 1. Check AdSense Meta Tag
  const meta = await page.locator('meta[name="google-adsense-account"]');
  await expect(meta).toHaveAttribute('content', 'ca-pub-1827611269042960');

  // 2. Check H1 title wrap fix (visually hard to check, but we check if text is there)
  await expect(page.getByRole('heading', { name: 'Tendências no Discurso Político Brasileiro' })).toBeVisible();

  // 3. Check Candidate Carousel
  await page.locator('div.group').first().hover();
  await expect(page.getByLabel('Próximo Candidato')).toBeVisible();
  
  // 4. Check Internal Page Consistency (Análise)
  await page.goto(`${PRODUCTION_URL}/pericia`);
  await expect(page.getByRole('heading', { name: 'Análise Pericial' })).toBeVisible();
  await expect(page.getByText('Laboratório de Perícia')).toBeVisible();

  // 5. Check Alertas Page
  await page.goto(`${PRODUCTION_URL}/alertas`);
  await expect(page.getByRole('heading', { name: 'Central de Alertas' })).toBeVisible();

  console.log('✅ Consistency and Monetization verified.');
});
