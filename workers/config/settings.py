import os
from dotenv import load_dotenv

load_dotenv()

# Configurações de Ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")

# Caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DOCS_DIR = os.path.join(BASE_DIR, "config", "api_docs")

# Limites e Intervalos
DEFAULT_RETRY_LIMIT = 3
TIER_INTERVALS = {
    "bronze": 300,  # 5 min
    "silver": 180,  # 3 min
    "gold": 60,     # 1 min
    "elite": 10     # 10 seg
}
