# Plano de Expansão: Sentinela Cloud & Hybrid (v80.0)

Este documento detalha o design de dois novos módulos modulares e gratuitos para comando remoto e redundância web.

## 🟢 Módulo 1: Sentinela Cloud Command (C2)
**Objetivo:** Monitorar e comandar o sistema (Local ou Web) através de uma interface online.

### Arquitetura (Serverless/Gratuita):
- **Canal de Controle:** Tabela `system_commands` no Supabase.
- **Mecanismo:** O Watchdog local assina o canal **Supabase Realtime**. Quando você insere um comando na web, o sistema local reage instantaneamente.
- **Interface:** Uma página Next.js (hospedada na Vercel Free) que lê as métricas da tabela `worker_metrics` e envia comandos.

### Comandos Suportados:
- `PAUSE`: Interrompe o ciclo de coleta sem matar o processo.
- `RESUME`: Retoma a operação.
- `RESTART`: Watchdog mata o `main_runner` e inicia um novo ciclo.
- `UPDATE`: Executa `git pull` e reinstala dependências.

---

## 🔵 Módulo 2: Web Scraper Redundancy (Cloud Workers)
**Objetivo:** Manter a coleta ativa mesmo com o computador desligado.

### Estratégia de "Custo Zero":
1. **GitHub Actions (Scheduled):**
   - Configurar um Workflow que roda a cada 1 hora.
   - O script utiliza o mesmo `InstagramScraperV2` (Playwright) em modo headless.
   - O GitHub Actions oferece 2.000 minutos/mês gratuitos, suficiente para ciclos curtos de alvos prioritários.

2. **Zyte API (Tier Gratuito):**
   - Integrar o driver do Zyte para realizar requisições via Cloud Proxy quando o IP do GitHub Actions for bloqueado.
   - O sistema prioriza o local, mas se o `Autopilot` detectar que o computador local está offline há mais de 15 min, ele sinaliza para o Cloud Worker assumir.

---

## 🛠️ Design de Integração (Sem Interferência)

### 1. Novo Arquivo: `core/autopilot/cloud_listener.py`
Este componente rodará como uma thread extra no Watchdog.
```python
async def listen_remote_commands():
    # Escuta a tabela 'system_commands' via Supabase Realtime
    # Se receber 'RESTART', chama os hooks do Watchdog L2.
```

### 2. Sincronização Híbrida:
- O **SQLite Local** continua sendo a fonte de verdade para evitar perda de dados.
- O **Cloud Worker** grava diretamente no Supabase. Quando o local volta, ele apenas segue a fila de onde o Cloud parou.

---
**Próximos Passos Sugeridos:**
1. Criar a tabela `system_commands` no Supabase.
2. Implementar o `CloudListener` no Watchdog.
3. Configurar a Action `.github/workflows/web_worker.yml`.
