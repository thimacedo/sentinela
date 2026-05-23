# -*- coding: utf-8 -*-
"""
reclassify_csv.py — Reclassifica comentários NEUTRO e salva resultado no CSV.

Fluxo:
  1. Lê comentários_neutros.csv
  2. Para cada linha com categoria_ia == NEUTRO, classifica via Mistral
  3. Salva o CSV atualizado em comentários_reclassificados.csv
  4. Progresso incremental em reclassify_csv_progress.json (retomável)

Uso:
    python scripts/reclassify_csv.py              # processa tudo
    python scripts/reclassify_csv.py --limit 100  # só 100 registros
    python scripts/reclassify_csv.py --reset      # ignora progresso anterior
    python scripts/reclassify_csv.py --dry-run    # classifica sem salvar
"""

import os
import sys
import csv
import json
import asyncio
import logging
import argparse
import time
import io
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── raiz do projeto ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from openai import AsyncOpenAI, APIStatusError

# ── logging (UTF-8 forçado no console Windows) ───────────────────────────────
LOG_FILE = Path(__file__).with_name("reclassify_csv.log")
_file_handler    = logging.FileHandler(LOG_FILE, encoding="utf-8")
_console_handler = logging.StreamHandler(
    io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
)
_fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
_file_handler.setFormatter(_fmt)
_console_handler.setFormatter(_fmt)
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _console_handler])
log = logging.getLogger("reclassify_csv")

# ── arquivos ──────────────────────────────────────────────────────────────────
CSV_INPUT    = ROOT / "comentários_neutros.csv"
CSV_OUTPUT   = ROOT / "comentários_reclassificados.csv"
PROGRESS_FILE = Path(__file__).with_name("reclassify_csv_progress.json")

# ── parâmetros de rate limit ──────────────────────────────────────────────────
CHUNK_SIZE      = 50    # linhas por salvamento incremental do CSV
MAX_CONCURRENT  = 1     # sequencial: evita 429 no plano free da Mistral
RETRY_ATTEMPTS  = 3     # tentativas por comentário antes de desistir
RETRY_DELAY     = 3     # segundos base entre tentativas em caso de erro
DELAY_BETWEEN   = 1.5   # segundos de pausa entre chamadas — elimina 429 (limite ~1 req/s)

# ── prompt de classificação ───────────────────────────────────────────────────
SYSTEM_PROMPT = """\
Você é um analista especializado em monitoramento de discurso político nas redes sociais brasileiras.

Analise o comentário e retorne APENAS JSON válido com esta estrutura exata:
{
  "categoria_ia": "<CATEGORIA>",
  "is_hate": <true|false>,
  "confianca_ia": <0.0 a 1.0>
}

CATEGORIAS (escolha exatamente uma):
- POSITIVO           → apoio, elogio, voto declarado, incentivo ao político
- NEGATIVO           → crítica, oposição, questionamento, ironia, cobrança política
- NEUTRO             → informativo puro, sem opinião clara, spam, emoji isolado, fora de contexto
- XENOFOBIA_REGIONAL → ataque à origem regional de pessoa
- RACISMO_ESTRUTURAL → racismo explícito ou velado
- RACISMO_RELIGIOSO  → intolerância religiosa com viés racial
- VIOLENCIA_GENERO   → ameaça ou humilhação com base em gênero/sexualidade
- MISOGINIA_POLITICA → ataques sexistas a mulheres em contexto político
- MILICIA_DIGITAL    → organização coordenada de ataques, intimidação ou desinformação

Regras obrigatórias:
- is_hate = true SOMENTE para: XENOFOBIA_REGIONAL, RACISMO_*, VIOLENCIA_GENERO, MISOGINIA_POLITICA, MILICIA_DIGITAL
- is_hate = false para POSITIVO, NEGATIVO e NEUTRO
- Interprete gírias, emojis e linguagem informal brasileira pelo seu sentimento real
- Spam e propaganda comercial → NEUTRO
- Responda SOMENTE com o JSON. Sem texto adicional, sem markdown.
"""

# ── cliente Mistral ───────────────────────────────────────────────────────────
def get_client() -> AsyncOpenAI:
    key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not key:
        raise RuntimeError("MISTRAL_API_KEY nao definida no .env")
    return AsyncOpenAI(api_key=key, base_url="https://api.mistral.ai/v1")

# ── progresso ─────────────────────────────────────────────────────────────────
def load_progress() -> dict:
    """Retorna dict {id -> resultado} dos já processados."""
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_progress(done: dict):
    PROGRESS_FILE.write_text(
        json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8"
    )

