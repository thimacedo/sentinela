"""
Worker: CandidateScanner (Motor de Inteligência de Alvos)
Finalidade: Monitorar a pasta de pesquisas, extrair candidatos, calcular relevância e agendar coleta.
Protocolo Diamond: Herda de BaseWorker.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import re
import hashlib
import asyncio
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Dict

# Import do contrato BaseWorker e DB
import sys
sys.path.append(r".")
from workers.core.base_worker import BaseWorker
from core.db import db_client
from core.ai_service import ai_service
from core.intelligence_service import intelligence_service

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

class CandidateScannerWorker(BaseWorker):
    def __init__(self):
        super().__init__("CandidateScanner")
        self.base_path = Path(r".\bases_pesquisas")
        self.processed_table = "pesquisas_processadas"
        self.candidate_table = "candidatos"
        self.queue_table = "fila_coleta"

    async def _run(self, *args, **kwargs):
        if not PdfReader:
            self.logger.error("Biblioteca 'pypdf' não encontrada. Execute 'pip install pypdf'.")
            return

        self.logger.info(f"🔍 Escaneando diretório: {self.base_path}")
        files = list(self.base_path.glob("*.pdf"))
        
        for file_path in files:
            await self._process_file(file_path)

    async def _process_file(self, file_path: Path):
        file_name = file_path.name
        self.logger.info(f"📄 Analisando arquivo: {file_name}")

        # 1. Verificar se já foi processado (Hash)
        file_content = file_path.read_bytes()
        file_hash = hashlib.sha256(file_content).hexdigest()

        existing = db_client.client.table(self.processed_table).select("id").eq("hash_sha256", file_hash).execute()
        if existing.data:
            self.logger.info(f"⏩ Arquivo já processado anteriormente. Pulando.")
            return

        # 2. Extrair Texto do PDF
        try:
            reader = PdfReader(str(file_path))
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            # 3. Detectar Candidatos e Intenções (%)
            candidates = self._extract_candidates(full_text)
            self.logger.info(f"🎯 Detectados {len(candidates)} potenciais alvos.")

            # 4. Salvar Registro da Pesquisa (usando upsert para idempotência)
            res_pesquisa = db_client.client.table(self.processed_table).upsert({
                "arquivo": file_name,
                "hash_sha256": file_hash,
                "candidatos_detectados": len(candidates),
                "status": "PROCESSADO"
            }, on_conflict="arquivo").execute()
            
            pesquisa_id = res_pesquisa.data[0]['id'] if res_pesquisa.data else None

            # 5. Processar cada candidato detectado
            for candidate in candidates:
                await self._handle_candidate(candidate, pesquisa_id, file_name)

        except Exception as e:
            self.logger.error(f"❌ Erro ao processar {file_name}: {e}")
            try:
                db_client.client.table(self.processed_table).upsert({
                    "arquivo": file_name,
                    "hash_sha256": file_hash,
                    "status": "ERRO"
                }, on_conflict="arquivo").execute()
            except Exception as e_log:
                self.logger.error(f"❌ Erro ao registrar status de falha para {file_name}: {e_log}")

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
        unique_candidates = {}
        for r in results:
            if r['nome'] not in unique_candidates or r['intencao'] > unique_candidates[r['nome']]['intencao']:
                unique_candidates[r['nome']] = r
                
        return list(unique_candidates.values())

    def _infer_cargo(self, text: str, name: str) -> str:
        """Tenta inferir o cargo baseado no contexto do PDF."""
        context = text.lower()
        if "presidente" in context: return "Presidente"
        if "governador" in context: return "Governador"
        if "senador" in context: return "Senador"
        return "Candidato"

    async def _discover_official_instagram(self, name: str, cargo: str, file_name: str) -> str:
        """Usa IA para descobrir o handle oficial do Instagram do candidato."""
        prompt = f"""
        Identifique o nome de usuário (username/handle) oficial e correto no Instagram da seguinte figura pública brasileira citada em pesquisas eleitorais:
        Nome: {name}
        Cargo provável: {cargo}
        Contexto do arquivo de pesquisa: {file_name}
        
        Instruções:
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
            self.logger.info(f"🔮 Consultando IA para descobrir Instagram de '{name}'...")
            res = await ai_service.chat_completion(
                prompt=prompt,
                system_prompt="Você é um assistente especializado em mapear perfis oficiais de políticos brasileiros nas redes sociais.",
                response_format="json_object"
            )
            if res and isinstance(res, dict) and "username" in res:
                username = res["username"].lower().strip().replace("@", "")
                if username and res.get("confianca", 0.0) >= 0.6:
                    self.logger.info(f"🎯 IA encontrou o perfil @{username} para '{name}' com confiança {res.get('confianca')}.")
                    return username
        except Exception as e:
            self.logger.error(f"⚠️ Erro ao descobrir Instagram por IA para {name}: {e}")
        
        fallback = self._generate_handle(name)
        self.logger.warning(f"⚠️ Usando fallback gerado automaticamente para '{name}': @{fallback}")
        return fallback

    async def _handle_candidate(self, info: Dict, pesquisa_id: str, file_name: str):
        """Calcula prioridade, descobre a rede oficial, valida com o IntelligenceService e enfileira."""
        nome = info['nome']
        intencao = info['intencao']
        cargo = info['cargo']
        
        # 1. Cálculo de Relevância (Sistema de Recompensas do Motor)
        # Nota: (CargoWeight * 10) + Intencao
        cargo_weight = {"Presidente": 5, "Governador": 4, "Senador": 3, "Candidato": 1}
        nota = (cargo_weight.get(cargo, 1) * 10) + intencao

        # 2. Descobrir a rede social oficial usando IA
        username = await self._discover_official_instagram(nome, cargo, file_name)

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
                    return
                
                # Se o alvo já está ativo e validado, atualizamos as estatísticas e enfileiramos direto
                if status_mon == "Ativo" or ident_val is True:
                    self.logger.info(f"♻️ Alvo @{username} já existe e está ativo no banco. Atualizando estatísticas e enfileirando direto.")
                    try:
                        db_client.client.table(self.candidate_table).update({
                            "intenção_voto": intencao,
                            "nota_relevancia": nota,
                            "ultima_pesquisa_id": pesquisa_id,
                            "atualizado_em": datetime.now(UTC).isoformat()
                        }).eq("username", username).execute()
                    except Exception as e_up:
                        self.logger.warning(f"⚠️ Erro ao atualizar estatísticas da pesquisa para @{username}: {e_up}")

                    # Define a prioridade na fila (1 a 3) baseada na relevância/situação (fila imediata)
                    prioridade = 3
                    if cargo in ["Presidente", "Governador"] or intencao > 15:
                        prioridade = 1
                    elif intencao > 5:
                        prioridade = 2

                    try:
                        today = datetime.now(UTC).date().isoformat()
                        db_client.client.table(self.queue_table).upsert({
                            "candidato_id": username,
                            "prioridade": prioridade,
                            "status": "PENDENTE",
                            "data_agendada": today,
                            "updated_at": datetime.now(UTC).isoformat()
                        }, on_conflict="candidato_id,data_agendada").execute()
                        self.logger.info(f"🚀 Alvo @{username} inserido na fila de coleta imediata hoje.")
                    except Exception as e_queue:
                        self.logger.error(f"❌ Erro ao inserir @{username} na fila de coleta: {e_queue}")
                    
                    return # Fim do processamento deste candidato já conhecido
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

        if is_valid or is_temporary_error:
            # Se for erro temporário, forçamos o cadastro como pendente de validação
            status_mon = "Ativo"
            val_identidade = None # Permite re-validação pelo TargetResearchWorker no futuro
            
            if is_temporary_error:
                self.logger.warning(f"⚠️ Validação de @{username} falhou por erro temporário ({temporary_reason}). Salvando como pendente e prosseguindo para a fila.")
            else:
                status_mon = "Ativo"
                val_identidade = True

            # Insere/Upserta na tabela de candidatos garantindo status Ativo e atualizando metadados da pesquisa
            try:
                db_client.client.table(self.candidate_table).upsert({
                    "username": username,
                    "nome_completo": nome,
                    "cargo": cargo,
                    "intenção_voto": intencao,
                    "nota_relevancia": nota,
                    "ultima_pesquisa_id": pesquisa_id,
                    "status_monitoramento": status_mon,
                    "identidade_validada": val_identidade,
                    "atualizado_em": datetime.now(UTC).isoformat()
                }, on_conflict="username").execute()
            except Exception as e_up:
                self.logger.warning(f"⚠️ Erro ao atualizar estatísticas da pesquisa para @{username}: {e_up}")

            # Define a prioridade na fila (1 a 3) baseada na relevância/situação (fila imediata)
            prioridade = 3
            if cargo in ["Presidente", "Governador"] or intencao > 15:
                prioridade = 1
            elif intencao > 5:
                prioridade = 2

            self.logger.info(f"💎 Target: @{username} | Nota: {nota:.2f} | Prioridade: {prioridade}")

            # 5. Inserir na fila de coleta com agendamento imediato para hoje
            try:
                today = datetime.now(UTC).date().isoformat()
                db_client.client.table(self.queue_table).upsert({
                    "candidato_id": username,
                    "prioridade": prioridade,
                    "status": "PENDENTE",
                    "data_agendada": today,
                    "updated_at": datetime.now(UTC).isoformat()
                }, on_conflict="candidato_id,data_agendada").execute()
                self.logger.info(f"🚀 Alvo @{username} inserido na fila de coleta imediata hoje.")
            except Exception as e_queue:
                self.logger.error(f"❌ Erro ao inserir @{username} na fila de coleta: {e_queue}")
        else:
            reason = research_res.get("motivo_desativacao") if research_res else "Validação falhou ou timeout"
            self.logger.warning(f"🚫 Alvo @{username} desconsiderado da fila imediata. Motivo: {reason}")

    def _generate_handle(self, nome: str) -> str:
        """Gera um handle provisório. Em produção, isso usaria uma busca real."""
        clean = re.sub(r'[^a-zA-Z0-9]', '', nome.lower())
        return clean

if __name__ == "__main__":
    worker = CandidateScannerWorker()
    asyncio.run(worker.execute())
