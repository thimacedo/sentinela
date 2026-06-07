"""
validate_trombone.py — Script de validação do contrato real da API Trombone
============================================================================
Execute ANTES de qualquer commit para confirmar que o VoyantServer local
está respondendo corretamente e no formato esperado pelo voyant_service.py.

Uso:
    # 1. Inicie o VoyantServer manualmente:
    #    java -Djava.awt.headless=true -Xmx512m -jar tools/voyant/VoyantServer.jar
    #
    # 2. Aguarde ~10s e então execute:
    #    python scripts/validate_trombone.py

Saída esperada:
    [✅] Ping OK
    [✅] CorpusTerms: 12 termos extraídos
    [✅] Termos hostis detectados: ['golpe', 'lixo']
    [✅] Fast-drop NEUTRO funcional (lote limpo classificado como NEUTRO)
    [✅] Trombone validado — voyant_service.py pode ser integrado ao pipeline.
"""
import asyncio
import json
import sys
import os

# Garante que o módulo core seja localizável ao rodar da raiz do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


HOSTILE_BATCH = [
    "Esse governador é um bandido, ladrão safado que rouba o povo todo dia!",
    "Tiro nessa corja de vagabundos que tomou o poder com fraude e golpe.",
    "Corrupto! Genocida! Vai preso com toda a quadrilha de traidores!",
    "Essa urna fraudada nunca vai me convencer. Ditadura disfarçada de democracia.",
    "Manda esse lixo de político pra cadeia onde ele merece ficar.",
]

NEUTRAL_BATCH = [
    "Parabéns pelo trabalho, governador. Continue com as obras na nossa cidade.",
    "Boa tarde a todos. Que venham mais eventos culturais para a nossa região.",
    "Apoio total à candidatura! Vamos juntos construir um futuro melhor.",
    "Gostei muito do discurso de hoje. Pauta social muito importante.",
    "Obrigado pelas melhorias no transporte público. Fez diferença no meu dia.",
    "Excelente iniciativa de saúde pública. Precisamos de mais ações assim.",
]


