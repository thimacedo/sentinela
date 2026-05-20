    async def _get_session_cookies(self):
        """Busca cookies do Supabase (system_configs) ou cai para as envs."""
        try:
            res = self.db.table("system_configs").select("value").eq("key", "instagram_session").single().execute()
            if res.data and res.data.get("value"):
                config = res.data["value"]
                self.logger.info(f"[{self.name}] Usando sessão dinâmica do banco de dados.")
                return [
                    {"name": "sessionid", "value": config["session_id"], "domain": ".instagram.com", "path": "/", "httpOnly": True, "secure": True, "sameSite": "Lax"},
                    {"name": "ds_user_id", "value": config["ds_user_id"], "domain": ".instagram.com", "path": "/", "secure": True},
                    {"name": "csrftoken", "value": config["csrf_token"], "domain": ".instagram.com", "path": "/", "secure": True}
                ]
        except Exception as e:
            self.logger.warning(f"[{self.name}] Falha ao buscar sessão no DB: {e}. Tentando .env...")

        if all([self.session_id, self.ds_user_id, self.csrf_token]):
            return [
                {"name": "sessionid", "value": self.session_id, "domain": ".instagram.com", "path": "/", "httpOnly": True, "secure": True, "sameSite": "Lax"},
                {"name": "ds_user_id", "value": self.ds_user_id, "domain": ".instagram.com", "path": "/", "secure": True},
                {"name": "csrftoken", "value": self.csrf_token, "domain": ".instagram.com", "path": "/", "secure": True}
            ]
        return None

    async def _run(self, payload: dict) -> Any:
        """Método principal exigido pelo BaseWorker. Executa a rotina de raspagem."""
        self.logger.info(f"🚀 Iniciando Playwright Stealth para: {self.target_profile}")
        
        cookies = await self._get_session_cookies()
        if not cookies:
            raise ValueError(f"[{self.name}] Nenhuma sessão ativa encontrada (DB ou .env)")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36", 
            viewport={'width': 1920, 'height': 1080}, 
            locale='pt-BR'
        )
        await context.add_cookies(cookies)
        page = await context.new_page()

        # Stealth Patch
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
        """)

        try:
            # 1. Acessa o Perfil
            await page.goto(self.profile_url, wait_until="domcontentloaded", timeout=30000)

            # Aceitar Cookies (Obrigatório no Brasil/Europa, bloqueia o grid se não aceitar)
            try: 
                await page.click('button:has-text("Aceitar"), button:has-text("Accept All"), button:has-text("Allow all cookies")', timeout=3000)
                self.logger.info("🍪 Cookies aceitos.")
                await asyncio.sleep(1)
            except: pass

            # Fecha pop-ups de notificação
            try: 
                await page.click('button:has-text("Agora não"), button:has-text("Not Now")', timeout=2000)
            except: pass

                # ==========================================
                # FAST FAIL: Detecção Imediata de Perfil Inexistente
                # ==========================================
                page_not_found_pt = await page.query_selector('text="Esta página não está disponível"')
                page_not_found_en = await page.query_selector('text="Sorry, this page isn\'t available"')
                
                if page_not_found_pt or page_not_found_en:
                    self.logger.error(f"❌ Perfil @{self.target_profile} NÃO EXISTE no Instagram. Abortando.")
                    # Tira print para evidência e levanta erro específico
                    await page.screenshot(path=f"perfil_inexistente_{self.target_profile}.png")
                    raise Exception(f"Perfil não encontrado: {self.target_profile}")

                # 2. Scroll leve e pega apenas os 3 primeiros posts
                self.logger.info("🖱️ Simulando scroll humano para carregar o grid...")
                await page.evaluate("window.scrollTo(0, 300)") # Scroll mínimo
                await asyncio.sleep(2)

                selector = 'a[href*="/p/"], a[href*="/reel/"]'
                # Espera só o PRIMEIRO post aparecer
                try: 
                    await page.wait_for_selector(selector, timeout=15000, state="visible")
                except:
                    self.logger.error(f"❌ Nenhum post carregou para {self.target_profile}. Tirando print...")
                    await page.screenshot(path=f"erro_grid_{self.target_profile}.png")
                    raise Exception(f"Timeout ao aguardar grid de posts para {self.target_profile}")

                elements = await page.query_selector_all(selector)
                # FORÇA O LIMITE EM 3 POSTS
                elements = elements[:3]
                self.logger.info(f"✅ Encontrados {len(elements)} posts. Iniciando extração profunda de comentários...")

                # 3. Extração via Modal
                detailed_posts = []
                for index, element in enumerate(elements):
                    try:
                        href = await element.get_attribute('href')
                        shortcode = href.strip('/').split('/')[-1]
                        await element.click()
                        await page.wait_for_selector('div[role="dialog"]', timeout=10000)
                        await asyncio.sleep(random.uniform(2.0, 4.0))
                        
                        dialog_element = await page.query_selector('div[role="dialog"]')
                        if dialog_element:
                            # Extrai Data
                            time_element = await dialog_element.query_selector('time')
                            date_str = await time_element.get_attribute('datetime') if time_element else "Unknown"
                            
                            # Extrai Legenda (Caption)
                            caption = ""
                            h1 = await dialog_element.query_selector('h1')
                            if h1: caption = await h1.inner_text()
                            
                            # ==========================================
                            # NOVA ESTRUTURA: SEPARA LEGENDA DE COMENTÁRIOS
                            # ==========================================
                            # Scroll dentro do modal para carregar os comentários
                            await dialog_element.evaluate('el => el.scrollTop = el.scrollHeight')
                            await asyncio.sleep(2)
                            
                            # ==========================================
                            # FILTRO ANTI-UI NÍVEL 3 (Regex Dinâmico)
                            # ==========================================
                            extracted_comments = [] # DECLARAÇÃO EXPLÍCITA AQUI
                            comment_elements = await dialog_element.query_selector_all('ul ul li')
                            
                            # Lista ampliada de ruídos estáticos
                            ui_noise = [
                                "upload de contatos e não usuários", # STRING COMPLETA
                                "curtida", "curtidas", "responder", "explorar", 
                                "notificações", "página inicial", "também da meta", 
                                "painel", "ver tradução", "ver comentários", 
                                "ver menos", "alternar", "ver perfil", "ver todas",
                                "respostas", "perfil", "mensagens", "salvo",
                                "configurações", "sair", "cancelar", "mais",
                                "seguidores", "seguindo", "editar perfil",
                                "upload de contatos", "não usuários"
                            ]
                            
                            months = [
                                "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
                            ]

                            # Regex para padrões dinâmicos do Instagram
                            import re
                            # Padrões: "há 9 horas", "há 5 min", "e outros 2", "1.245 visualizações"
                            dynamic_noise_patterns = [
                                r'^há \d+ (hora|horas|min|mins|dia|dias|semana|semanas|mês|meses|ano|anos)$', 
                                r'^e outros \d+$',
                                r'^\d+(\.\d+)? visualizaç(ão|ões)$',
                                r'^\d+ semanal$',
                                r'^upload de contatos', # Catch para variações
                                r'^\d+ ponto(s)? de coleta'
                            ]
                            emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0]')
                            
                            for idx, c_el in enumerate(comment_elements[:20]):
                                raw_text = await c_el.inner_text()
                                if not raw_text: continue
                                
                                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                                
                                meaningful_lines = []
                                for line in lines:
                                    line_lower = line.lower()
                                    
                                    # Ignora UI Noise Estático
                                    if any(noise in line_lower for noise in ui_noise): continue
                                    # Ignora só números
                                    if line.isdigit(): continue
                                    # Ignora Datas (Meses)
                                    if any(mes in line_lower for mes in months): continue
                                    # Ignora Padrões Dinâmicos (NOVO)
                                    if any(re.match(pattern, line_lower) for pattern in dynamic_noise_patterns): continue
                                    
                                    meaningful_lines.append(line)
                                
                                if not meaningful_lines: continue
                                
                                # Heurística de Comentário vs Username Solto
                                if len(meaningful_lines) == 1:
                                    sole_line = meaningful_lines[0]
                                    if " " not in sole_line and not emoji_pattern.search(sole_line):
                                        continue # É um username solto ou UI curta
                                
                                # Isola Username e Comentário
                                if len(meaningful_lines) >= 2:
                                    author_username = meaningful_lines[0] if len(meaningful_lines[0]) < 30 and " " not in meaningful_lines[0] else "public_user"
                                    comment_text = " ".join(meaningful_lines[1:]) if author_username != "public_user" else " ".join(meaningful_lines)
                                else:
                                    author_username = "public_user"
                                    comment_text = meaningful_lines[0]

                                clean_text = comment_text.replace('\n', ' ').strip()
                                if len(clean_text) < 2: continue

                                hash_input = f"{shortcode}_{idx}_{clean_text[:50]}"
                                comment_id = f"ig_{hashlib.md5(hash_input.encode()).hexdigest()}"
                                category, is_critical = classify_pasa(clean_text)
                                
                                comment_data = {
                                    "id_externo": comment_id,
                                    "candidato_id": self.target_profile,
                                    "post_id": shortcode,
                                    "autor_username": author_username,
                                    "texto_bruto": clean_text,
                                    "data_publicacao": date_str,
                                    "categoria_ia": category,
                                    "is_hate": is_critical,
                                    "confianca_ia": 0.85 if is_critical else 0.60,
                                    "processado_ia": True,
                                    "plataforma": "INSTAGRAM",
                                    "mined": True
                                }
                                extracted_comments.append(comment_data)

                            # 2. Processa a Legenda do Próprio Alvo
                            if caption.strip():
                                category_cap, is_critical_cap = classify_pasa(caption)
                                caption_data = {
                                    "id_externo": f"ig_{shortcode}_caption",
                                    "candidato_id": self.target_profile,
                                    "post_id": shortcode,
                                    "autor_username": self.target_profile, # O alvo é o autor
                                    "texto_bruto": caption.strip(),
                                    "data_publicacao": date_str,
                                    "categoria_ia": category_cap,
                                    "is_hate": is_critical_cap,
                                    "confianca_ia": 0.95 if is_critical_cap else 0.70,
                                    "processado_ia": True,
                                    "plataforma": "INSTAGRAM",
                                    "mined": True
                                }
                                extracted_comments.insert(0, caption_data)

                            self.logger.info(f"🔍 [{index+1}/3] {shortcode} -> Extraídos {len(extracted_comments)} itens (Legenda + Comentários)")
                            
                            # Adiciona à lista geral do Worker
                            detailed_posts.extend(extracted_comments)
                            
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(random.uniform(2.0, 4.0))

                    except Exception as e:
                        self.logger.warning(f"⚠️ Falha ao extrair post do modal: {e}")
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(2)

                # Salva no Supabase (Usando a nova tabela estruturada com Validação de Contrato PASA v17)
                if detailed_posts:
                    valid_comments, n_rejected = self.validate_comments(detailed_posts)

                    self.logger.info(
                        f"✅ Validação PASA v17: {len(valid_comments)} aceitos, "
                        f"{n_rejected} rejeitados (ruído/lixo de UI)"
                    )

                    if valid_comments:
                        self.logger.info(f"💾 Salvando {len(valid_comments)} itens VALIDADOS na tabela 'comentarios'...")
                        success = save_comments(valid_comments)
                        if not success:
                            raise RuntimeError("Falha ao persistir comentários no Supabase")
                        self.logger.info("✅ Sincronização com o banco concluída com sucesso!")
                        
                        # ==========================================
                        # PASA v17: EVENT BUS INTEGRATION
                        # ==========================================
                        try:
                            from core.event_bus import bus
                            # Publica evento para a próxima fase: Classificação via LLM
                            bus.publish("classify_comments", {
                                "post_id": shortcode,
                                "candidato_id": self.target_profile,
                                "count": len(valid_comments),
                                "platform": "INSTAGRAM"
                            })
                            self.logger.info(f"📡 Evento 'classify_comments' publicado para o post {shortcode}")
                        except Exception as eb_err:
                            self.logger.warning(f"⚠️ Falha ao publicar no EventBus: {eb_err}")
                    else:
                        self.logger.warning("📉 Nenhum comentário restou após a validação de contrato (Todos eram ruído).")
                
                return valid_comments if 'valid_comments' in locals() else []

            except Exception as e:
                self.logger.error(f"❌ Erro geral na raspagem: {e}")
                raise
            finally:
                await browser.close()

    def handle_failure(self, exception: Exception):
        self.logger.error(f"🚨 ALERTA DE FALHA NO WORKER {self.name}: {str(exception)}")

# Bloco de teste isolado
async def main():
    # Teste com um perfil real que tenha textos políticos ou agressivos para o PASA pegar
    worker = InstagramWorker("instagram", max_posts=3) 
    dados = await worker.execute()
    for d in dados: 
        print(f"ID: {d.get('id')} | PASA: {d.get('category')} | Texto: {d.get('text')[:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
