import scrapy
import re
from scrapy_playwright.page import PageMethod
from ..items import InstagramCommentItem

class InstagramDOMSpider(scrapy.Spider):
    """Tier 2: Usa Playwright para renderizar JavaScript."""
    name = 'instagram_dom'
    
    custom_settings = {
        # ✅ Playwright APENAS aqui no Tier 2
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 3,
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'timeout': 30000,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        },
        'ITEM_PIPELINES': {
            'sentinela_scrapy.pipelines.QualityGatePipeline': 300,
        },

    }
    
    def __init__(self, username='', max_posts=5, max_comments=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username
        self.max_posts = int(max_posts)
        self.max_comments = int(max_comments)

    def start_requests(self):
        url = f"https://www.instagram.com/{self.username}/"
        yield scrapy.Request(
            url=url,
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "article")
                ],
                "tier": 2
            },
            callback=self.parse,
            errback=self.handle_error,
            dont_filter=True
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        content = await page.content()
        await page.close()
        
        # Regex básico para pegar links de posts (simplificado)
        links = re.findall(r'href="/(p|reel)/([^/"]+)/"', content)
        seen_codes = set()
        posts = []
        for type_cmd, shortcode in links:
            if shortcode not in seen_codes:
                posts.append(shortcode)
                seen_codes.add(shortcode)
                if len(posts) >= self.max_posts:
                    break
                    
        self.logger.info(f"✅ Tier 2: Encontrados {len(posts)} posts via Playwright para @{self.username}")
        
        for shortcode in posts:
            # Em um cenário real, aqui precisaríamos de outra requisição Playwright 
            # para cada post para pegar comentários se não conseguirmos via JSON
            self.logger.info(f"🔍 Tier 2: (Simulado) Coletando comentários do post {shortcode}")
            
    def handle_error(self, failure):
        tier = failure.request.meta.get('tier', 2)
        self.logger.error(f"❌ Tier {tier}: Requisição Playwright falhou - {failure.value}")
