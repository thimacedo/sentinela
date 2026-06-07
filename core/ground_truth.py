import csv
import os
from typing import Optional, Dict

# Mapeamento de sufixos para inferência determinística de gênero (sem IA)
FEMININE_SUFFIXES = ("a", "e", "í", "is", "nha", "ela", "ana", "ia")
MASCULINE_SUFFIXES = ("o", "r", "s", "n", "l", "der", "el", "ão", "us")

class GroundTruthDB:
    """
    Camada de Sanitização Determinística (PASA v93.6)
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
            # Pula headers e separa por '|' ou ';'
            # O arquivo original pode usar delimitador de ; interno à primeira coluna se exportado incorretamente do Excel
            reader = csv.reader(f, delimiter='|')
            for row in reader:
                if not row: continue
                # Pula header identificando se a primeira coluna não é id numérico/UUID ou contem 'id'
                if len(row) < 4 and ';' in row[0]:
                    row_data = row[0].split(';')
                else:
                    row_data = row
                    
                if len(row_data) < 4 or 'id' in str(row_data[0]).lower():
                    continue 
                
                try:
                    # Formato do CSV: id;nome_completo;cargo;username;status...
                    username = str(row_data[3]).strip().lower().replace("@", "")
                    nome_completo = str(row_data[1]).strip()
                    cargo = str(row_data[2]).strip()
                    
                    self._db[username] = {
                        "nome_completo": nome_completo,
                        "cargo": cargo,
                        "sexo": self._inferir_genero_deterministico(nome_completo),
                        "validado": True
                    }
                except Exception:
                    continue
        print(f"[GroundTruth] Carregadas {len(self._db)} verdades absolutas.")

    def _inferir_genero_deterministico(self, nome: str) -> str:
        """Regras simples baseadas no nome para evitar que a IA erre o gênero."""
        if not nome: return "NI"
        partes = nome.split(' ')
        nome_limpo = partes[0] if partes else ""
        if not nome_limpo: return "NI"
        
        # Exceções comuns
        exceptions = {
            "andre": "M", "felipe": "M", "jose": "M", "lucas": "M", 
            "carlos": "M", "duda": "F", "luis": "M", "marcos": "M"
        }
        lower_nome = nome_limpo.lower()
        if lower_nome in exceptions:
            return exceptions[lower_nome]

        if lower_nome.endswith(FEMININE_SUFFIXES): return "F"
        if lower_nome.endswith(MASCULINE_SUFFIXES): return "M"
        return "NI"

    def get_truth(self, username: str) -> Optional[dict]:
        """Retorna a verdade absoluta para um username se ele existir no banco local."""
        return self._db.get(username.strip().lower().replace("@", ""))

# Instância Singleton
ground_truth = GroundTruthDB()
