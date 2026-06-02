import os
import sys
import json
import logging
import argparse
import asyncio
from pypdf import PdfReader

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

from core.ai_service import ai_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - RESEARCHER - %(levelname)s - %(message)s")
logger = logging.getLogger("researcher")

PROMPT_RESEARCH = """Você é um especialista em Processamento de Linguagem Natural (NLP) e Linguística Forense Digital.
Analise a seguinte amostra de texto extraída de uma base teórica/artigo sobre discurso de ódio, violência política, ironia e nuances de hostilidade:

--- INÍCIO DO TEXTO ---
{text_sample}
--- FIM DO TEXTO ---

Sua missão é extrair diretrizes acuradas e operacionais para treinar e refinar classificadores de IA de hostilidade política, especificamente para a taxonomia:
- ODIO_IDENTITARIO: preconceito de raça, religião, xenofobia/regionalismo, orientação sexual.
- VIOLENCIA_GENERO: misoginia e ofensas a mulheres.
- AMEACA: incitação à violência física ou morte.
- INSULTO_AD_HOMINEM: ataques à honra, competência pessoal ou aparência.
- ATAQUE_INSTITUCIONAL: deslegitimação de órgãos de Estado ou do sistema eleitoral.
- DANO_A_IMAGEM: teorizar crimes, imputar desvios de conduta grave ou corrupção.

Identifique regras operacionais práticas e palavras-chave específicas.
Retorne APENAS um objeto JSON válido contendo:
{
  "additional_rules": ["regra 1 (máx 150 caracteres)", "regra 2..."],
  "mitigate_false_positives": ["caso de falso positivo para evitar (máx 150 caracteres)", "caso 2..."],
  "custom_keywords": {
    "CATEGORIA_IA": ["keyword1", "keyword2"]
  }
}
Use apenas categorias exatas como chaves em custom_keywords. Evite repetir palavras óbvias. Não use explicações ou formatações adicionais além do JSON.
"""

def extract_pdf_text(filepath: str, max_pages: int = 15) -> str:
    try:
        reader = PdfReader(filepath)
        text = ""
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Erro ao extrair PDF {filepath}: {e}")
        return ""

def merge_rules(existing: dict, new_rules: dict) -> dict:
    # Garante a estrutura básica
    if not existing:
        existing = {"additional_rules": [], "mitigate_false_positives": [], "custom_keywords": {}}
        
    for key in ["additional_rules", "mitigate_false_positives"]:
        if key not in existing:
            existing[key] = []
        if key in new_rules and isinstance(new_rules[key], list):
            for item in new_rules[key]:
                if item and isinstance(item, str) and item not in existing[key]:
                    existing[key].append(item)
                    
    if "custom_keywords" not in existing:
        existing["custom_keywords"] = {}
        
    if "custom_keywords" in new_rules and isinstance(new_rules["custom_keywords"], dict):
        for cat, kw_list in new_rules["custom_keywords"].items():
            if not isinstance(kw_list, list):
                continue
            cat_upper = cat.upper().strip()
            if cat_upper not in existing["custom_keywords"]:
                existing["custom_keywords"][cat_upper] = []
            for kw in kw_list:
                if kw and isinstance(kw, str):
                    kw_clean = kw.lower().strip()
                    # Evita duplicar na mesma categoria (comparação case-insensitive)
                    if not any(x.lower() == kw_clean for x in existing["custom_keywords"][cat_upper]):
                        existing["custom_keywords"][cat_upper].append(kw)
                        
    return existing

