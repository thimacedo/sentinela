import os
import json
import fitz  # pymupdf

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrai o texto completo de um PDF usando PyMuPDF.
    Retorna o texto como string única.
    """
    doc = fitz.open(pdf_path)
    text = []
    for page in doc:
        text.append(page.get_text())
    return "\n".join(text)

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    base_dirs = [
        os.path.join(project_root, "bases_pdf"),
        os.path.join(project_root, "pdf_ironiaesarcasmo")
    ]
    out_dir = os.path.join(project_root, "data", "pdf_texts")
    os.makedirs(out_dir, exist_ok=True)

    training_entries = []
    
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            print(f"Diretório não encontrado: {base_dir}")
            continue
            
        for fname in os.listdir(base_dir):
            if not fname.lower().endswith('.pdf'):
                continue
            pdf_path = os.path.join(base_dir, fname)
            try:
                text = extract_text_from_pdf(pdf_path)
                txt_fname = os.path.splitext(fname)[0] + ".txt"
                txt_path = os.path.join(out_dir, txt_fname)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                # Cria entrada padrão para finetuning (prompt + expected JSON vazio)
                entry = {
                    "prompt": f"Classifique o texto abaixo segundo o protocolo PASA.\n\nTexto: {text[:1000]}...",
                    "completion": "{\"is_hate\": false, \"categoria_ia\": \"NEUTRO\", \"confianca_ia\": 1.0, \"evidencia_lexical\": [], \"analise_pericial\": \"Sem análise\"}"
                }
                training_entries.append(entry)
            except Exception as e:
                print(f"Erro ao processar {fname}: {e}")

    # Salva dataset JSONL para fine‑tuning
    training_dir = os.path.join(project_root, "data", "training")
    os.makedirs(training_dir, exist_ok=True)
    training_path = os.path.join(training_dir, "pasa_training_dataset.jsonl")
    with open(training_path, "w", encoding="utf-8") as f:
        for entry in training_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Extraiu {len(training_entries)} PDFs. Texto salvo em {out_dir}. Dataset salvo em {training_path}")

if __name__ == "__main__":
    main()
