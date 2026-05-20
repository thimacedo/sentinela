import os
import sys
from dotenv import load_dotenv

# Add current directory to path so we can import workers
sys.path.insert(0, os.getcwd())

# Load environment variables
load_dotenv()

def test_env_loading():
    zyte_key = os.getenv('ZYTE_API_KEY')
    supabase_url = os.getenv('SUPABASE_URL')
    
    print(f'ZYTE_API_KEY: {"SET" if zyte_key else "NOT SET"}')
    if zyte_key:
        print(f'  Value starts with: {zyte_key[:10]}...')
    
    print(f'SUPABASE_URL: {"SET" if supabase_url else "NOT SET"}')
    if supabase_url:
        print(f'  Value: {supabase_url[:50]}...')
    
    # Test that the worker can access these
    try:
        from workers.scrapers.ig_zyte import IGZyteWorker
        print('SUCCESS: Worker imports correctly')
        # Test that we can create an instance (though it will fail on missing dependencies)
        config = {}  # Minimal config
        worker = IGZyteWorker('test-worker', config)
        print('SUCCESS: Worker instantiation works')
        return True
    except Exception as e:
        print(f'ERROR: Failed to import/instantiate worker: {e}')
        return False

if __name__ == '__main__':
    test_env_loading()
