# Playwright Python — Referência Operacional
_last_updated: 2026-05-20_

## Padrão de uso assíncrono (Teardown seguro)
> ⚠️ **Nunca** feche o browser fora do `finally`.
```python
async def run(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            # ... scraping
        except Exception as e:
            await page.screenshot(path="erro.png")
            raise
        finally:
            await browser.close()
```

## Seletores e Estabilidade
- Use `page.get_by_role()` antes de qualquer CSS.
- Sempre use `page.wait_for_load_state("networkidle")` para SPAs.

## Anti-detecção
- Randomize `user_agent`, `viewport` e adicione `page.wait_for_timeout()` (1-3s) entre ações humanas.
