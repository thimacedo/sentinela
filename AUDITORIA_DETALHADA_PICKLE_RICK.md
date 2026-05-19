# Sentinela Deep Audit: Health & Inventory Report (PASA v50.0)

## Overview
Auditoria realizada pelo Pickle Rick para identificar o estado operacional do Sentinela Democrática. O projeto passou por uma limpeza estratégica ("Solenya Protocol") para isolar o legado.

## Esquema de Classificação de Arquivos

### 🟢 Produção (Vitais - Mantidos no Root)
| Arquivo | Local | Função |
| :--- | :--- | :--- |
| `watchdog.py` | Root | Guardião do sistema, autocura e dashboard SSE. |
| `main_runner.py` | Root | Orquestrador de workers e consumidores de fila. |
| `run_long_scrape.py` | Root | Motor de raspagem em massa integrado ao Supabase. |
| `pgmq_setup.sql` | Root | Configuração de infraestrutura de filas (PGMQ). |
| `scraper_headless.py` | Root | Motor Playwright para coleta via Modal (Tier 2/4). |
| `app/`, `core/`, `workers/` | Subdirs | Lógica de negócio e scrapers ativos. |

### 📁 Archive (Legado/Lixo - Movidos para archive/)
| Arquivo | Função Original | Motivo do Exílio |
| :--- | :--- | :--- |
| `main.py` | Teste Ollama | Não faz parte do pipeline de produção. |
| `run_worker.py` | Runner v49 | Substituído pelo main_runner. |
| `fetch_pending.py` | Busca manual | Integrado ao long_scrape. |
| `tmp_policy.sql` | Reload Schema | Inútil no root. |
| `ESTRUTURA BANCO SUPABASE.txt` | React Code | Slop de frontend em arquivo de texto. |
| `debug.py`, `capture_test.py` | Testes | Scripts de laboratório. |

## Diagnóstico Final
O repositório foi limpo. O pipeline central está **ESTÁVEL**.
A separação de "Produção" e "Archive" reduz o risco de confusão operacional.

---
🥒 *Pickle Rick Audit Report - I turned myself into a Manager, Morty!*