async def run_validation():
    from core.voyant_service import voyant_service, HOSTILE_RATIO_THRESHOLD

    errors: list[str] = []
    ok_count = 0

    print("\n" + "=" * 60)
    print("  VALIDAÇÃO DO CONTRATO TROMBONE — SENTINELA DEMOCRÁTICA")
    print("=" * 60 + "\n")

    # --- 1. Ping ---
    print("[1/5] Testando conectividade com o Trombone...")
    is_alive = await voyant_service.ping()
    if is_alive:
        print("  [✅] Ping OK — VoyantServer está respondendo.\n")
        ok_count += 1
    else:
        print("  [❌] Ping FALHOU — VoyantServer não está acessível.")
        print("       Verifique se o .jar foi iniciado na porta 8888.\n")
        errors.append("ping_failed")
        # Sem servidor não tem como continuar
        _print_summary(ok_count, errors)
        await voyant_service.close()
        return

    # --- 2. Extração de termos (lote hostil) ---
    print("[2/5] Testando extração de CorpusTerms (lote hostil)...")
    terms = await voyant_service.extract_corpus_terms(HOSTILE_BATCH)
    if terms is None:
        print("  [❌] extract_corpus_terms retornou None (timeout/erro de rede).")
        errors.append("corpus_terms_failed")
    elif not terms:
        print("  [⚠️] extract_corpus_terms retornou dict vazio — cheque o formato da resposta.")
        print("       Raw payload esperado: { 'corpusTerms': { 'terms': [...] } }")
        errors.append("corpus_terms_empty")
    else:
        print(f"  [✅] CorpusTerms: {len(terms)} termos extraídos.")
        top5 = sorted(terms.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"       Top-5 termos: {[t[0] for t in top5]}\n")
        ok_count += 1

    # --- 3. Detecção de léxico hostil ---
    print("[3/5] Testando cruzamento léxico no lote hostil...")
    triage_hostile = await voyant_service.triage_batch(HOSTILE_BATCH)
    if triage_hostile is None:
        print("  [❌] triage_batch retornou None para lote hostil.")
        errors.append("triage_hostile_none")
    elif triage_hostile["drop"]:
        print(f"  [⚠️] Lote HOSTIL foi marcado como NEUTRO (ratio={triage_hostile['hostile_ratio']:.2%}).")
        print(f"       Considere ajustar VOYANT_HOSTILE_THRESHOLD (atual: {HOSTILE_RATIO_THRESHOLD}).")
        print(f"       Termos hostis encontrados: {triage_hostile['hostile_terms']}")
        errors.append("false_negative_hostile")
    else:
        print(f"  [✅] Vocabulário hostil detectado corretamente.")
        print(f"       Ratio: {triage_hostile['hostile_ratio']:.2%} | Termos: {triage_hostile['hostile_terms']}\n")
        ok_count += 1

    # --- 4. Fast-drop de lote neutro ---
    print("[4/5] Testando fast-drop em lote neutro...")
    triage_neutral = await voyant_service.triage_batch(NEUTRAL_BATCH)
    if triage_neutral is None:
        print("  [❌] triage_batch retornou None para lote neutro.")
        errors.append("triage_neutral_none")
    elif not triage_neutral["drop"]:
        print(f"  [⚠️] Lote NEUTRO não foi descartado (ratio={triage_neutral['hostile_ratio']:.2%}).")
        print(f"       Falso positivo? Termos: {triage_neutral['hostile_terms']}")
        print(f"       Considere revisar o HOSTILE_LEXICON ou aumentar o THRESHOLD.")
        errors.append("false_positive_neutral")
    else:
        print(f"  [✅] Fast-drop NEUTRO funcional.")
        print(f"       Ratio: {triage_neutral['hostile_ratio']:.2%} — lote descartado sem LLM.\n")
        ok_count += 1

    # --- 5. Validação do formato JSON bruto ---
    print("[5/5] Inspecionando formato JSON bruto do Trombone...")
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            corpus_input = "\n\n".join(HOSTILE_BATCH)
            resp = await client.post(
                "http://127.0.0.1:8888/trombone",
                params={"tool": "corpus.CorpusTerms", "format": "json", "limit": 5, "sort": "RELATIVEFREQ"},
                data={"input": corpus_input, "inputFormat": "text"},
            )
            raw = resp.json()
            # Imprime os primeiros 500 chars para inspeção manual
            raw_preview = json.dumps(raw, ensure_ascii=False, indent=2)[:600]
            print("  Raw JSON (preview):\n")
            for line in raw_preview.split("\n"):
                print(f"    {line}")
            print()

            # Valida se as chaves esperadas estão presentes
            if "corpusTerms" in raw and "terms" in raw.get("corpusTerms", {}):
                print("  [✅] Estrutura JSON confirmada: formato principal detectado.")
                ok_count += 1
            elif "terms" in raw:
                print("  [⚠️] Formato alternativo detectado (chave 'terms' na raiz).")
                print("       O parser do voyant_service.py já suporta este formato.")
                ok_count += 1
            else:
                print("  [❌] Estrutura JSON inesperada — revisar _parse_corpus_terms().")
                print(f"       Chaves encontradas: {list(raw.keys())}")
                errors.append("unexpected_json_format")
    except Exception as exc:
        print(f"  [❌] Erro ao inspecionar JSON bruto: {exc}")
        errors.append("raw_json_error")

    await voyant_service.close()
    _print_summary(ok_count, errors)


def _print_summary(ok: int, errors: list):
    print("\n" + "=" * 60)
    print(f"  RESULTADO: {ok}/5 verificações passaram | {len(errors)} erro(s)")
    print("=" * 60)
    if not errors:
        print("\n  [✅] Trombone validado — voyant_service.py pode ser integrado.")
        print("  Próximo passo: adicionar fast-drop em core/ai_service.py\n")
    else:
        print(f"\n  [❌] Falhas: {', '.join(errors)}")
        print("  Corrija os problemas acima antes de integrar ao pipeline.\n")


if __name__ == "__main__":
    asyncio.run(run_validation())
