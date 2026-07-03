# Arquivo 5: workers/coleta_pipeline.py

# workers/coleta_pipeline.py
"""Pipeline de coleta do Twitter/X com fallback automático de 3 camadas.
Prioridade: 1) Xquik → 2) snscrape → 3) Playwright
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# ... (conteúdo completo conforme acima) ...
