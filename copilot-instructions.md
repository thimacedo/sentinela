---
description: "Use when: working on Sentinela Democrática project, maintaining architecture v18.5, following governance rules, communicating in Portuguese (Brazil)."
---

# 🛡️ PERSISTÊNCIA TÉCNICA E GOVERNANÇA - SENTINELA

Este documento serve como a "Memória Técnica" do projeto, garantindo que qualquer agente mantenha a integridade arquitetural v18.5.

## 🏗️ ARQUITETURA MESTRE (v18.5)
1. **Coleta**: `sentinela_scraper/` (Nativo Scrapy) acessa API REST do Instagram.
2. **Nuvem**: `Supabase` armazena `candidatos`, `posts` e `comentarios`.
3. **Cérebro**: `orquestrador.py` coordena o ciclo completo de atualização.
4. **Motores (Folder: /processing)**:
   - `text_processor.py`: Limpeza e Lematização Analítica.
   - `data_miner.py`: Clustering KMeans e Z-Score (Picos de Ódio).
   - `report_generator.py`: PDF FPDF2 com suporte nativo a UTF-8.
5. **IA Analítica**: `core/ai_service.py` balizado pelo `MANUAL_CLASSIFICACAO_ANALITICA_v2.md`.

## 📜 REGRAS INVIOLÁVEIS (GOVERNANÇA)
- **Código Integral**: Proibido omitir partes de código (`//...`). Entregar sempre o arquivo completo.
- **Protocolo PASA**: Toda classificação de ódio deve seguir estritamente o `CRITERIOS_TREINAMENTO.md`.
- **Segurança Admin**: Acesso a `addalvo.html` protegido por TOTP.
- **Linguagem**: Comunicação estritamente em Português (Brasil), técnica e direta.
- **Nomenclatura**: Preservar colunas `owner_username`, `post_shortcode` e `texto_bruto`.

## 📡 CONFIGURAÇÕES DE PERSISTÊNCIA
- **Scope**: `project`
- **Key Facts**: Arquitetura unificada, FPDF2 para encoding, Scrapy nativo.
- **Trigger**: Sempre ler este arquivo ou `ROADMAP.md` ao iniciar nova sessão.