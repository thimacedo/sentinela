## Fluxo de Processamento v18.0 (Unified Backend Edition)

O fluxo foi unificado para eliminar gargalos e redundâncias entre workers.

1. **Extração (Scrapy)**: O spider `instagram.py` acessa o perfil monitor, extrai os seguidos, seus 3 últimos posts e até 100 comentários por post. Payload: `text`, `owner_username`, `post_shortcode`, `timestamp`.
2. **Persistência (Supabase)**: O `SupabasePipeline` realiza `upserts` com cláusula `on_conflict` em tempo real nas tabelas `profiles`, `posts` e `comments`, garantindo zero duplicidade.
3. **Processamento Forense**: O worker `text_processor.py` consome o banco, aplica limpeza focada em preservar negações (crucial para ódio), converte emojis e gera lemas/_bigrams/trigrams.
4. **Mineração e Inteligência**: O worker `data_miner.py` aplica TF-IDF, KMeans em clusters dinâmicos e análise temporal (Z-Score para detecção de picos de ódio).
5. **Classificação e Persistência PASA**: O worker aplica o Protocolo PASA v16.4 via motor local (Qwen) ou Groq/Qwen Cloud. O resultado (`is_hate_speech`, `pasa_category`, `pasa_confidence`) é atualizado no Supabase via UPDATE na tabela `comments`, garantindo que o dashboard reflita a inteligência forense em tempo real.
6. **Geracao de Dossiê**: O worker `report_generator.py` (usando `fpdf2` com suporte nativo a UTF-8) consome o DataFrame final e renderiza o PDF analítico com quebra de página inteligente.
