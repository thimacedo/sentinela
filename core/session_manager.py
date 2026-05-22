import json
import os
from typing import Optional, List, Dict

class SessionManager:
    def __init__(self, session_dir: str = "sessions"):
        self.session_dir = session_dir
        if not os.path.exists(self.session_dir): os.makedirs(self.session_dir)

    def save_session(self, profile_name: str, cookies: List[Dict]):
        with open(os.path.join(self.session_dir, f"{profile_name}_cookies.json"), 'w') as f:
            json.dump(cookies, f)

    def load_session(self, profile_name: str) -> Optional[List[Dict]]:
        path = os.path.join(self.session_dir, f"{profile_name}_cookies.json")
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f)
        return None

    def get_proxy_config(self): return None # Adicione seu proxy aqui se necessário

session_manager = SessionManager()
