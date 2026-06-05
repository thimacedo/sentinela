"""
Worker: CandidateScanner (Motor de Inteligência de Alvos)
Finalidade: Monitorar a pasta de pesquisas, extrair candidatos, calcular relevância e agendar coleta.
Protocolo Diamond v88.0: Herda de workers.base.worker_base.BaseWorker (moderno).
"""
from __future__ import annotations
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import re
import hashlib
import asyncio
import urllib.parse
from core.constants import DEFAULT_TIMEOUT
import httpx
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Dict, Optional

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.db import db_client
from core.ai_service import ai_service
from core.intelligence_service import intelligence_service
from workers.util.duckduckgo_helper import search_instagram

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


class WkEscaneiaCandidatos(BaseWorker):
    """
    Sub-agente de escaneamento de candidatos.
    Monitora a pasta de pesquisas em PDF, extrai candidatos e os enfileira para coleta.
    """

    # Mapeamento de aliases de handles incorretos conhecidos
    HANDLE_ALIASES: Dict[str, str] = {
        "jairbolsonaro": "jairmessiasbolsonaro",
        # Adicione outros mapeamentos aqui conforme necessário
    }

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.base_path = Path(config.get('base_path', r'.\bases_pesquisas'))
        self.processed_table = 'pesquisas_processadas'
        self.candidate_table = 'candidatos'
        self.queue_table = 'fila_coleta'

    def describe(self) -> str:
        return (
            f"WkEscaneiaCandidatos | "
            f"Monitora PDFs em '{self.base_path}', extrai candidatos e enfileira para coleta."
        )

    async def setup(self) -> None:
        """Verifica dependências e loga inicialização."""
        if not PdfReader:
            self.logger.error(
                "Biblioteca 'pypdf' não encontrada. Execute 'pip install pypdf'."
            )
        self.logger.info(f"[{self.worker_id}] Setup concluído. Base path: {self.base_path}")

    async def teardown(self) -> None:
        """Loga encerramento graceful."""
        self.logger.info(f"[{self.worker_id}] Encerramento concluído.")

    async def run_cycle(self) -> CycleResult:
        """
        Escaneia PDFs novos na pasta base_path.
        - extracted: total de candidatos detectados em todos os PDFs
        - inserted:  total de candidatos enfileirados com sucesso
        - failed:    erros durante o processamento
        Retorna error='no_tasks_available' se nenhum PDF novo for encontrado.
        """
        self.cycle += 1
        result = CycleResult(worker_id=self.worker_id, cycle=self.cycle)

        if not PdfReader:
            result.error = 'pypdf_not_installed'
            result.failed = 1
            return result

        self.logger.info(f"🔍 [{self.worker_id}] Ciclo #{self.cycle} | Escaneando: {self.base_path}")

        # Verifica se o diretório existe
        if not self.base_path.exists():
            self.logger.warning(f"⚠️ Diretório não encontrado: {self.base_path}")
            result.error = 'no_tasks_available'
            return result

        files = list(self.base_path.glob("*.pdf"))
        if not files:
            self.logger.info("📂 Nenhum PDF encontrado na pasta de pesquisas.")
            result.error = 'no_tasks_available'
            return result

        total_extracted = 0
        total_inserted = 0
        total_failed = 0

        for file_path in files:
            # Parada graceful entre arquivos
            if self.shutdown_event and self.shutdown_event.is_set():
                self.logger.info(f"[{self.worker_id}] Shutdown detectado. Interrompendo ciclo.")
                break

            extracted, inserted, failed = await self._process_file(file_path)
            total_extracted += extracted
            total_inserted += inserted
            total_failed += failed

        result.extracted = total_extracted
        result.inserted = total_inserted
        result.failed = total_failed
        result.db_success = total_inserted > 0

        if total_extracted == 0 and total_failed == 0:
            result.error = 'no_tasks_available'

        self.logger.info(
            f"✅ [{self.worker_id}] Ciclo #{self.cycle} concluído | "
            f"detectados={total_extracted} enfileirados={total_inserted} falhas={total_failed}"
        )
        return result

    async def _process_file(self, file_path: Path) -> tuple[int, int, int]:
        """
        Processa um único PDF de pesquisa.
        Retorna (extracted, inserted, failed).
        """
        file_name = file_path.name
        extracted = 0
        inserted = 0
        failed = 0

        self.logger.info(f"📄 Analisando arquivo: {file_name}")

        # 1. Verificar se já foi processado (Hash)
        file_content = file_path.read_bytes()
        file_hash = hashlib.sha256(file_content).hexdigest()

        existing = db_client.client.table(self.processed_table).select("id").eq("hash_sha256", file_hash).execute()
        if existing.data:
            self.logger.info(f"⏩ Arquivo '{file_name}' já processado anteriormente. Pulando.")
            return 0, 0, 0

        # 2. Extrair Texto do PDF
        try:
            reader = PdfReader(str(file_path))
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"

            # 3. Detectar Candidatos e Intenções (%)
            candidates = self._extract_candidates(full_text)
            extracted = len(candidates)
            self.logger.info(f"🎯 Detectados {extracted} potenciais alvos em '{file_name}'.")

            # 4. Salvar Registro da Pesquisa (upsert para idempotência)
            res_pesquisa = db_client.client.table(self.processed_table).upsert({
                "arquivo": file_name,
                "hash_sha256": file_hash,
                "candidatos_detectados": extracted,
                "status": "PROCESSADO"
            }, on_conflict="arquivo").execute()

            pesquisa_id = res_pesquisa.data[0]['id'] if res_pesquisa.data else None

            candidatos_to_upsert = []
            fila_to_upsert = []

            # 5. Processar cada candidato detectado
            for candidate in candidates:
                # Parada graceful entre candidatos
                if self.shutdown_event and self.shutdown_event.is_set():
                    break
                res_handle = await self._handle_candidate(candidate, pesquisa_id, file_name)
                if res_handle:
                    if res_handle.get("candidato"):
                        candidatos_to_upsert.append(res_handle["candidato"])
                    if res_handle.get("fila"):
                        fila_to_upsert.append(res_handle["fila"])
                    if res_handle.get("success"):
                        inserted += 1

            # Executa os Bulk Upserts no banco
            if candidatos_to_upsert:
                try:
                    db_client.client.table(self.candidate_table).upsert(candidatos_to_upsert, on_conflict="username").execute()
                    self.logger.info(f"💾 Bulk Upsert concluído: {len(candidatos_to_upsert)} candidatos salvos/atualizados.")
                except Exception as e_bulk_c:
                    self.logger.error(f"❌ Falha no Bulk Upsert de candidatos: {e_bulk_c}")

            if fila_to_upsert:
                try:
                    db_client.client.table(self.queue_table).upsert(fila_to_upsert, on_conflict="candidato_id,data_agendada").execute()
                    self.logger.info(f"🚀 Bulk Upsert concluído: {len(fila_to_upsert)} agendamentos de coleta criados.")
                except Exception as e_bulk_f:
                    self.logger.error(f"❌ Falha no Bulk Upsert de fila_coleta: {e_bulk_f}")

        except Exception as e:
            self.logger.error(f"❌ Erro ao processar '{file_name}': {e}")
            failed += 1
            try:
                db_client.client.table(self.processed_table).upsert({
                    "arquivo": file_name,
                    "hash_sha256": file_hash,
                    "status": "ERRO"
                }, on_conflict="arquivo").execute()
            except Exception as e_log:
                self.logger.error(f"❌ Erro ao registrar status de falha para '{file_name}': {e_log}")

        return extracted, inserted, failed

    def _extract_candidates(self, text: str) -> List[Dict]:
        """
        Regex robusto para capturar: Nome do Candidato e Intenção de Voto.
        """
        results = []
        # Padrão: Palavra Capitular seguida de outras palavras capitulares e uma porcentagem
        pattern = r"([A-Z][a-zà-ú]+(?:\s+[A-Z][a-zà-ú]+)+)\s*\(?(\d+(?:[,\.]\d+)?)\s*%\)?"
        matches = re.findall(pattern, text)

        blacklist = [
            "Pesquisa", "Instituto", "Margem", "Erro", "Total", "Votos", "Brancos", "Nulos",
            "Sexo", "Masculino", "Feminino", "Branca", "Negra", "Amarela", "Parda", "Indígena",
            "Bom", "Regular", "Ruim", "Péssimo", "Aprova", "Desaprova", "Sim", "Não", "Perfil",
            "Esquerda", "Direita", "Centro", "Indecisos", "Ninguém", "Nenhum", "Espontânea", "Estimulada",
            "Religião", "Católica", "Evangélica", "Outras", "Renda", "Salários", "Escolaridade", "Idade",
            "Anos", "Analfabeto", "Superior", "Fundamental", "Médio", "Entrevistados", "Válidos", "Nível",
            "Instrução", "Região", "Capital", "Interior", "Pública", "Privada", "Renda Familiar", "Salário"
        ]

        for name, value in matches:
            clean_name = name.replace('\n', ' ')
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()

            words = clean_name.split()
            if len(words) < 2 or len(words) > 5:
                continue

            is_noise = any(sw.lower() in clean_name.lower() for sw in blacklist)
            if is_noise:
                continue

            val_float = float(value.replace(",", "."))
            results.append({
                "nome": clean_name,
                "intencao": val_float,
                "cargo": self._infer_cargo(text, clean_name)
            })

        # Remove duplicatas mantendo o maior valor
        unique_candidates: Dict[str, Dict] = {}
        for r in results:
            if r['nome'] not in unique_candidates or r['intencao'] > unique_candidates[r['nome']]['intencao']:
                unique_candidates[r['nome']] = r

        return list(unique_candidates.values())

    def _infer_cargo(self, text: str, name: str) -> str:
        """Tenta inferir o cargo baseado no contexto do PDF."""
        context = text.lower()
        if "presidente" in context:
            return "Presidente"
        if "governador" in context:
            return "Governador"
        if "senador" in context:
            return "Senador"
        return "Candidato"

    async def _search_web_for_instagram(self, name: str, cargo: str) -> List[str]:
        """Search DuckDuckGo for Instagram handles (delega para duckduckgo_helper)."""
        return await search_instagram(name, cargo)

    def _apply_handle_alias(self, username: str) -> str:
        """Normaliza o username aplicando aliases conhecidos.
        Se o username estiver no dicionário de aliases, substitui pelo valor correto.
        """
        return self.HANDLE_ALIASES.get(username.lower(), username)

    async def _discover_official_instagram(self, name: str, cargo: str, file_name: str) -> Optional[str]:
        """Usa IA combinada com busca na web (DuckDuckGo) para obter o handle oficial do Instagram do candidato.
        Aplica alias de curadoria antes de efetuar a validação.
        """
        # 1. Faz busca ativa na web para coletar candidatos de handles reais
        web_handles = await self._search_web_for_instagram(name, cargo)

        prompt = f"""
        Identifique o nome de usuário (username/handle) oficial e correto no Instagram da seguinte figura pública brasileira citada em pesquisas eleitorais:
        Nome: {name}
        Cargo provável: {cargo}
        Contexto do arquivo de pesquisa: {file_name}

        Resultados reais encontrados na busca web pelo perfil: {web_handles}

        Instruções:
        - Analise os resultados de busca e selecione o handle oficial mais adequado e verídico.
        - Priorize perfis que pareçam claramente a conta oficial do político (evitando fã-clubes ou perfis secundários).
        - Responda obrigatoriamente em formato JSON.
        - Se souber o Instagram real e oficial, coloque no campo "username" (sem o caractere '@').
        - Se o político não possuir rede oficial confirmada ou você não souber, deixe o campo "username" vazio ("").
        - Retorne APENAS o JSON no formato:
        {{
            "username": "string_do_username_ou_vazio",
            "confianca": float (de 0.0 a 1.0)
        }}
        """
        try:
            self.logger.info(f"🔮 Consultando IA para selecionar Instagram oficial de '{name}'...")
            res = await ai_service.chat_completion(
                prompt=prompt,
                system_prompt="Você é um assistente especializado em mapear perfis oficiais de políticos brasileiros nas redes sociais com base em buscas web.",
                response_format="json_object"
            )
            if res and isinstance(res, dict) and "username" in res:
                username = self._apply_handle_alias(res["username"]).lower().strip().replace("@", "")
                if username and res.get("confianca", 0.0) >= 0.6:
                    self.logger.info(f"🎯 IA selecionou o perfil @{username} para '{name}' com confiança {res.get('confianca')}.")
                    return username
        except Exception as e:
            self.logger.error(f"⚠️ Erro ao descobrir Instagram por IA para {name}: {e}")

        # Fallback se a IA falhar
        # Se houver resultados da web, prioriza o primeiro em vez do handle bruto gerado
        if web_handles:
            # Aplica alias nos resultados da web antes de usar como fallback
            web_handles = [self._apply_handle_alias(h) for h in web_handles]
            fallback = web_handles[0]
            self.logger.info(f"🔎 Handle oficial encontrado via DuckDuckGo: @{fallback}")
            return fallback

        # Nenhum handle encontrado; retorna None para indicar erro temporário
        self.logger.warning(f"⚠️ Nenhum handle oficial encontrado para '{name}'. Marcando como observação.")
        return None

    async def _handle_candidate(self, info: Dict, pesquisa_id: Optional[str], file_name: str) -> Optional[Dict]:
        """
        Calcula prioridade, descobre a rede oficial, valida com o IntelligenceService.
        Retorna um dicionário com os dados preparados para inserção em lote, ou None se deve pular.
        """
        nome = info['nome']
        intencao = info['intencao']
        cargo = info['cargo']

        # 1. Cálculo de Relevância (Sistema de Recompensas do Motor)
        # Nota: (CargoWeight * 10) + Intencao
        cargo_weight = {"Presidente": 5, "Governador": 4, "Senador": 3, "Candidato": 1}
        nota = (cargo_weight.get(cargo, 1) * 10) + intencao

        # 2. Descobrir a rede social oficial usando IA e DuckDuckGo
        username = await self._discover_official_instagram(nome, cargo, file_name)
        if not username:
            # Nenhum handle encontrado; registra como observação e encerra
            self.logger.warning(f"⚠️ Nenhum handle oficial detectado para '{nome}'. Registrando como observação.")
            return {
                "candidato": {
                    "username": self._generate_handle(nome),  # fallback genérico
                    "nome_completo": nome,
                    "cargo": cargo,
                    "intenção_voto": intencao,
                    "nota_relevancia": nota,
                    "ultima_pesquisa_id": pesquisa_id,
                    "status_monitoramento": "Observação",
                    "identidade_validada": None,
                    "atualizado_em": datetime.now(UTC).isoformat()
                },
                "success": False
            }

        # Garante que o username está normalizado conforme aliases
        username = self._apply_handle_alias(username)

        # --- CURADORIA DE ALVOS EXISTENTES ---
        try:
            existing = db_client.client.table(self.candidate_table)\
                .select("username, identidade_validada, status_monitoramento")\
                .eq("username", username)\
                .execute()

            if existing.data:
                cand_data = existing.data[0]
                status_mon = cand_data.get("status_monitoramento")
                ident_val = cand_data.get("identidade_validada")

                # Se o alvo já foi desativado/rejeitado anteriormente (e não por erro temporário), pulamos
                if status_mon == "DESATIVADO" or ident_val is False:
                    self.logger.info(f"⏩ Alvo @{username} já rejeitado/desativado anteriormente no banco. Pulando.")
                    return None

                # Se o alvo já está ativo e validado, atualizamos as estatísticas e enfileiramos direto
                if status_mon == "Ativo" or ident_val is True:
                    self.logger.info(f"♻️ Alvo @{username} já existe e está ativo no banco. Preparando agendamento direto.")

                    # Define a prioridade na fila (1 a 3) baseada na relevância/situação
                    prioridade = 3
                    if cargo in ["Presidente", "Governador"] or intencao > 15:
                        prioridade = 1
                    elif intencao > 5:
                        prioridade = 2

                    today = datetime.now(UTC).date().isoformat()
                    return {
                        "candidato": {
                            "username": username,
                            "nome_completo": nome,
                            "cargo": cargo,
                            "intenção_voto": intencao,
                            "nota_relevancia": nota,
                            "ultima_pesquisa_id": pesquisa_id,
                            "status_monitoramento": status_mon,
                            "identidade_validada": ident_val,
                            "atualizado_em": datetime.now(UTC).isoformat()
                        },
                        "fila": {
                            "candidato_id": username,
                            "prioridade": prioridade,
                            "status": "PENDENTE",
                            "data_agendada": today,
                            "updated_at": datetime.now(UTC).isoformat()
                        },
                        "success": True
                    }

        except Exception as e_check:
            self.logger.error(f"⚠️ Erro ao consultar existência de @{username} no banco: {e_check}")

        # 3. Validar a identidade do alvo através do IntelligenceService (Apenas para novos ou pendentes)
        self.logger.info(f"🔎 Validando identidade de @{username} para o escopo do projeto...")
        try:
            research_res = await intelligence_service.research_and_validate(username)
        except Exception as e_validate:
            self.logger.error(f"❌ Erro ao validar @{username} via IntelligenceService: {e_validate}")
            research_res = None

        # 4. Decisão de inserção baseada na validação
        is_valid = False
        is_temporary_error = False
        temporary_reason = None

        if research_res:
            is_valid = research_res.get("identidade_validada", False) or research_res.get("status_monitoramento") == "ATIVO"
            motivo_desativacao = research_res.get("motivo_desativacao") or ""

            # Detecta se é erro temporário de sessão/scraping
            if not is_valid:
                for term in ["header_not_found", "exception", "timeout", "unknown_error", "Erro de IA"]:
                    if term.lower() in motivo_desativacao.lower():
                        is_temporary_error = True
                        temporary_reason = term
                        break
        else:
            # Se a chamada falhou completamente (None), tratamos como erro temporário
            is_temporary_error = True
            temporary_reason = "Falha de comunicação/timeout na validação"

        if is_valid:
            # 5. Se o perfil for válido, prepara para inserir como Ativo e enfileirar na fila_coleta
            prioridade = 3
            if cargo in ["Presidente", "Governador"] or intencao > 15:
                prioridade = 1
            elif intencao > 5:
                prioridade = 2

            self.logger.info(f"💎 Target: @{username} | Nota: {nota:.2f} | Prioridade: {prioridade}")
            today = datetime.now(UTC).date().isoformat()

            return {
                "candidato": {
                    "username": username,
                    "nome_completo": nome,
                    "cargo": cargo,
                    "intenção_voto": intencao,
                    "nota_relevancia": nota,
                    "ultima_pesquisa_id": pesquisa_id,
                    "status_monitoramento": "Ativo",
                    "identidade_validada": True,
                    "atualizado_em": datetime.now(UTC).isoformat()
                },
                "fila": {
                    "candidato_id": username,
                    "prioridade": prioridade,
                    "status": "PENDENTE",
                    "data_agendada": today,
                    "updated_at": datetime.now(UTC).isoformat()
                },
                "success": True
            }

        elif is_temporary_error:
            # 6. Se for erro temporário de validação, prepara para salvar em status 'Observação' e NÃO enfileira
            self.logger.warning(f"⚠️ Validação de @{username} falhou por erro temporário ({temporary_reason}). Preparando alvo para observação.")
            return {
                "candidato": {
                    "username": username,
                    "nome_completo": nome,
                    "cargo": cargo,
                    "intenção_voto": intencao,
                    "nota_relevancia": nota,
                    "ultima_pesquisa_id": pesquisa_id,
                    "status_monitoramento": "Observação",
                    "identidade_validada": None,
                    "atualizado_em": datetime.now(UTC).isoformat()
                },
                "success": False
            }
        else:
            reason = research_res.get("motivo_desativacao") if research_res else "Validação falhou ou timeout"
            self.logger.warning(f"🚫 Alvo @{username} desconsiderado da fila imediata. Motivo: {reason}")

        return None

    def _generate_handle(self, nome: str) -> str:
        """Gera um handle provisório a partir do nome."""
        clean = re.sub(r'[^a-zA-Z0-9]', '', nome.lower())
        return clean
