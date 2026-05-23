# 🚨 ALVOS DE PRIORIDADE MÁXIMA (TIER 1)
**Data de Emissão**: 02/05/2026
**Status Operacional**: 0 Raspagens (Blank State)

A análise da fila de raspagem revelou 55 perfis de Alto Escopo (Governadores e Presidenciáveis) que não possuem NENHUM comentário coletado. O `worker_sentinela` deve ser forçado a consumir esta lista ignorando o `limit` padrão de vereadores e prefeitos.

## 🏛️ PRESIDENCIÁVEIS (Nacional)
- `@jairmessiasbolsonaro` (Presidente)

## 🏛️ GOVERNADORES (Estadual)
*Esta é a lista de perfis inativos no banco de dados que exigem varredura imediata:*
- `@jeronimorodriguesba` (Governador - BA)
- `@claud castro` (Governador - RJ)
- `@ronaldocaiado` / `@ronaldocaiadooficial` (Governador - GO)
- `@fatimabezerra13` / `@fatimabezerraoficial` (Governadora - RN)
- `@gladsoncameli` (Governador - AC)
- `@paulodantasoficial` (Governador - AL)
- `@talescastroap` (Governador - AP)
- `@carlosbrandaooficial` (Governador - MA)
- `@eduardoriedeloficial` (Governador - MS)
- `@wilsonlimaoficial` (Governador - AM)
- `@elmanofreitasoficial` (Governador - CE)
- `@renatocasagrandeoficial` (Governador - ES)
- `@helderbarbalho` / `@helderbarbalhooficial` (Governador - PA)
- `@joaoazevedooficial` (Governador - PB)
- `@ratinhojunioroficial` (Governador - PR)
- `@claudiocastrooficial` (Governador - RJ)
- `@rafaelfontelesoficial` (Governador - PI)
- `@eduardoleite45` (Governador - RS)
- `@raquellyraoficial` (Governadora - PE)
- `@mauromendesoficial` (Governador - MT)
- `@romeuzemaoficial` (Governador - MG)
- `@flaviodino` (Governador/STF)
- `@joaocampos` (Governador/Prefeito - PE)

*(Nota: Vice-governadores listados na query foram ocultados deste sumário principal para focar no topo da cadeia de comando).*

---

# 📺 ESTRATÉGIA DE EXPANSÃO: YOUTUBE (O Pântano Sombrio)

**Diagnóstico Atual**: O banco de dados possui **0 (ZERO)** perfis cadastrados com a plataforma 'youtube'. A tabela semente `perfis_consolidados_eleicoes_2026.csv` contém apenas a coluna `instagram_url`.

## Plano de Ação para o TargetManager

1. **Atualização do Schema de Semente**: 
   A planilha CSV base precisa ser atualizada para suportar a coluna `youtube_url` ou a tabela do Supabase deve ser injetada via API. O orquestrador não sabe o que é YouTube porque não fomos ensinados a olhar pra lá!

2. **Injeção de Alvos Prioritários (YouTube)**:
   Os perfis com maior volume de ódio em vídeo (lives e cortes) devem ser cadastrados manualmente no banco de dados, marcando a coluna `plataforma` = 'youtube'.
   
   *Lista de Injeção Sugerida (Canais com alta inflamação política)*:
   - `JairBolsonaro` (Youtube)
   - `LulaOficial` (Youtube)
   - `PabloMarcal` (Youtube)
   - `AndréJanones` (Youtube)
   - Canais de mídia hiper-partidária que cobrem governadores locais.

3. **Ativação do `youtube_scraper.py`**:
   O `orquestrador.py` deve ser atualizado para, além do `instagram_headless`, instanciar o `YoutubeScraper` e puxar as URLs dos canais. O YouTube permite a coleta massiva via API oficial ou RSS/Scraping sem bloqueios agressivos de login (ao contrário do Instagram).

## Ordem de Comando
Force o `TargetManager` a rodar uma rotina de `seed_diamond.py` focada apenas nos `candidatos` cujo cargo contenha 'Presidente' ou 'Governador', ignorando a taxa de expiração de 48h.
