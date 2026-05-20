import re

# Read the file
with open(r'.\workers\scrapers\ig_zyte.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Old method pattern
old_method = r'''    async def fetch_comments_via_zyte\(self, target: Target\) -> list\[dict\]:
        \"""Extração real via Zyte API.\"""
        api_key = os\.getenv\("ZYTE_API_KEY"\)
        if not api_key:
            raise RuntimeError\("zyte_api_key_missing"\)

        url = f"https://www\.instagram\.com/\{target\.username\}/"
        self\.logger\.info\("Zyte fetch iniciado \| target=@%s \| url=%s", target\.username, url\)

        import httpx
        import base64

        payload = \{
            "url": url,
            "browserHtml": True,
            "screenshot": False,
        \}

        async with httpx\.AsyncClient\(timeout=60\) as client:
            response = await client\.post\(\
                "https://api\.zyte\.com/v1/extract",\
                auth=\(api_key, ""\),\
                json=payload,\
            \)

        if response\.status_code >= 400:
            raise RuntimeError\(f"zyte_http_\{response\.status_code\}:\{response\.text\[:200\]}"\)\)

        data = response\.json\(\)
        html = data\.get\("browserHtml"\)\)
        
        # Simulação de processamento de comentários para validar o fluxo
        # Fase 1: apenas logar o sucesso da conexão e tamanho da resposta
        self\.logger\.info\("Zyte fetch concluído \| target=@%s \| html_len=%s", target\.username, len\(html\) if html else 0\)

        # Retorno de lista vazia proposital para manter simulado=True até a lógica de extração ser validada
        return \[\]'''

# New method
new_method = '''    async def fetch_comments_via_zyte(self, target: Target) -> list[dict]:
        """Extração real via Zyte API."""
        api_key = os.getenv("ZYTE_API_KEY")
        if not api_key:
            raise RuntimeError("zyte_api_key_missing")

        url = f"https://www.instagram.com/{target.username}/"
        self.logger.info("Zyte fetch iniciado | target=@%s | url=%s", target.username, url)

        import httpx
        import base64

        payload = {
            "url": url,
            "browserHtml": True,
            "screenshot": False,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.zyte.com/v1/extract",
                auth=(api_key, ""),
                json=payload,
            )

        if response.status_code >= 400:
            raise RuntimeError(f"zyte_http_{response.status_code}:{response.text[:200]}")

        data = response.json()
        html = data.get("browserHtml")
        
        # Fallback para httpResponseBody se browserHtml não estiver disponível
        if not html and data.get("httpResponseBody"):
            html = base64.b64decode(data["httpResponseBody"]).decode(
                "utf-8",
                errors="ignore",
            )

        if not html:
            raise RuntimeError("zyte_empty_html")

        # Log do sucesso da conexão e tamanho da resposta
        self.logger.info("Zyte fetch concluído | target=@%s | html_len=%s", target.username, len(html))

        # Armazenar status para uso no run_cycle
        self.last_fetch_status = "zyte_fetch_ok_parser_pending"

        # Retorno de lista vazia proposital para manter simulado=True até a lógica de extração ser validada
        return []'''

# Replace the method
new_content = re.sub(old_method, new_method, content, flags=re.DOTALL)

# Also update the error message in run_cycle
new_content = new_content.replace('error="zyte_fetch_not_implemented_or_empty"', 'error="zyte_fetch_ok_parser_pending"')

# Write back
with open(r'.\workers\scrapers\ig_zyte.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Method replacement completed!")
