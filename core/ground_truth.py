import csv
import os
from typing import Optional, Dict

class GroundTruthDB:
    """
    Camada de Sanitização Determinística (PASA v94.0)
    Elimina alucinações da malha de IA forçando dados reais baseados
    em um CSV de verdades absolutas ('alvos_sanitizacao.csv').
    """
    def __init__(self):
        self._db: Dict[str, dict] = {}
        self._load_csv()

    def _load_csv(self):
        # Tenta carregar do CSV de sanitização fornecido na raiz
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'alvos_sanitizacao.csv')
        if not os.path.exists(csv_path):
            print("[GroundTruth] CSV de sanitização não encontrado.")
            return

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                if not row or not row.get("username"):
                    continue
                try:
                    username = str(row["username"]).strip().lower().replace("@", "")
                    nome_completo = str(row["nome_completo"]).strip()
                    cargo = str(row["cargo"]).strip()
                    sexo = str(row.get("sexo", "NI")).strip().upper()
                    
                    self._db[username] = {
                        "nome_completo": nome_completo,
                        "cargo": cargo,
                        "sexo": sexo,
                        "validado": True
                    }
                except Exception:
                    continue
        print(f"[GroundTruth] Carregadas {len(self._db)} verdades absolutas.")

    def get_truth(self, username: str) -> Optional[dict]:
        """Retorna a verdade absoluta para um username se ele existir no banco local."""
        return self._db.get(username.strip().lower().replace("@", ""))

# Instância Singleton
ground_truth = GroundTruthDB()
