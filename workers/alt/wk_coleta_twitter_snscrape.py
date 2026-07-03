# Arquivo 3: workers/alt/wk_coleta_twitter_snscrape.py

# workers/alt/wk_coleta_twitter_snscrape.py
"""Worker de coleta do Twitter/X via snscrape.
Alternativa gratuita ao Xquik — sem API key, scraping direto da web.
"""

import snscrape.modules.twitter as sntwitter
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict, Any, Optional

# ... (conteúdo completo conforme acima) ...

if __name__ == "__main__":
    # ... exemplo de uso ...
