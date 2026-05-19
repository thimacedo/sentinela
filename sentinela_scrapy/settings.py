BOT_NAME = 'sentinela_scrapy'

SPIDER_MODULES = ['sentinela_scrapy.spiders']
NEWSPIDER_MODULE = 'sentinela_scrapy.spiders'

# Respeito aos robots.txt
ROBOTSTXT_OBEY = False

# Configurações de concorrência
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# User Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Middlewares BÁSICOS (sem Playwright por padrão)
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
}

# Pipelines
ITEM_PIPELINES = {
    'sentinela_scrapy.pipelines.QualityGatePipeline': 300,
}

# Cookies
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Retry
RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Logs
LOG_LEVEL = 'INFO'
LOG_ENCODING = 'utf-8'

# Autothrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Timeout
DOWNLOAD_TIMEOUT = 30

# Redirect
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 3

# Memory management
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 512
MEMUSAGE_WARNING_MB = 256

# Exportação padrão (sobrescrito pelo runner)
FEEDS = {}