async def process_file(filepath: str) -> dict:
    logger.info(f"Analisando arquivo: {os.path.basename(filepath)}")
    text = ""
    
    if filepath.endswith(".pdf"):
        text = extract_pdf_text(filepath, max_pages=15)
    elif filepath.endswith(".md") or filepath.endswith(".txt"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Erro ao ler arquivo de texto {filepath}: {e}")
            
    if not text.strip():
        logger.warning(f"Nenhum texto extraído de {filepath}")
        return {}
        
    # Limita tamanho do texto para o prompt de IA (cerca de 8000 caracteres)
    text_sample = text[:8000]
    
    prompt = PROMPT_RESEARCH.replace("{text_sample}", text_sample)
    
    # Chama o provedor de IA Cloud
    try:
        response = await ai_service.chat_completion(
            prompt=prompt,
            system_prompt="Você é um assistente acadêmico e perito em linguística computacional.",
            response_format="json_object"
        )
        if response:
            return response
    except Exception as e:
        logger.error(f"Erro ao processar com IA para {filepath}: {e}")
        
    return {}

async def run_research(limit_files: int):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_dir = os.path.join(base_dir, "bases_pdf")
    config_dir = os.path.join(base_dir, "config")
    config_path = os.path.join(config_dir, "custom_rules.json")
    
    if not os.path.exists(pdf_dir):
        logger.error(f"Diretório {pdf_dir} não encontrado!")
        return
        
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
        
    # Varre a pasta bases_pdf
    files = []
    for root, _, filenames in os.walk(pdf_dir):
        for name in filenames:
            if name.endswith((".pdf", ".md", ".txt")) and not name.startswith("~"):
                files.append(os.path.join(root, name))
                
    if not files:
        logger.info("Nenhum arquivo relevante encontrado em bases_pdf.")
        return
        
    # Limita a quantidade de arquivos para não exceder taxas
    files = files[:limit_files]
    logger.info(f"Processando lote de {len(files)} arquivos de bases_pdf...")
    
    # Tenta ler as regras já existentes para enriquecimento incremental
    existing_rules = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing_rules = json.load(f)
            logger.info("Regras customizadas anteriores carregadas para mesclagem.")
        except Exception as e:
            logger.warning(f"Erro ao carregar custom_rules.json existente: {e}")
            
    for filepath in files:
        new_data = await process_file(filepath)
        if new_data:
            existing_rules = merge_rules(existing_rules, new_data)
        await asyncio.sleep(1) # delay preventivo
        
    # Escreve de volta as regras mescladas e validadas
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing_rules, f, indent=2, ensure_ascii=False)
        logger.info(f"Regras customizadas salvas com sucesso em: {config_path}")
    except Exception as e:
        logger.error(f"Erro ao gravar {config_path}: {e}")
        return
        
    # Atualiza a documentação docs/PADRONIZACAO_LINGUISTICA_FORENSE.md
    doc_path = os.path.join(base_dir, "docs", "PADRONIZACAO_LINGUISTICA_FORENSE.md")
    if os.path.exists(doc_path):
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_content = f.read()
                
            header = "## 6. Critérios Enriquecidos via Pesquisa Automatizada"
            
            # Formata a nova seção markdown
            new_section = f"\n\n{header}\n"
            new_section += f"_Última atualização: {os.popen('date /t').read().strip() if sys.platform == 'win32' else '2026-06-02'}_\n\n"
            
            if existing_rules.get("additional_rules"):
                new_section += "### Regras Linguísticas Adicionais:\n"
                for r in existing_rules["additional_rules"][:15]:
                    new_section += f"- {r}\n"
                new_section += "\n"
                
            if existing_rules.get("mitigate_false_positives"):
                new_section += "### Regras de Mitigação de Falsos Positivos:\n"
                for m in existing_rules["mitigate_false_positives"][:15]:
                    new_section += f"- {m}\n"
                new_section += "\n"
                
            if existing_rules.get("custom_keywords"):
                new_section += "### Marcadores Léxico-Semânticos Adicionais:\n"
                for cat, kw_list in existing_rules["custom_keywords"].items():
                    if kw_list:
                        new_section += f"- **{cat}**: {', '.join(kw_list[:20])}\n"
                new_section += "\n"
                
            # Substitui ou anexa
            if header in doc_content:
                parts = doc_content.split(header)
                # Remove a seção antiga
                updated_content = parts[0].strip() + new_section
            else:
                updated_content = doc_content.strip() + new_section
                
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            logger.info("Documentação PADRONIZACAO_LINGUISTICA_FORENSE.md atualizada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao atualizar documentação: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pesquisa de critérios linguísticos a partir de PDFs")
    parser.add_argument("--limit-files", type=int, default=5, help="Quantidade máxima de arquivos a ler por ciclo")
    args = parser.parse_args()
    
    asyncio.run(run_research(args.limit_files))
