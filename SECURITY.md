# Política de Segurança da Sentinela

A segurança deste projeto é dividida entre a proteção da infraestrutura de coleta e a privacidade dos dados processados.

## 1. Vulnerabilidades Conhecidas e Mitigações

### Vazamento de Chaves (Frontend)
- **Risco**: O `ui.js` atual contém chaves `anon` do Supabase expostas no cliente.
- **Status**: *Mitigado (Arquitetura Hardened Proxy)*.
- **Revisão**: 2026-08-20

### Coleta de Dados (Instagram Session)
- **Risco**: O scraper depende do cookie `sessionid` de uma conta real. Se o Instagram detectar automação, a conta pode ser banida.
- **Status**: *Mitigado*. O Scrapy está configurado com `DOWNLOAD_DELAY`, `RANDOMIZE_DOWNLOAD_DELAY` e User-Agent rotativo para simular comportamento humano. Limitado a 2 execuções diárias.
- **Revisão**: 2026-08-20
- **Ação**: NUNCA use a conta pessoal principal do projeto para extração. Crie contas "focalizadoras" (burner accounts).

## 2. Tratamento de Dados Sensíveis
- Não armazenamos senhas ou tokens privados de usuários do Instagram, apenas nomes de usuário (`username`) e textos públicos (`text`).
- Os logs de erro (`scheduler_error.log`) não fazem dump de payloads completos para evitar vazamento de PII (Informações Pessoalmente Identificáveis) em caso de acesso indevido ao servidor.

## 3. Boas Práticas Atuais
- `.env` configurado para manter `INSTAGRAM_SESSIONID` e `SUPABASE_KEY` fora do versionamento Git.
- Limpeza de histórico Git realizada para remover secrets cometidos acidentalmente no passado.

## 4. Reportando uma Vulnerabilidade
Se você encontrar uma falha de segurança (ex: bypass nas RLS do Supabase, falha de sanitização no PDF), abra uma *Issue* com a etiqueta `[SEGURANÇA]` ou entre em contato com o administrador do repositório. Não abra PRs públicos para correções de segurança.
