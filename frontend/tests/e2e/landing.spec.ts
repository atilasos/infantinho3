import { expect, test } from '@playwright/test';

test.describe('Portal headless - experiência pública', () => {
  test('apresenta hero de login Microsoft', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Uma experiência cooperativa entre alunos, professores e família.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Entrar com Microsoft' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Ver blog completo' })).toBeVisible();
  });

  test('hero mantém leitura confortável em mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /experiência cooperativa/i })).toBeVisible();
    const loginButton = page.getByRole('button', { name: 'Entrar com Microsoft' });
    await expect(loginButton).toBeVisible();
  });
});
