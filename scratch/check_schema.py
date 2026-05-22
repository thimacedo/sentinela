import io
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
from core.supabase_service import get_supabase_client

db = get_supabase_client()
# we can just use the postgrest API to fetch the table schema? No, there is no direct schema endpoint.
# Try checking the 'comentarios' structure
try:
    res = db.table('comentarios').select('*').limit(1).execute()
    print("Comentarios sample:", res.data)
except Exception as e:
    print(e)
