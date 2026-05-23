# -*- coding: utf-8 -*-
"""Treinamento de modelo de IA para classificação baseada no protocolo PASA.

Este script lê o dataset JSONL gerado por `scripts/extract_pdfs.py` e executa o
fine‑tuning de um modelo de linguagem remoto (ex.: OpenAI, Anthropic, etc.).
A implementação usa a biblioteca `openai` como exemplo; basta substituir o
cliente pelo provedor desejado.

Requisitos:
- Variável de ambiente `OPENAI_API_KEY` (ou chave do provedor que será usado).
- Arquivo `.env` contendo `OPENAI_API_KEY` e `PASA_MODEL_NAME` (nome do modelo base).

O script produz:
- Um arquivo `training_log.txt` com o resumo da execução.
- Atualiza `STATE.md` com o modelo fine‑tuned criado.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Configuração básica de logging
logging.basicConfig(
    filename=Path(__file__).with_name("training_log.txt"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def load_dataset(path: Path) -> list[dict]:
    """Carrega o dataset JSONL preparado para fine‑tuning.

    Cada linha contém um objeto com as chaves `prompt` e `completion`
    conforme exigido pelo protocolo PASA.
    """
    entries = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError as exc:
                logging.error(f"Linha inválida no dataset {path}: {exc}")
    logging.info(f"Dataset carregado com {len(entries)} entradas.")
    return entries


def prepare_openai_finetune_file(entries: list[dict], out_path: Path) -> None:
    """Converte as entradas para o formato esperado pela API de fine‑tuning.

    O modelo OpenAI espera um arquivo JSONL onde cada linha tem as chaves
    `prompt` e `completion`. O script já recebe esse formato, portanto apenas
    grava as linhas novamente para garantir consistência.
    """
    with out_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")
    logging.info(f"Arquivo para fine‑tuning gravado em {out_path}")


def fine_tune_openai_model(train_file_path: Path, base_model: str) -> str:
    """Inicia o fine‑tuning usando a biblioteca `openai`.

    Retorna o ID do job de fine‑tuning para acompanhamento.
    """
    try:
        import openai
    except ImportError as exc:
        raise RuntimeError("Biblioteca `openai` não está instalada.") from exc

    # Carrega a chave da API a partir do .env ou das variáveis de ambiente
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise RuntimeError("Variável de ambiente OPENAI_API_KEY não encontrada.")

    # Upload do arquivo de treinamento
    upload_resp = openai.File.create(file=open(train_file_path, "rb"), purpose="fine-tune")
    file_id = upload_resp.id
    logging.info(f"Arquivo de treinamento enviado: {file_id}")

    # Cria o job de fine‑tuning
    ft_resp = openai.FineTune.create(training_file=file_id, model=base_model)
    job_id = ft_resp.id
    logging.info(f"Job de fine‑tuning iniciado: {job_id}")
    return job_id


def update_state_md(job_id: str, model_name: str) -> None:
    """Atualiza `STATE.md` registrando o modelo fine‑tuned.

    O arquivo `STATE.md` faz parte do protocolo de engenharia do projeto.
    """
    state_path = Path.cwd() / "STATE.md"
    timestamp = datetime.utcnow().isoformat() + "Z"
    entry = f"- Fine‑tuning concluído ({timestamp}): job_id={job_id}, modelo={model_name}\n"
    with state_path.open("a", encoding="utf-8") as f:
        f.write(entry)
    logging.info("STATE.md atualizado com o resultado do treinamento.")

# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------

def main():
    project_root = Path.cwd()
    dataset_path = project_root / "data" / "training" / "pasa_training_dataset.jsonl"
    if not dataset_path.is_file():
        logging.error(f"Dataset não encontrado em {dataset_path}")
        return

    entries = load_dataset(dataset_path)
    if not entries:
        logging.error("Nenhuma entrada válida encontrada no dataset.")
        return

    # Preparar arquivo de fine‑tuning (pode ser o mesmo, mas garantimos consistência)
    fine_tune_file = project_root / "data" / "training" / "pasa_finetune.jsonl"
    prepare_openai_finetune_file(entries, fine_tune_file)

    # Nome do modelo base – pode ser configurado via .env
    base_model = os.getenv("PASA_MODEL_NAME", "gpt-3.5-turbo")
    try:
        job_id = fine_tune_openai_model(fine_tune_file, base_model)
    except Exception as exc:
        logging.exception("Falha ao iniciar o fine‑tuning.")
        return

    # Atualiza o registro de estado
    update_state_md(job_id, base_model)
    print("Fine‑tuning iniciado. Consulte o arquivo training_log.txt para detalhes.")

if __name__ == "__main__":
    main()