# ── classificação via Mistral ─────────────────────────────────────────────────
async def classify(client: AsyncOpenAI, row_id: str, text: str) -> Optional[dict]:
    """Chama Mistral com retry. Retorna dict com novos campos ou None."""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = await client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": f'Comentário: "{text}"'},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                timeout=25.0,
            )
            raw = resp.choices[0].message.content
            data = json.loads(raw)

            categoria  = str(data.get("categoria_ia", "NEUTRO")).upper()
            confianca  = float(data.get("confianca_ia", 0.5))
            is_hate    = bool(data.get("is_hate", False))

            # pausa pós-chamada para respeitar rate limit
            await asyncio.sleep(DELAY_BETWEEN)

            return {"categoria_ia": categoria, "confianca_ia": confianca, "is_hate": is_hate}

        except APIStatusError as e:
            log.warning(f"[{row_id}] HTTP {e.status_code} (tentativa {attempt}/{RETRY_ATTEMPTS})")
            if e.status_code in (401, 403):
                log.error("[FATAL] Chave API invalida. Encerrando.")
                raise
            wait = RETRY_DELAY * attempt * (2 if e.status_code == 429 else 1)
            await asyncio.sleep(wait)
        except json.JSONDecodeError:
            log.warning(f"[{row_id}] Resposta nao e JSON valido (tentativa {attempt})")
            await asyncio.sleep(RETRY_DELAY)
        except Exception as e:
            log.warning(f"[{row_id}] Erro inesperado (tentativa {attempt}): {e}")
            await asyncio.sleep(RETRY_DELAY * attempt)

    log.error(f"[{row_id}] Falhou apos {RETRY_ATTEMPTS} tentativas. Mantendo NEUTRO.")
    return None

# ── leitura do CSV ────────────────────────────────────────────────────────────
def read_csv() -> tuple[list[dict], list[str]]:
    """Retorna (linhas, fieldnames)."""
    with open(CSV_INPUT, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    return rows, list(fieldnames)

# ── escrita do CSV ────────────────────────────────────────────────────────────
def write_csv(rows: list[dict], fieldnames: list[str]):
    with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# ── main ──────────────────────────────────────────────────────────────────────
async def main(limit: Optional[int], reset: bool, dry_run: bool):
    log.info("=" * 60)
    log.info(f"reclassify_csv.py | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"Entrada : {CSV_INPUT}")
    log.info(f"Saida   : {CSV_OUTPUT}")
    log.info(f"Limite: {limit or 'todos'} | Reset: {reset} | DryRun: {dry_run}")
    log.info("=" * 60)

    # carrega progresso anterior
    progress = {} if reset else load_progress()
    log.info(f"Registros ja processados (progresso): {len(progress)}")

    # lê CSV
    rows, fieldnames = read_csv()
    log.info(f"Total de linhas no CSV: {len(rows)}")

    # filtra os que precisam de reclassificação
    pendentes = [
        r for r in rows
        if r.get("id") not in progress
        and r.get("texto_bruto", "").strip()
    ]
    if limit:
        pendentes = pendentes[:limit]
    log.info(f"Pendentes para reclassificar: {len(pendentes)}")

    if not pendentes:
        log.info("Nada a processar. CSV ja esta atualizado.")
        # mesmo assim grava o output com o progresso existente aplicado
        _apply_and_save(rows, progress, fieldnames, dry_run)
        return

    client = get_client()

    stats = {}
    erros = 0
    inicio = time.time()

    for i, row in enumerate(pendentes, 1):
        row_id = row.get("id", "")
        texto  = row.get("texto_bruto", "").strip()

        resultado = await classify(client, row_id, texto)

        if resultado:
            progress[row_id] = resultado
            cat = resultado["categoria_ia"]
            stats[cat] = stats.get(cat, 0) + 1
        else:
            erros += 1

        # log de progresso a cada 20
        if i % 20 == 0 or i == len(pendentes):
            elapsed = time.time() - inicio
            rate    = i / elapsed if elapsed > 0 else 0
            pct     = i / len(pendentes) * 100
            log.info(
                f"[{i}/{len(pendentes)}] {pct:.1f}% | "
                f"OK: {i - erros} | Erros: {erros} | {rate:.2f} reg/s"
            )
            # salva progresso incremental
            if not dry_run:
                save_progress(progress)

    # aplica resultados ao CSV e salva
    _apply_and_save(rows, progress, fieldnames, dry_run)

    # relatório final
    elapsed = time.time() - inicio
    log.info("=" * 60)
    log.info(f"CONCLUIDO em {elapsed:.1f}s")
    log.info(f"  Classificados: {len(pendentes) - erros}")
    log.info(f"  Erros:         {erros}")
    log.info("  Distribuicao:")
    for cat, count in sorted(stats.items(), key=lambda x: -x[1]):
        pct = count / max(len(pendentes) - erros, 1) * 100
        log.info(f"    {cat:<30} {count:>5}  ({pct:.1f}%)")
    if not dry_run:
        log.info(f"  CSV salvo em: {CSV_OUTPUT}")
    log.info("=" * 60)


def _apply_and_save(rows: list[dict], progress: dict, fieldnames: list[str], dry_run: bool):
    """Aplica o progresso ao dataset e salva o CSV de saída."""
    for row in rows:
        rid = row.get("id", "")
        if rid in progress:
            r = progress[rid]
            row["categoria_ia"]  = r["categoria_ia"]
            row["confianca_ia"]  = r["confianca_ia"]
            row["is_hate"]       = str(r["is_hate"]).lower()
            row["processado_ia"] = "true"

    if dry_run:
        log.info(f"[DRY-RUN] CSV nao salvo. {len(progress)} registros classificados em memoria.")
        return

    write_csv(rows, fieldnames)
    log.info(f"CSV salvo: {CSV_OUTPUT} ({len(rows)} linhas)")


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",   type=int, default=None)
    parser.add_argument("--reset",   action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(limit=args.limit, reset=args.reset, dry_run=args.dry_run))
